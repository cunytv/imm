#!/usr/bin/env python3

import os
import requests
import sys
from requests.exceptions import ConnectionError
import datetime
import time
import hashlib
import queue
import json
import threading
import validateuserinput
import sendnetworkmail
import filetype
import subprocess
import multiprogressbar

class DropboxUploadSession:
    def __init__(self, path=None, filesdict=None, transfertype=None, checksum=True):
        # Credentials for creating access token
        self.client_id = 'zxka9wntib7t1nn'
        self.client_secret = '3oag5msq6eslynv'
        self.refresh_token = 'BeoDf-HCH5wAAAAAAAAAAZngRU1m49sJglEOh1-5VdRq_Qg0EJy80Mso7YluLNzl'
        self.ACCESS_TOKEN = ''

        # Keeping track of access token's expiration
        self.time_now = ''
        self.time_expire = ''

        # File progress
        self.total_size = 0
        self.bytes_read = 0
        self.total_files = 0
        self.files_read = 0
        self.current_process = ''
        self.email_increment = 0

        # Dropbox logging
        self.DROPBOX_FILES_DICT = []
        self.DROPBOX_TRANSFER_OKAY = True
        self.DROPBOX_TRANSFER_NOT_OKAY_REASON = []

        # DB sharelink        
        self.share_link = ''

        # Multi-threading variables for upload
        self.lock = threading.Lock()
        self.q = queue.Queue()

        # Initializing functions
        if isinstance(path, list):
            for p in path:
                print(p)
                self.get_path_stats(p, transfertype, filesdict, checksum)
        else:
            self.get_path_stats(path, transfertype, filesdict, checksum)

        self.refresh_access_token()

    def get_path_stats(self, path, transfer_type=None, files_dict=None, checksum=True):
        total_size = 0
        total_files = 0
        nondict_file_bytes = 0

        if not path:
            return
        elif os.path.isfile(path):
            total_size = os.path.getsize(path)
            total_files = 1

            if files_dict and all(f["dest"] != path for f in files_dict):
                nondict_file_bytes += total_size

        elif os.path.isdir(path):
            for dirpath, dirs, filenames in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if self.mac_system_metadata(f) or os.path.getsize(fp) == 0:
                        continue

                    if transfer_type == 'delivery' and filetype.is_av(fp) != 'objects':
                        continue

                    try:
                        total_size += os.path.getsize(fp)
                        total_files += 1

                        if files_dict and all(f["dest"] != fp for f in files_dict):
                            nondict_file_bytes += os.path.getsize(fp)
                    except (OSError, FileNotFoundError):
                        pass

        if checksum and not files_dict:
            self.total_size += total_size * 2
        else:
            self.total_size += total_size + nondict_file_bytes

        self.total_files += total_files

        # add bytes to account for sending notifcation
        email_increment = round(self.total_size/100)
        self.email_increment += email_increment
        self.total_size += email_increment

    # Generates access tokens to make API calls
    def refresh_access_token(self):
        url = 'https://api.dropboxapi.com/oauth2/token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }

        retry_attempt = 0
        while retry_attempt < 3:
            try:
                response = requests.post(url, data=data, timeout=15)
                if response.status_code == 200:
                    self.ACCESS_TOKEN = response.json()['access_token']
                    expires_in = response.json()['expires_in']
                    time_now = datetime.datetime.now()
                    self.time_expire = time_now + datetime.timedelta(seconds=expires_in - 1000)
            except requests.exceptions.RequestException as e:
                if retry_attempt == 2:
                    self.DROPBOX_TRANSFER_OKAY = False
                    self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                                                                "timestamp": str(datetime.datetime.now()),
                                                                "error_type": "Error refreshing token",
                                                                "message": str(e)
                                                            })
                    return False
            retry_attempt += 1

    # Checks if access token has expired
    def token_expired(self):
        time_now = datetime.datetime.now()

        if time_now >= self.time_expire:
            return True
        else:
            return False

    def mac_system_metadata(self, file):
        if '.' not in file or file.startswith('.'):
            return True

    # Creates dropbox output paths for each file in a folder
    def list_files(self, directory, split_s, prefix):
        file_paths = []
        dropbox_paths = []

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for filename in files:
                if not self.mac_system_metadata(filename):
                    file_paths.append(os.path.join(root, filename))
                    dropbox_path = os.path.join(prefix + os.path.join(root.rsplit(split_s, 1)[1], filename))
                    dropbox_path = dropbox_path.replace("//", "/")
                    dropbox_paths.append(dropbox_path)
        return file_paths, dropbox_paths

    # Creates checksum as per DB documentation
    def calculate_sha256_checksum(self, file_path, block_size=4 * 1024 * 1024):
        self.current_process = f"Calculating checksum {os.path.basename(file_path)}"

        hash_object = hashlib.sha256()
        bytes_read = 0
        block_hashes = []

        with open(file_path, 'rb') as f:
            while True:
                block = f.read(block_size)
                if not block:
                    break  # End of file

                block_hash = hashlib.sha256(block).digest()
                block_hashes.append(block_hash)
                bytes_read += len(block)
                hash_object.update(block_hash)
                self.bytes_read += len(block)

        final_hash = hash_object.hexdigest()

        return final_hash

    # Creates dropbox folder
    def create_folder(self, path):
        url = "https://api.dropboxapi.com/2/files/create_folder_v2"
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "path": path
        }

        retry_attempt = 0
        while retry_attempt < 3:
            try:
                response = requests.post(url, headers=headers, json=data, timeout=15)
                if response.status_code == 200:
                    break  # Successful chunk upload
            except requests.exceptions.RequestException as e:
                if retry_attempt == 2:
                    self.DROPBOX_TRANSFER_OKAY = False
                    self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                        "timestamp": str(datetime.datetime.now()),
                        "error_type": "Error creating folder",
                        "message": e
                    })
                    return False

            retry_attempt += 1

    # Deletes file from dropbox
    def delete_file(self, path):
        url = "https://api.dropboxapi.com/2/files/delete_v2"
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "path": path
        }

        retry_attempt = 0
        while retry_attempt < 3:
            try:
                response = requests.post(url, headers=headers, json=data, timeout=15)
                if response.status_code == 200:
                    break  # Successful chunk upload
            except requests.exceptions.RequestException as e:
                if retry_attempt == 2:
                    self.DROPBOX_TRANSFER_OKAY = False
                    self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                                                                "timestamp": str(datetime.datetime.now()),
                                                                "error_type": "Error deleting file",
                                                                "message": e
                                                            })
                    return False

            retry_attempt += 1

    def initiate_upload_session(self):
        session_start_url = 'https://content.dropboxapi.com/2/files/upload_session/start'
        dropbox_api_arg = {
            "close": False,
            "session_type": "concurrent"

        }
        dropbox_api_arg_json = json.dumps(dropbox_api_arg)
        headers = {
            'Authorization': 'Bearer ' + self.ACCESS_TOKEN,
            'Dropbox-API-Arg': dropbox_api_arg_json,
            'Content-Type': 'application/octet-stream'
        }

        retry_attempt = 0
        while retry_attempt < 3:
            try:
                response = requests.post(session_start_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    return response.json()['session_id']
            except requests.exceptions.RequestException as e:
                if retry_attempt == 2:
                    self.DROPBOX_TRANSFER_OKAY = False
                    self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                                                                "timestamp": str(datetime.datetime.now()),
                                                                "error_type": "Failed to initiate upload session",
                                                                "message": str(e)
                                                            })
                return

            retry_attempt += 1

    def upload_queue(self, file_path, chunk_size, offset):
        with open(file_path, 'rb') as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                self.q.put((chunk, offset))
                offset += len(chunk)

    def upload_chunks(self, session_id):
        while True:
            with self.lock:
                if not self.q.empty():  # get chunk info from queue
                    item = self.q.get()
                    chunk = item[0]
                    offset = item[1]
                    if self.q.empty():  # if last chunk close upload session
                        close_bool = True
                    else:
                        close_bool = False
                else:  # terminate thread if queue is empty
                    break

            upload_url = 'https://content.dropboxapi.com/2/files/upload_session/append_v2'
            
            dropbox_api_arg = {
                "close": close_bool,
                "cursor": {
                    "offset": offset,
                    "session_id": session_id
                }
            }

            dropbox_api_arg_json = json.dumps(dropbox_api_arg)

            headers = {
                'Authorization': f'Bearer {self.ACCESS_TOKEN}',
                'Dropbox-API-Arg': dropbox_api_arg_json,
                'Content-Type': 'application/octet-stream'
            }
            retry_attempt = 0
            while retry_attempt < 3:
                try:
                    response = requests.post(upload_url, headers=headers, data=chunk, timeout=15)
                    if response.status_code == 200:
                        break  # Successful chunk upload

                    elif response.status_code == 429:  # Too many requests
                        seconds = response.json()["error"]["retry_after"]
                        for i in range(seconds, 0, -1):
                            time.sleep(1)
                        retry_attempt += 1
                        if retry_attempt >= 3:
                            self.DROPBOX_TRANSFER_OKAY = False
                            self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                                "timestamp": str(datetime.datetime.now()),
                                "error_type": "Too many retries (429 Too Many Requests)",
                                "message": f"Retry-after {seconds}s exhausted"
                            })
                            return


                    elif 'Error: 503' in response.text:  # Dropbox service unavailable
                        seconds = 10
                        for i in range(seconds, 0, -1):
                            time.sleep(1)
                        retry_attempt += 1
                        if retry_attempt >= 3:
                            self.DROPBOX_TRANSFER_OKAY = False
                            self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                                "timestamp": str(datetime.datetime.now()),
                                "error_type": "Dropbox service unavailable",
                                "message": "Received 503 multiple times"
                            })
                            return

                except requests.exceptions.RequestException as e:
                    if retry_attempt == 2:
                        self.DROPBOX_TRANSFER_OKAY = False
                        self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                                                                "timestamp": str(datetime.datetime.now()),
                                                                "error_type": "Network error during chunk upload",
                                                                "message": str(e)
                                                            })
                        return
                retry_attempt += 1
            self.bytes_read += len(chunk)

    def complete_upload_session(self, session_id, offset, dropbox_path):
        session_finish_url = 'https://content.dropboxapi.com/2/files/upload_session/finish'
        headers = {
            'Authorization': 'Bearer ' + self.ACCESS_TOKEN,
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': f'{{"cursor": {{"session_id": "{session_id}", "offset": {offset}}}, "commit": {{"path": "{dropbox_path}", "mode": "add", "autorename": true, "mute": false}}}}'
        }

        retry_attempt = 0
        while retry_attempt < 3:
            try:
                response = requests.post(session_finish_url, headers=headers, timeout=30)
                if response.status_code == 200:
                    break  # Successful chunk upload
            except requests.exceptions.RequestException as e:
                if retry_attempt == 2:
                    self.DROPBOX_TRANSFER_OKAY = False
                    self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                                                                "timestamp": str(datetime.datetime.now()),
                                                                "error_type": "Error completing upload session",
                                                                "message": str(e)
                                                            })
                    return

            retry_attempt += 1

        return True

    # Uploads file to dropbox, by calling the appropriate endpoints 
    def upload_file_to_dropbox(self, file_path, dropbox_path, do_fixity, files_dict, max_retries=5, num_threads=8):
        # Create db folder immediately
        db_dir = os.path.dirname(dropbox_path)
        self.create_folder(db_dir)
        
        self.files_read += 1
        for attempt in range(max_retries):
            try:
                # Step 0: Check if ACCESS_TOKEN is still valid
                if self.token_expired():
                    self.refresh_access_token()

                # Step 1: Initiate an upload session
                session_id = self.initiate_upload_session()
                if not session_id:  # if session initialization fails exit method
                    return

                # Step 2: Upload the file in chunks
                offset = 0
                chunk_size = 4194304  # required chunk size for concurrent uploads as per dbx api

                # Create threads
                threads = []
                thread = threading.Thread(target=self.upload_queue, args=(file_path, chunk_size, offset,))
                threads.append(thread)
                thread.start()
                time.sleep(1)

                self.current_process = f"Uploading {os.path.basename(file_path)}"
                for _ in range(num_threads):
                    thread = threading.Thread(target=self.upload_chunks, args=(session_id,))
                    threads.append(thread)
                    thread.start()

                for thread in threads:
                    thread.join()

                # Step 3: Complete the upload session
                complete = self.complete_upload_session(session_id, os.path.getsize(file_path), dropbox_path)
                if not complete:  # if session completion fails exit method
                    return


                # Step 4 (optional): Fixity check
                if do_fixity:
                    # Get checksums
                    cs1, cs2 = None, self.get_file_hash(dropbox_path)
                    if not files_dict:
                        cs1 = self.calculate_sha256_checksum(file_path)
                    else:
                        found = False
                        for f in files_dict:
                            if f['dest'] == file_path:  # Check the destination path
                                cs1 = f['checksum_d']
                                found = True
                                break
                        if not found:
                            cs1 = self.calculate_sha256_checksum(file_path)


                    # Update files dictionary and check fixity
                    if cs1 == cs2:
                        self.DROPBOX_FILES_DICT.append({"orig": file_path,
                                                         "dest": dropbox_path,
                                                         "checksum_o": cs1,
                                                         "checksum_d": cs2,
                                                         "fixity_pass": True
                                                         })
                        return True
                    else:
                        raise ConnectionError(f'File {file_path} transferred but did not pass fixity check')
                else:
                    self.DROPBOX_FILES_DICT.append({"orig": file_path,
                                                         "dest": dropbox_path,
                                                         "checksum_o": None,
                                                         "checksum_d": None,
                                                         "fixity_pass": True
                                                         })
                    return

            except ConnectionError as e:
                if attempt < max_retries - 1:
                    self.delete_file(dropbox_path)
                    self.bytes_read = self.bytes_read - os.path.getsize(file_path)
                else:
                    self.DROPBOX_FILES_DICT.append({"orig": file_path,
                                                         "dest": dropbox_path,
                                                         "checksum_o": cs1,
                                                         "checksum_d": cs2,
                                                         "fixity_pass": False
                                                         })
                    self.DROPBOX_TRANSFER_OKAY = False
                    self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                                                                "timestamp": str(datetime.datetime.now()),
                                                                "error_type": "Max retry uploads reached",
                                                                "message": str(e)
                                                            })
                    return False

    # Get shared link
    def get_shared_link(self, path):
        url = "https://api.dropboxapi.com/2/sharing/list_shared_links"
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "direct_only": True,
            "path": path
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            if response.json()['links']:
                return response.json()['links'][0]['url'], response.json()['links'][0]['id']
            else:
                return self.create_shared_link_with_settings(path)
        else:
            return self.create_shared_link_with_settings(path)

    # Creates share link that anyone can use to access
    def create_shared_link_with_settings(self, path):
        url = 'https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings'
        headers = {
            'Authorization': 'Bearer ' + self.ACCESS_TOKEN,
            'Content-Type': 'application/json',
        }

        settings = {
            'access': "viewer",
            'allow_download': True,
            'audience': "public",
            'requested_visibility': 'public'
        }

        data = {
            'path': path,
            'settings': settings
        }
        response = requests.post(url, headers=headers, json=data)

        try:
            response.raise_for_status()
            return response.json()['url'], response.json()['id']
        except requests.exceptions.HTTPError as e:
            return None

    def file_request(self, db_dest):
        url = "https://api.dropboxapi.com/2/file_requests/create"
        headers = {
            "Authorization": 'Bearer ' + self.ACCESS_TOKEN,
            "Content-Type": "application/json"
        }
        data = {
            "destination": db_dest,
            "open": True,
            "title": db_dest.split("/")[-1],
            "description": db_dest
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            print(response.text)
            url = response.json()['url']
            return url
        except ConnectionError as e:
            return None


    def make_gif_summary(self, directory):
        home_dir = os.path.expanduser('~')
        desktop_path = os.path.join(home_dir, 'Desktop')
        name = directory.rsplit('/', 1)[1] + '.gif'

        gif_output_filepath = os.path.join(desktop_path, name)
        command = f"makegifsummary -o {gif_output_filepath} {directory}"

        devnull_fd = os.open(os.devnull, os.O_WRONLY)

        old_stdout_fd = os.dup(1)
        old_stderr_fd = os.dup(2)

        os.dup2(devnull_fd, 1)
        os.dup2(devnull_fd, 2)
        os.close(devnull_fd)

        try:
            process = subprocess.Popen(command, shell=True)
            process.wait()
        finally:
            os.dup2(old_stdout_fd, 1)
            os.dup2(old_stderr_fd, 2)
            os.close(old_stdout_fd)
            os.close(old_stderr_fd)

        if process.returncode == 0:
            return gif_output_filepath
        else:
            return process.returncode

    def ingestremote_email(self, desktop_path, emails, dropbox_directory, package):
        self.current_process = "Sending notification email to recipients"
        # Bifurcate email type
        cuny_emails = []
        other_emails = []
        if emails:
            for email in emails:
                if "@tv.cuny.edu" in email:
                    cuny_emails.append(email)
                else:
                    other_emails.append(email)

        # Send network email to CUNY recipients
        self.share_link = self.get_shared_link(dropbox_directory)[0]
        window_dub_share_link = self.get_shared_link(f"{dropbox_directory}/{package}_WINDOW.mp4")[0]

        notification = sendnetworkmail.SendNetworkEmail()
        notification.sender("library@tv.cuny.edu")
        notification.recipients(cuny_emails)
        notification.subject(f"Dropbox Upload: {package}")

        html_content = f"""
            <html>
                <body>
                <p>Hello, </p>
                <p></p>
                Click the link below to stream the window dub:
                <br><a href="{window_dub_share_link}">{window_dub_share_link}</a>.
                <p></p>
                Click the link below to access all files, including the window dub:
                <br><a href="{self.share_link}">{self.share_link}</a>.
                <p></p>
                Best
                <br>
                Library Bot
                <p></p>
                </body>
            </html>
            """

        notification.html_content(html_content)
        gif_path = self.make_gif_summary(os.path.join(desktop_path, package))

        with open(os.devnull, "w") as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = devnull
            sys.stderr = devnull
            try:
                notification.embed_img(gif_path)
                notification.send()
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        os.remove(gif_path)

        # Send dropbox notification to non-CUNY recipients
        if other_emails is not None:
            msg = f"{dropbox_directory} has finished uploading."
            self.add_folder_member(other_emails, self.get_shared_folder_id(dropbox_directory),
                                            False, msg)

        self.bytes_read += self.email_increment

    def email(self, emails, filename, link):
        self.current_process = "Sending notification email to recipients"

        notification = sendnetworkmail.SendNetworkEmail()
        notification.sender("library@tv.cuny.edu")
        notification.recipients(emails)
        notification.subject(f"Dropbox Upload: {filename}")

        html_content = f"""
        <html>
          <body>
            <p>Hello, </p>
            <p></p>
            <p>See the link below: </p>
            <p><a href="{link}">{link}</a>.</p>
            <p>Best, </p>
            <p>Library Bot</p>
          </body>
        </html>
        """

        notification.html_content(html_content)

        with open(os.devnull, "w") as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = devnull
            sys.stderr = devnull
            try:
                notification.send()
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr


    # Gets shared folder id if it does not already exist. Necessary for the API call to add member(s) to folder
    def get_file_hash(self, file_path):
        url = "https://api.dropboxapi.com/2/files/get_metadata"
        access_token = self.ACCESS_TOKEN

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "include_deleted": True,
            "include_has_explicit_shared_members": True,
            "include_media_info": True,
            "path": file_path  # Removed curly braces
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()["content_hash"]
        else:
            return None

    # Gets shared folder id if it does not already exist. Necessary for the API call to add member(s) to folder
    def get_shared_folder_id(self, path):
        url = "https://api.dropboxapi.com/2/files/get_metadata"
        access_token = self.ACCESS_TOKEN
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "include_deleted": True,
            "include_has_explicit_shared_members": True,
            "include_media_info": True,
            "path": path  # Removed curly braces
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            if 'sharing_info' in response.json():
                return response.json()["sharing_info"]["parent_shared_folder_id"]
            else:
                return self.create_shared_folder_id(path)
        else:
            return self.create_shared_folder_id(path)

    def create_shared_folder_id(self, path):
        url = 'https://api.dropboxapi.com/2/sharing/share_folder'

        headers = {
            'Authorization': 'Bearer ' + self.ACCESS_TOKEN,
            'Content-Type': 'application/json',
        }
        data = {
            'access_inheritance': 'inherit',
            'acl_update_policy': 'editors',
            'force_async': False,
            'member_policy': 'anyone',
            'path': path,
            'shared_link_policy': 'anyone'
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()["shared_folder_id"]
        else:
            self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                                                                "timestamp": str(datetime.datetime.now()),
                                                                "error_type": f"Error sharing folder: {str(response.status_code)}",
                                                                "message": str(response.text),
                                                            })
            return False

    #Adds member(s) to folder and sends email notification
    def add_folder_member(self, emails, id, quiet_bool, msg):
        url = 'https://api.dropboxapi.com/2/sharing/add_folder_member'
        headers = {
            'Authorization': 'Bearer ' + self.ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }

        members = []
        for email in emails:
            members.append({"access_level": "viewer", "member": {".tag": "email", "email": email}})

        data = {
            "custom_message": msg,
            "members": members,
            "quiet": quiet_bool,
            "shared_folder_id": id
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code != 200:
            self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                                                                "timestamp": str(datetime.datetime.now()),
                                                                "error_type": f"Error sharing folder: {str(response.status_code)}",
                                                                "message": str(response.text)
                                                            })
            return False

    # Adds member(s) to file and sends email notification
    def add_file_member(self, emails, id, quiet_bool):
         url = "https://api.dropboxapi.com/2/sharing/add_file_member"
         headers = {
             "Authorization": "Bearer " + self.ACCESS_TOKEN,
             "Content-Type": "application/json"
         }

         members = []
         for email in emails:
             members.append({".tag": "email","email": email})

         data = {
             "access_level": "viewer",
             "add_message_as_comment": False,
             "custom_message": None,
             "file": id,
             "members": members,
             "quiet": quiet_bool
         }

         response = requests.post(url, headers=headers, json=data)

         # Check the response
         if response.status_code != 200:
             self.DROPBOX_TRANSFER_NOT_OKAY_REASON.append({
                                                                "timestamp": str(datetime.datetime.now()),
                                                                "error_type": f"Error sharing file: {str(response.status_code)}",
                                                                "message": str(response.text),
                                                            })
             return False

    # Handles folder uploads
    def folder (self, folder_path, dropbox_path_prefix, emails):
        # Dropbox root folder where you want to upload files
        # /Users/archivesx/Desktop/Test => /Test
        ROOT_PATH = '/' + folder_path.rsplit('/', 1)[1]
        # Append root to prefix, /Test -> prefix/Test
        if dropbox_path_prefix:
            ROOT_PATH = dropbox_path_prefix + ROOT_PATH

        # Split all files paths in directory at the following string to create dropbox paths
        # /Users/archivesx/Desktop/Test => /Users/archivesx/Desktop
        split_string = folder_path.rsplit('/', 1)[0]
        file_paths, dropbox_file_paths = self.list_files(folder_path, split_string, dropbox_path_prefix)

        # Upload to dropbox
        for f, d in zip(file_paths, dropbox_file_paths):
            self.upload_file_to_dropbox(f, d, True, None)

        if emails:
            cuny_emails = []
            other_emails = []

            for email in emails:
                if "@tv.cuny.edu" in email:
                    cuny_emails.append(email)
                else:
                    other_emails.append(email)

            # Get or create shared link
            self.share_link = self.get_shared_link(ROOT_PATH)[0]

            # Email notification
            if cuny_emails:
                self.email(cuny_emails, folder_path.rsplit('/', 1)[1], self.share_link)

            # Get or create share folder
            id = self.get_shared_folder_id(ROOT_PATH)

            # Dropbox notification
            if other_emails:
                self.add_folder_member(other_emails, id, False, None)

            self.bytes_read += self.email_increment

    # Handles file uploads
    def file (self, file_path, dropbox_path_prefix, emails, link=None):
        # Dropbox file path where you want to upload the file
        # /Users/archivesx/Desktop/test.png => /test.png
        ROOT_PATH = '/' + file_path.rsplit('/', 1)[1]
        # Append root to prefix, /test.png -> prefix/test.png
        if dropbox_path_prefix:
            ROOT_PATH = dropbox_path_prefix + ROOT_PATH

        # Upload file
        self.upload_file_to_dropbox(file_path, ROOT_PATH, True, None)

        if emails:
            cuny_emails = []
            other_emails = []
            for email in emails:
                if "@tv.cuny.edu" in email:
                    cuny_emails.append(email)
                else:
                    other_emails.append(email)

            # Create shared link (do you want to create shared link for the file or for the folder??, test and figure out
            if link == "file":
                self.share_link, id = self.get_shared_link(ROOT_PATH)
            elif link == "folder":
                self.share_link, id = self.get_shared_link(dropbox_path_prefix)

            # Email notification
            if cuny_emails:
                self.email(cuny_emails, file_path.rsplit('/', 1)[1], self.share_link)

            # Dropbox notification
            if other_emails:
                self.add_file_member(other_emails, id, False)

            self.bytes_read += self.email_increment

if __name__ == "__main__":
    input("This script uploads a folder or file(s) to one dropbox directory. Press enter to continue.")

    input_path = input("Input folder or file path(s): ")
    paths = []
    current = ""

    for path in input_path.split():
        # If previous part was continuing
        if current:
            current += " " + path.replace("\\", "")
            if not path.endswith("\\"):
                paths.append(current)
                current = ""
        else:
            if path.endswith("\\"):
                current = path.replace("\\", "")
            else:
                paths.append(path.replace("\\", ""))


    emails = validateuserinput.emails(input("List email(s) delimited by space or press enter to continue: "))
    emails.extend(["library@tv.cuny.edu"])
    #emails.extend(["aida.garrido@tv.cuny.edu"])

    # Custom dropbox parent folder path, otherwise defaults to root dropbox folder in the case of a file
    # and show code workflow in the case of a folder
    dbfolder = None
    if len(paths) > 1:
        dbfolder = input("Specify dropbox folder name: ")
    custom_prefix = input(
        "Specify dropbox directory (/Example/Example) or press enter for default /_AD_HOC_REQUESTS: "
    ).strip() or "/_AD_HOC_REQUESTS"

    if dbfolder:
        custom_prefix = custom_prefix + "/" + dbfolder

    # Create class instance
    session = DropboxUploadSession(paths)

    mpb = multiprogressbar.MultiProgressBar()
    mpb.add_task("Dropbox Upload", session, 'total_size', 'total_files', 'bytes_read', 'files_read',
                     'current_process')
    stop_event = threading.Event()
    t2 = threading.Thread(target=mpb.render, args=(stop_event,))
    t2.start()

    for i, p in enumerate(paths):
        if os.path.isfile(p):
            if  len(paths) == 1:
                t1 = threading.Thread(target=session.file, args=(p, custom_prefix, emails, 'file',))
            elif i == len(paths) - 1:
                t1 = threading.Thread(target=session.file, args=(p, custom_prefix, emails, 'folder',))
            else:
                t1 = threading.Thread(target=session.file, args=(p, custom_prefix, None,))

        else:
            if i == len(paths) - 1:
                t1 = threading.Thread(target=session.folder, args=(p, custom_prefix, emails,))
            else:
                t1 = threading.Thread(target=session.folder, args=(p, custom_prefix, None,))

        t1.start()
        t1.join()

    stop_event.set()
    t2.join()
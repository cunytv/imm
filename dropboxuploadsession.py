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

class DropboxUploadSession:
    def __init__(self, path):
        # Credentials for creating access token
        self.client_id = 'wjmmemxgpuxh911'
        self.client_secret = 'mynnf0nelu4xahk'
        self.refresh_token = 'ST-MxmX3A50AAAAAAAAAAahnN5Tez_DKUHRTFfp9-VhLcf73AzHQlyJQdVxdDrZM'
        self.ACCESS_TOKEN = ''

        # Keeping track of access token's expiration
        self.time_now = ''
        self.time_expire = ''

        # File progress
        self.total_size = self.get_size(path)
        self.bytes_read = 0

        # Dropbox access token and expiration
        self.refresh_access_token()

        # Dropbox errors
        self.DROPBOX_FILES_DICT = {}
        self.DROPBOX_TRANSFER_OKAY = True
        self.DROPBOX_TRANSFER_NOT_OKAY_REASON = ''

        # Share link
        self.share_link = ''

        # Create lock
        self.lock = threading.Lock()

        # Create queue
        self.q = queue.Queue()

    def get_size(self, path):
        total_size = 0
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            for dirpath, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(file_path)
            return total_size

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
                response = requests.post(url, data=data)
                if response.status_code == 200:
                    self.ACCESS_TOKEN = response.json()['access_token']
                    expires_in = response.json()['expires_in']

                    time_now = datetime.datetime.now()
                    self.time_expire = time_now + datetime.timedelta(seconds=expires_in - 1000)
            except requests.exceptions.RequestException as e:
                print(f"Error refreshing access token: {e}")
                if retry_attempt == 2:
                    self.DROPBOX_TRANSFER_OKAY = False
                    self.DROPBOX_TRANSFER_NOT_OKAY_REASON = f"{response.status_code}: {response.text}"
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

    # Creates dropbox output paths for each file in a folder and calculates total size
    def list_files(self, directory, split_s, prefix):
        file_paths = []
        dropbox_paths = []

        # Walk through all files and directories recursively
        for root, directories, files in os.walk(directory):
            # Append file paths to the list
            for filename in files:
                if not self.mac_system_metadata(filename):
                    file_paths.append(os.path.join(root, filename))
                    dropbox_path = os.path.join(prefix + os.path.join(root.rsplit(split_s, 1)[1], filename))
                    dropbox_path = dropbox_path.replace("//", "/")
                    dropbox_paths.append(dropbox_path)
        return file_paths, dropbox_paths

    # Creates checksum
    def calculate_sha256_checksum(self, file_path, block_size=4 * 1024 * 1024):
        # Get the total size of the file
        total_size = os.path.getsize(file_path)
        hash_object = hashlib.sha256()
        bytes_read = 0
        block_hashes = []

        # Open the file for reading in binary mode
        with open(file_path, 'rb') as f:
            while True:
                # Read a block of data
                block = f.read(block_size)
                if not block:
                    break  # End of file

                # Compute the hash of the block and store it
                block_hash = hashlib.sha256(block).digest()
                block_hashes.append(block_hash)

                # Update the total bytes read
                bytes_read += len(block)

                # Update the main hash with the current block hash
                hash_object.update(block_hash)

                # Calculate and display progress
                progress = min(int((bytes_read / total_size) * 100), 100)
                sys.stdout.write("\rChecksum progress: [{:<50}] {:d}% ".format('=' * (progress // 2), progress))
                sys.stdout.flush()

        # Compute the final hash of the concatenated block hashes
        final_hash = hash_object.hexdigest()

        print()  # Move to the next line after progress
        return final_hash

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
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    break  # Successful chunk upload
            except requests.exceptions.RequestException as e:
                print(f"Error completing upload session: {e}")
                if retry_attempt == 2:
                    self.DROPBOX_TRANSFER_OKAY = False
                    self.DROPBOX_TRANSFER_NOT_OKAY_REASON = f"{response.status_code}: {response.text}"
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
                response = requests.post(session_start_url, headers=headers)
                if response.status_code == 200:
                    return response.json()['session_id']
            except requests.exceptions.RequestException as e:
                print(f"Failed to initiate upload session: {e}, {response.text}")
                if retry_attempt == 2:
                    self.DROPBOX_TRANSFER_OKAY = False
                    self.DROPBOX_TRANSFER_NOT_OKAY_REASON = f"{response.status_code}: {response.text}"
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
            # Prepare the Dropbox-API-Arg payload
            dropbox_api_arg = {
                "close": close_bool,
                "cursor": {
                    "offset": offset,
                    "session_id": session_id
                }
            }

            # Convert to JSON string
            dropbox_api_arg_json = json.dumps(dropbox_api_arg)

            headers = {
                'Authorization': f'Bearer {self.ACCESS_TOKEN}',
                'Dropbox-API-Arg': dropbox_api_arg_json,
                'Content-Type': 'application/octet-stream'
            }
            retry_attempt = 0
            while retry_attempt < 3:
                try:
                    response = requests.post(upload_url, headers=headers, data=chunk)
                    if response.status_code == 200:
                        break  # Successful chunk upload

                    elif response.status_code == 429:  # Too many requests
                        seconds = response.json()["error"]["retry_after"]
                        for i in range(seconds, 0, -1):
                            sys.stdout.write(
                                "\rToo many requests. Retrying chunk upload in {:2d} seconds.".format(i))
                            sys.stdout.flush()
                            time.sleep(1)

                    elif 'Error: 503' in response.text:  # Dropbox service unavailable
                        seconds = 10
                        for i in range(seconds, 0, -1):
                            sys.stdout.write(
                                "\rDropbox service availability issue. Retrying chunk upload in {:2d} seconds.".format(i))
                            sys.stdout.flush()
                            time.sleep(1)

                    else:
                        print()
                        print(response.status_code)
                        print(f"Failed to upload chunk: {response.text}")
                        print(f"Offset:{offset}")

                except requests.exceptions.RequestException as e:
                    print(f"Network error during chunk upload: {e}")
                    if retry_attempt == 2:
                        self.DROPBOX_TRANSFER_OKAY = False
                        self.DROPBOX_TRANSFER_NOT_OKAY_REASON = f"Chunk upload retry attempts exceeded; {response.status_code}: {response.text}"
                        return

                retry_attempt += 1

            with self.lock:
                self.bytes_read += len(chunk)
                progress = min(self.bytes_read / self.total_size, 1.0) * 100
                sys.stdout.write(
                    f"\rUpload progress: {progress:.2f}% ({self.bytes_read}/{self.total_size} bytes)")
                sys.stdout.flush()

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
                print(f"Error completing upload session: {e}")
                if retry_attempt == 2:
                    self.DROPBOX_TRANSFER_OKAY = False
                    self.DROPBOX_TRANSFER_NOT_OKAY_REASON = f"Complete upload session retry attempts exceeded; {response.status_code}: {response.text}"
                    return

            retry_attempt += 1

        return True

    # Uploads file to dropbox
    def upload_file_to_dropbox(self, file_path, dropbox_path, do_fixity, files_dict, max_retries=5, num_threads=8):
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
                time.sleep(5)

                for _ in range(num_threads):
                    thread = threading.Thread(target=self.upload_chunks, args=(session_id,))
                    threads.append(thread)
                    thread.start()

                for thread in threads:
                    thread.join()

                # check if upload was okay in the event of upload
                #chunk_okay = self.upload_chunk(chunk, offset, session_id, close_bool)
                #if not chunk_okay:
                #    return  # if chunk upload fails exit method

                # Step 3: Complete the upload session
                complete = self.complete_upload_session(session_id, os.path.getsize(file_path), dropbox_path)
                if not complete:  # if session completion fails exit method
                    return


                # Step 4 (optional): Fixity check
                if do_fixity:
                    # Get checksums
                    cs1, cs2 = None, self.get_file_hash(dropbox_path)
                    if files_dict is None:
                        cs1 = self.calculate_sha256_checksum(file_path)
                    else:
                        for key, value in files_dict.items():
                            if key[0] == file_path:
                                cs1 = value[0]
                                break

                    # Update files dictionary and check fixity
                    if cs1 == cs2:
                        print(f'File {file_path} transferred and passed fixity check')
                        self.DROPBOX_FILES_DICT[(file_path, dropbox_path)] = [cs1, cs2, True]
                        return True
                    else:
                        raise ConnectionError(f'File {file_path} transferred but did not pass fixity check')
                else:
                    self.DROPBOX_FILES_DICT[(file_path, dropbox_path)] = [None, None, None]
                    return

            except ConnectionError as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("Retrying upload.")
                    self.delete_file(dropbox_path)
                    self.bytes_read = self.bytes_read - os.path.getsize(file_path)
                else:
                    print(f"Max retries reached. Operation failed: {e}")
                    self.DROPBOX_FILES_DICT[(file_path, dropbox_path)] = [cs1, cs2, False]
                    self.DROPBOX_TRANSFER_OKAY = False
                    self.DROPBOX_TRANSFER_NOT_OKAY_REASON = f"File upload retry attempts exceeded; {e}"
                    return False

    # Get shared link
    def get_shared_link(self, path):
        # Define the endpoint URL
        url = "https://api.dropboxapi.com/2/sharing/list_shared_links"

        # Define request headers
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        # Define request body data
        data = {
            "direct_only": True,
            "path": path
        }

        # Send the POST request
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
        print("CREATE SHARED LINK")
        print(response)

        # Check Response
        try:
            response.raise_for_status()
            return response.json()['url'], response.json()['id']
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            print(f"Response content: {response.content}")
            return None

    def email(self, emails, filename, link):
        notification = sendnetworkmail.SendNetworkEmail()
        notification.sender("library@tv.cuny.edu")
        notification.recipients(emails)
        notification.subject(f"Dropbox Upload: {filename}")

        # Write text content with HTML formatting
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
        notification.send()

    # Gets shared folder id if it does not already exist. Necessary for the API call to add member(s) to folder
    def get_file_hash(self, file_path):
        # Define the endpoint URL
        url = "https://api.dropboxapi.com/2/files/get_metadata"

        # Replace '<get access token>' with your actual access token
        access_token = self.ACCESS_TOKEN

        # Define the headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Define the data payload
        data = {
            "include_deleted": True,
            "include_has_explicit_shared_members": True,
            "include_media_info": True,
            "path": file_path  # Removed curly braces
        }

        # Make the POST request
        response = requests.post(url, headers=headers, json=data)

        # Check the response
        if response.status_code == 200:
            return response.json()["content_hash"]
        else:
            return None

    # Gets shared folder id if it does not already exist. Necessary for the API call to add member(s) to folder
    def get_shared_folder_id(self, path):
        # Define the endpoint URL
        url = "https://api.dropboxapi.com/2/files/get_metadata"

        # Replace '<get access token>' with your actual access token
        access_token = self.ACCESS_TOKEN

        # Define the headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Define the data payload
        data = {
            "include_deleted": True,
            "include_has_explicit_shared_members": True,
            "include_media_info": True,
            "path": path  # Removed curly braces
        }

        # Make the POST request
        response = requests.post(url, headers=headers, json=data)

        # Check the response
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

        # Check the response
        if response.status_code == 200:
            return response.json()["shared_folder_id"]
        else:
            print("Error sharing folder:", response.text)
            self.DROPBOX_TRANSFER_NOT_OKAY_REASON = f"{response.status_code}: {response.text}"
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

        # Check the response
        if response.status_code == 200:
            print(f"\nFolder succesfully shared with {emails}")
        else:
            print("Error sharing folder:", response.text)
            self.DROPBOX_TRANSFER_NOT_OKAY_REASON = f"{response.status_code}: {response.text}"
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
         if response.status_code == 200:
             print(f"\nFile succesfully shared with {email}")
         else:
             print("Error sharing file:", response.text)
             self.DROPBOX_TRANSFER_NOT_OKAY_REASON = f"{response.status_code}: {response.text}"
             return False

    # Handles folder uploads
    def folder (self, folder_path, emails, dropbox_path_prefix):
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

    # Handles file uploads
    def file (self, file_path, emails, dropbox_path_prefix):
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
            self.share_link, id = self.get_shared_link(ROOT_PATH)

            # Email notification
            if cuny_emails:
                self.email(cuny_emails, file_path.rsplit('/', 1)[1], self.share_link)

            # Dropbox notification
            if other_emails:
                self.add_file_member(other_emails, id, False)


if __name__ == "__main__":

    # (Input, Emails, Output), ...
    input_emails_output_tuple = []

    cont = True
    while cont:
        input_path = validateuserinput.path(input("Input folder or file path: "))
        emails = validateuserinput.emails(input("List email(s) delimited by space or press enter to continue: "))
        emails.extend(["library@tv.cuny.edu"])
        #emails.extend(["aida.garrido@tv.cuny.edu"])

        # Custom dropbox parent folder path, otherwise defaults to root dropbox folder in the case of a file
        # and show code workflow in the case of a folder
        custom_prefix = input('Specify dropbox path (/Example/Example) or press enter for default /_AD_HOC_REQUESTS: ') or "/_AD_HOC_REQUESTS"

        input_emails_output_tuple.append([input_path, emails, custom_prefix])
        cont = (input("\tQueue more dropbox uploads? y/n: ")).lower() == 'y'

    for tuple in input_emails_output_tuple:
        # Create class instance
        session = DropboxUploadSession(tuple[0])

        if os.path.isfile(tuple[0]):
            session.file (tuple[0], tuple[1], tuple[2])

        elif os.path.isdir(input_path):
            session.folder(tuple[0], tuple[1], tuple[2])

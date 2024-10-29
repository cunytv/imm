#!/usr/bin/env python3

import os
import requests
import sys
from requests.exceptions import ConnectionError
import datetime
import time

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

        # Share link
        self.share_link = ''

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

        response = requests.post(url, data=data)
        self.ACCESS_TOKEN = response.json()['access_token']
        expires_in = response.json()['expires_in']

        time_now = datetime.datetime.now()
        self.time_expire = time_now + datetime.timedelta(seconds=expires_in - 1000)

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

    # Uploads file to dropbox
    def upload_file_to_dropbox(self, file_path, dropbox_path, do_fixity, files_dict, max_retries=5):
        for attempt in range(max_retries):
            try:
                #Step 0: Check if ACCESS_TOKEN is still valid
                if self.token_expired():
                    self.refresh_access_token()

                # Step 1: Initiate an upload session
                session_start_url = 'https://content.dropboxapi.com/2/files/upload_session/start'
                headers = {
                    'Authorization': 'Bearer ' + self.ACCESS_TOKEN,
                    'Content-Type': 'application/octet-stream'
                }
                response = requests.post(session_start_url, headers=headers)
                if response.status_code != 200:
                    print("Failed to initiate upload session:", response.text)
                    return

                session_id = response.json()['session_id']
                offset = 0

                # Step 2: Upload the file in chunks
                chunk_size = 4 * 1024 * 1024  # 4MB chunk size
                with open(file_path, 'rb') as file:
                    while True:
                        if self.token_expired():
                            self.refresh_access_token()

                        chunk = file.read(chunk_size)
                        if not chunk:
                            break
                        upload_url = 'https://content.dropboxapi.com/2/files/upload_session/append_v2'
                        headers = {
                            'Authorization': 'Bearer ' + self.ACCESS_TOKEN,
                            'Content-Type': 'application/octet-stream',
                            'Dropbox-API-Arg': '{"cursor": {"session_id": "' + session_id + '", "offset": ' + str(offset) + '}}'
                        }
                        response = requests.post(upload_url, headers=headers, data=chunk)

                        if response.status_code == 429:
                            seconds = response.json()["error"]["retry_after"]
                            for i in range(seconds, 0, -1):
                                sys.stdout.write("\rToo many requests. Retrying chunk upload in {:2d} seconds.".format(i))
                                sys.stdout.flush()
                                time.sleep(1)
                            continue
                        # eventually edit this statement for exponential back off
                        # for some reason dropbox outputs this response as HTML, instead of JSON
                        elif 'Error: 503' in response.text:
                            seconds = 10
                            for i in range(seconds, 0, -1):
                                sys.stdout.write("\rDropbox service availability issue. Retrying chunk upload in {:2d} seconds.".format(i))
                                sys.stdout.flush()
                                time.sleep(1)
                            continue
                        elif response.status_code != 200:
                            print("Failed to upload chunk:", response.text)
                            return

                        offset += len(chunk)
                        self.bytes_read += len(chunk)
                        progress = min(self.bytes_read / self.total_size, 1.0) * 100
                        sys.stdout.write(f"\rUpload progress: {progress:.2f}% ({self.bytes_read}/{self.total_size} bytes)")
                        sys.stdout.flush()

                # Step 3: Complete the upload session
                session_finish_url = 'https://content.dropboxapi.com/2/files/upload_session/finish'
                headers = {
                    'Authorization': 'Bearer ' + self.ACCESS_TOKEN,
                    'Content-Type': 'application/octet-stream',
                    'Dropbox-API-Arg': '{"cursor": {"session_id": "' + session_id + '", "offset": ' + str(offset) + '}, "commit": {"path": "' + dropbox_path + '", "mode": "add", "autorename": true, "mute": false}}'
                }
                response = requests.post(session_finish_url, headers=headers, timeout=30)

                # Create checksum variables and retrieve post-transfer checksum from dropbox API
                cs1 = None
                cs2 = self.get_file_hash(dropbox_path)

                # Create pre-transfer checksum or retrieve existing checksum from files_dict
                if do_fixity and files_dict is None:
                    cs1 = self.calculate_sha256_checksum(file_path)
                elif do_fixity and files_dict:
                    for key, value in files_dict.items():
                        if key[1] == file_path:  # Check the destination path
                            cs1 = value[1]  # The first element is the checksum
                            break

                # Update files dictionary
                if do_fixity:
                    if cs1 == cs2:
                        print(f'File {file} transferred and passed fixity check')
                        self.DROPBOX_FILES_DICT[(file_path, dropbox_path)] = [cs1, cs2, True]
                    else:
                        print(f'File {file} transferred but did not pass fixity check')
                        self.DROPBOX_FILES_DICT[(file_path, dropbox_path)] = [cs1, cs2, False]
                        self.DROPBOX_TRANSFER_OKAY = False
                else:
                    self.DROPBOX_FILES_DICT[(file_path, dropbox_path)] = [cs1, cs2, None]

                if response.status_code != 200:
                    print("Failed to complete upload session:", response.text)
                    self.DROPBOX_TRANSFER_OKAY = False
                    return
                return  # Exit the function after successful upload

            except ConnectionError as e:
                if attempt < max_retries - 1:
                    print(f"ConnectionError: Retry attempt {attempt + 1}")
                else:
                    self.DROPBOX_TRANSFER_OKAY = False
                    raise e

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

        notification.content(html_content)
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
            for email in emails:
                cuny_emails = []
                other_emails = []

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

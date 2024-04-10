#!/usr/bin/env python3

import os
import requests
import sys
from requests.exceptions import ConnectionError
import datetime

import validateuserinput

# Credentials for creating access token
client_id = 'wjmmemxgpuxh911'
client_secret = 'mynnf0nelu4xahk'
refresh_token = 'ST-MxmX3A50AAAAAAAAAAahnN5Tez_DKUHRTFfp9-VhLcf73AzHQlyJQdVxdDrZM'
ACCESS_TOKEN = ''

# Keeping track of access token's expiration
time_now = ''
time_expire = ''

# File progress
total_size = 0
bytes_read = 0

# Generates access tokens to make API calls
def refresh_access_token():
    global ACCESS_TOKEN, time_expire  # Declare global variables

    url = 'https://api.dropboxapi.com/oauth2/token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }

    response = requests.post(url, data=data)
    ACCESS_TOKEN = response.json()['access_token']
    expires_in = response.json()['expires_in']

    time_now = datetime.datetime.now()
    time_expire = time_now + datetime.timedelta(seconds=expires_in - 350)

# Checks if access token has expired
def token_expired():
    time_now = datetime.datetime.now()

    if time_now >= time_expire:
        return True
    else:
        return False


# Creates dropbox output paths for each file in a folder and calculates total size
def list_files(directory, split_s, prefix):
    global total_size
    file_paths = []
    dropbox_paths = []

    # Walk through all files and directories recursively
    for root, directories, files in os.walk(directory):
        # Append file paths to the list
        for filename in files:
            if not filename.startswith('.') and '.' in filename:
                file_paths.append(os.path.join(root, filename))
                dropbox_path = os.path.join(prefix + os.path.join(root.rsplit(split_s, 1)[1], filename))
                dropbox_path = dropbox_path.replace("//", "/")
                dropbox_paths.append(dropbox_path)
                total_size += os.path.getsize(os.path.join(root, filename))
    return file_paths, dropbox_paths


# Uploads file to dropbox
def upload_file_to_dropbox(file_path, dropbox_path, max_retries=5):
    global bytes_read, total_size

    # Dropbox access token and expiration
    refresh_access_token()

    for attempt in range(max_retries):
        try:
            #Step 0: Check if ACCESS_TOKEN is still valid
            if token_expired():
                refresh_access_token()

            # Step 1: Initiate an upload session
            session_start_url = 'https://content.dropboxapi.com/2/files/upload_session/start'
            headers = {
                'Authorization': 'Bearer ' + ACCESS_TOKEN,
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
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    upload_url = 'https://content.dropboxapi.com/2/files/upload_session/append_v2'
                    headers = {
                        'Authorization': 'Bearer ' + ACCESS_TOKEN,
                        'Content-Type': 'application/octet-stream',
                        'Dropbox-API-Arg': '{"cursor": {"session_id": "' + session_id + '", "offset": ' + str(offset) + '}}'
                    }
                    response = requests.post(upload_url, headers=headers, data=chunk)
                    if response.status_code != 200:
                        print("Failed to upload chunk:", response.text)
                        return
                    offset += len(chunk)
                    bytes_read += len(chunk)
                    progress = min(bytes_read / total_size, 1.0) * 100
                    sys.stdout.write(f"\rUpload progress: {progress:.2f}% ({bytes_read}/{total_size} bytes)")
                    sys.stdout.flush()

            # Step 3: Complete the upload session
            session_finish_url = 'https://content.dropboxapi.com/2/files/upload_session/finish'
            headers = {
                'Authorization': 'Bearer ' + ACCESS_TOKEN,
                'Content-Type': 'application/octet-stream',
                'Dropbox-API-Arg': '{"cursor": {"session_id": "' + session_id + '", "offset": ' + str(offset) + '}, "commit": {"path": "' + dropbox_path + '", "mode": "add", "autorename": true, "mute": false}}'
            }
            response = requests.post(session_finish_url, headers=headers, timeout=30)
            if response.status_code != 200:
                print("Failed to complete upload session:", response.text)
                return
            return  # Exit the function after successful upload

        except ConnectionError as e:
            if attempt < max_retries - 1:
                print(f"ConnectionError: Retry attempt {attempt + 1}")
            else:
                raise e

# Get shared link
def get_shared_link(path):
    # Define the endpoint URL
    url = "https://api.dropboxapi.com/2/sharing/list_shared_links"

    # Define request headers
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Define request body data
    data = {
        "path": path
    }

    # Send the POST request
    response = requests.post(url, headers=headers, json=data)

    # Check if request was successful
    if response.json()['links']:
        return response.json()['links'][0]['url'], response.json()['links'][0]['id']
    else:
        return create_shared_link_with_settings(path)

# Creates share link that anyone can use to access
def create_shared_link_with_settings(path):
    url = 'https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings'
    headers = {
        'Authorization': 'Bearer ' + ACCESS_TOKEN,
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

    # Check Response
    try:
        response.raise_for_status()
        return response.json()['url'], response.json()['id']
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        print(f"Response content: {response.content}")
        return None

# Gets shared folder id if it does not already exist. Necessary for the API call to add member(s) to folder
def get_shared_folder_id(path):
    global ACCESS_TOKEN
    # Define the endpoint URL
    url = "https://api.dropboxapi.com/2/files/get_metadata"

    # Replace '<get access token>' with your actual access token
    access_token = ACCESS_TOKEN

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
            print(response.json())
            return response.json()["sharing_info"]["parent_shared_folder_id"]
        else:
            return create_shared_folder_id(path)
    else:
        print("Error sharing folder:", response.text)


def create_shared_folder_id(path):
    url = 'https://api.dropboxapi.com/2/sharing/share_folder'

    headers = {
        'Authorization': 'Bearer ' + ACCESS_TOKEN,
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
def add_folder_member(message, emails, id):
    url = 'https://api.dropboxapi.com/2/sharing/add_folder_member'
    headers = {
        'Authorization': 'Bearer ' + ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }

    members = []
    for email in emails:
        members.append({"access_level": "viewer", "member": {".tag": "email", "email": email}})

    data = {
        "custom_message": message,
        "members": members,
        "quiet": False,
        "shared_folder_id": id
    }

    response = requests.post(url, headers=headers, json=data)

    # Check the response
    if response.status_code == 200:
        print(f"\nFolder succesfully shared with {emails}")
    else:
        print("Error sharing folder:", response.text)

# Adds member(s) to file and sends email notification
def add_file_member(message, emails, id):
     url = "https://api.dropboxapi.com/2/sharing/add_file_member"
     headers = {
         "Authorization": "Bearer " + ACCESS_TOKEN,
         "Content-Type": "application/json"
     }

     members = []
     for email in emails:
         members.append({"access_level": "viewer", "member": {".tag": "email","email": email}})

     data = {
         "access_level": "viewer",
         "add_message_as_comment": False,
         "custom_message": message,
         "file": id,
         "members": members,
         "quiet": False
     }

     response = requests.post(url, headers=headers, json=data)

     # Check the response
     if response.status_code == 200:
         print(f"\nFile succesfully shared with {email}")
     else:
         print("Error sharing file:", response.text)

# Handles folder uploads
def folder (folder_path, emails, dropbox_path_prefix):
    # Dropbox root folder where you want to upload files
    # /Users/archivesx/Desktop/Test => /Test
    ROOT_PATH = '/' + folder_path.rsplit('/', 1)[1]
    # Append root to prefix, /Test -> prefix/Test
    if dropbox_path_prefix:
        ROOT_PATH = dropbox_path_prefix + ROOT_PATH

    # Split all files paths in directory at the following string to create dropbox paths
    # /Users/archivesx/Desktop/Test => /Users/archivesx/Desktop
    split_string = folder_path.rsplit('/', 1)[0]
    file_paths, dropbox_file_paths = list_files(folder_path, split_string, dropbox_path_prefix)

    # Upload to dropbox
    for f, d in zip(file_paths, dropbox_file_paths):
        upload_file_to_dropbox(f, d)

    if emails:
        # Get or create shared link
        link = get_shared_link(ROOT_PATH)[0]

        # Get or create share folder
        id = get_shared_folder_id(ROOT_PATH)

        # Share with colleagues
        message = f"This folder has been shared with: {emails}. If this email is forwarded, this folder can be accessed using the following link: {link}"
        add_folder_member(message, emails, id)

# Handles file uploads
def file (file_path, emails, dropbox_path_prefix):
    global total_size

    # Dropbox file path where you want to upload the file
    # /Users/archivesx/Desktop/test.png => /test.png
    ROOT_PATH = '/' + file_path.rsplit('/', 1)[1]
    # Append root to prefix, /test.png -> prefix/test.png
    if dropbox_path_prefix:
        ROOT_PATH = dropbox_path_prefix + ROOT_PATH

    # Get size of file to keep track of upload progress
    total_size = os.path.getsize(file_path)

    # Upload file
    upload_file_to_dropbox(file_path, ROOT_PATH)

    if emails:
        # Create shared link (do you want to create shared link for the file or for the folder??, test and figure out
        link, id = get_shared_link(ROOT_PATH)

        # Share with colleagues
        message = f"If this email is forwarded, this file can be accessed using the following link: {link}"
        add_file_member(message, emails, id)


if __name__ == "__main__":
    # (Input, Emails, Output), ...
    input_emails_output_tuple = []

    cont = True
    while cont:
        input_path = validateuserinput.path(input("Input folder or file path: "))
        emails = validateuserinput.emails(input("List email(s) delimited by space or press enter to continue: "))

        # Custom dropbox parent folder path, otherwise defaults to root dropbox folder in the case of a file
        # and show code workflow in the case of a folder
        #custom_prefix = "/Apps/Automate Camera Card Upload"
        custom_prefix = input('Specify dropbox path (/Example/Example) or press enter to continue: ')
        input_emails_output_tuple.append([input_path, emails, custom_prefix])
        cont = (input("\tQueue more dropbox uploads? y/n: ")).lower() == 'y'

    for tuple in input_emails_output_tuple:
        if os.path.isfile(tuple[0]):
            file (tuple[0], tuple[1], tuple[2])

        elif os.path.isdir(input_path):
            folder(tuple[0], tuple[1], tuple[2])

#!/usr/bin/env python3

import os
import requests
import datetime
import json

class DropboxTraverseDownload:
    image_extensions = [
        "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp", "svg", "heif", "heic", "ico",
        "raw", "exr", "apng", "pdf", "psd", "ai", "eps", "indd", "heif", "jpe", "jfif", "wdp", "dng",
        "fpx", "pcx", "pgm", "ppm", "tga", "xcf", "cur", "webm", "3fr", "arw", "bay", "cr2", "crw", "dcr",
        "mef", "mrw", "nef", "orf", "pef", "raf", "sr2", "srw", "tiff", "xpm", "yuv", "kdc", "sct", "pict",
        "bpg", "jxr", "wdp", "xif", "fif"
    ]

    def __init__(self):
        # Credentials for creating access token
        self.client_id = 'wjmmemxgpuxh911'
        self.client_secret = 'mynnf0nelu4xahk'
        self.refresh_token = 'ST-MxmX3A50AAAAAAAAAAahnN5Tez_DKUHRTFfp9-VhLcf73AzHQlyJQdVxdDrZM'
        self.ACCESS_TOKEN = ''

        # Keeping track of access token's expiration
        self.time_now = ''
        self.time_expire = ''

        # Dropbox access token and expiration
        self.refresh_access_token()

        # Array of image dropbox file paths
        self.image_paths = []

        # Array of folder dropbox file paths
        self.folder_paths = []

        # Numbers of files
        self.counter = 0


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

    def listcontents(self, path, txtfile):

        # Check if token is expired
        if self.token_expired():
            self.refresh_access_token()

        # Replace this with your Dropbox API access token
        access_token = self.ACCESS_TOKEN

        # Define the Dropbox API endpoint
        url = "https://api.dropboxapi.com/2/files/list_folder"

        # Set the headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Define the request body (data to send in the POST request)
        data = {
            "include_deleted": False,
            "include_has_explicit_shared_members": False,
            "include_media_info": False,
            "include_mounted_folders": True,
            "include_non_downloadable_files": True,
            "path": path,  # Replace with the folder path you want to list
            "recursive": False
        }

        # Send the POST request to the Dropbox API
        response = requests.post(url, headers=headers, data=json.dumps(data))

        # Check if the request was successful
        if response.status_code == 200:
            # Parse and print the response JSON
            folder_info = response.json()
            #print("Folder contents:")
            for entry in folder_info.get('entries', []):
                if entry['.tag'] == 'folder':
                    self.folder_paths.append(entry['path_display'])
                else:
                    if '.' in entry['path_display']:
                        extension = entry['path_display'].rsplit('.', 1)[1]
                        if extension in self.image_extensions:
                            self.counter += 1
                            print(f"- Detected {entry['.tag']} {self.counter}: {entry['path_display']}")
                            txtfile.write(entry['path_display'] + '\n')  # Added newline
                            self.image_paths.append(entry['path_display'])

        else:
            print(f"Error: {response.status_code}")
            print(response.text)


    def download(self, dropbox_path, local_directory):
        # Check if token is expired
        if self.token_expired():
            self.refresh_access_token()

        # Define the Dropbox API endpoint
        url = "https://content.dropboxapi.com/2/files/download"

        # Define the headers, including the authorization and Dropbox-API-Arg
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Dropbox-API-Arg": json.dumps({
                "path": dropbox_path  # No need to encode here, only encode when sending the URL
            })
        }

        # Send the POST request
        response = requests.post(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            binary_data = response.content

            # Construct the local path (stripping leading '/' from dropbox_path for file name)
            # Use os.path.join to ensure correct path formation across platforms
            download_path = os.path.join(local_directory, dropbox_path.lstrip('/'))

            # Ensure the directory exists locally
            os.makedirs(os.path.dirname(download_path), exist_ok=True)

            # Save the binary data to a file
            with open(download_path, "wb") as file:
                file.write(binary_data)

            #print(f"File downloaded successfully to: {download_path}")
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    # Create class instance
    session = DropboxTraverseDownload()

    # If path is "", this indicates traversing the entire dropbox and not a specific directory
    # Can change to accept user input
    path = ""
    session.folder_paths.append(path)

    # Local directory to save files
    #local_directory = "/Users/aidagarrido/Desktop/DOWNLOAD_TEST"
    local_directory = input("Local directory for download: ")
    while not os.path.isdir(local_directory):
        local_directory = input("Directory does not exist. Try again: ")

    # Create desktop file path to save file paths to txt
    # Get the path to the user's home directory
    home_dir = os.path.expanduser('~')
    # Path to the Desktop folder (typically under the user's home directory)
    desktop_path = os.path.join(home_dir, 'Desktop')


    # Step 1, traverse dropbox and gather file names into txt file
    # Open the file for writing
    with open(os.path.join(desktop_path, "dropbox_image_filepaths_test.txt"), "w") as file:
        while session.folder_paths:
            path = session.folder_paths.pop()
            session.listcontents(path, file)
            file.flush()

    # Step 2, download files
    i = 1
    # Open the text file in read mode ('r')
    with open(os.path.join(desktop_path, "dropbox_image_filepaths_test.txt"), 'r') as file:
        # Iterate through each line in the file
        for line in file:
            # Strip the newline character from each line
            dropbox_path = line.strip()
            session.download(dropbox_path, local_directory)
            print(f"- Downloaded file {i} of {session.counter}: {dropbox_path}")
            i += 1

    # Step 3, delete txt file
    os.remove(os.path.join(desktop_path, "dropbox_image_filepaths_test.txt"))

import datetime
import requests
import json
import time
import os

class LongPoll:

    def __init__(self):

        # Library of image extensions
        self.image_extensions = [
            "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp", "svg", "heif", "heic", "ico",
            "raw", "exr", "apng", "pdf", "psd", "ai", "eps", "indd", "heif", "jpe", "jfif", "wdp", "dng",
            "fpx", "pcx", "pgm", "ppm", "tga", "xcf", "cur", "webm", "3fr", "arw", "bay", "cr2", "crw", "dcr",
            "mef", "mrw", "nef", "orf", "pef", "raf", "sr2", "srw", "tiff", "xpm", "yuv", "kdc", "sct", "pict",
            "bpg", "jxr", "wdp", "xif", "fif"
        ]

        # Credentials for creating access token
        self.client_id = 'bsp8x2pbkklqbz8'
        self.client_secret = 'c3po7io03u5zgtt'
        self.refresh_token = 'diOhyTjXTgsAAAAAAAAAAfak8rrGSeI0tELBy1SdQceJyvoei6qBfsSXFvAMOzio'
        self.ACCESS_TOKEN = ''

        # Keeping track of access token's expiration
        self.time_now = ''
        self.time_expire = ''

        # Local directory for downloads
        self.local_directory = ''

    # Timer
    def timer(self, timeout):
        for remaining in range(timeout, 0, -1):
            time.sleep(1)

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

    def get_cursor(self, path):
        print("Fetching cursor")
        cursor, has_more = lp.list_folder(path)

        while has_more:
            cursor, has_more = lp.list_folder_continue(cursor)

        print("Cursor fetched")
        return cursor

    def list_folder(self, path):
        url = "https://api.dropboxapi.com/2/files/list_folder"

        # Replace 'YOUR_ACCESS_TOKEN' with your actual OAuth access token
        headers = {
            "Authorization": f'Bearer {self.ACCESS_TOKEN}',  # OAuth Access Token
            "Content-Type": "application/json",
        }

        # Data to be sent in the request body
        data = {
            "include_deleted": False,
            "include_has_explicit_shared_members": False,
            "include_media_info": False,
            "include_mounted_folders": True,
            "include_non_downloadable_files": True,
            "path": path,  # Path to the folder
            "recursive": True
        }

        # Send the POST request
        response = requests.post(url, headers=headers, data=json.dumps(data))

        # Check the response status and print it
        if response.status_code == 200:
            #print(response.json())
            return response.json()['cursor'], response.json()['has_more']
        else:
            print("Error:", response.status_code, response.text)

    def list_folder_continue(self, cursor):

        url = "https://api.dropboxapi.com/2/files/list_folder/continue"
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",  # Replace with actual authorization header
            "Content-Type": "application/json"
        }

        data = {
            "cursor": cursor  # Your cursor value
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))

        # Print response to see the result
        return response.json()['cursor'], response.json()['has_more']

    def list_changes(self, cursor):

        url = "https://api.dropboxapi.com/2/files/list_folder/continue"
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",  # Replace with actual authorization header
            "Content-Type": "application/json"
        }

        data = {
            "cursor": cursor  # Your cursor value
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))

        # If reponse contains entries, see which are image uploads
        if response.json()['entries']:
            self.image_detect(response.json())

    def image_detect(self, response):
        # Check if token is expired
        if self.token_expired():
            self.refresh_access_token()

        # Loop through the entries and select those where .tag is 'file'
        file_entries = [entry for entry in response['entries'] if entry['.tag'] == 'file']

        # Print the file entries
        for entry in file_entries:
            if entry['.tag'] == 'file':
                if '.' in entry['path_display']:
                    extension = entry['path_display'].rsplit('.', 1)[1]
                    if extension in self.image_extensions:
                        print(f"- Detected new image upload: {entry['path_display']}")


    def download(self, dropbox_path):
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
            download_path = os.path.join(self.local_directory, dropbox_path.lstrip('/'))

            # Ensure the directory exists locally
            os.makedirs(os.path.dirname(download_path), exist_ok=True)

            # Save the binary data to a file
            with open(download_path, "wb") as file:
                file.write(binary_data)

            #print(f"File downloaded successfully to: {download_path}")
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            print(response.text)

    def longpoll(self, cursor, timeout):
        # Set the Dropbox API endpoint and the headers
        url = "https://notify.dropboxapi.com/2/files/list_folder/longpoll"
        headers = {
            "Content-Type": "application/json"
        }

        # Define the data for the request
        data = {
            "cursor": cursor,
            "timeout": timeout
        }

        # Make the POST request
        response = requests.post(url, headers=headers, data=json.dumps(data))

        # Check the response
        if response.status_code == 200:
            print("Response received successfully:")
            return response.json()['changes']
        else:
            print("Error:", response.status_code)
            print(response.text)


if __name__ == "__main__":
    # Create class instance
    lp = LongPoll()
    lp.refresh_access_token()

    # Specify dropbox path, if blank this means the entire dropbox
    path = ""

    # Get cursor
    cursor = lp.get_cursor(path)

    # Specify timeout
    timeout = 30

    # Specify local directory for downloads
    lp.local_directory = "/Users/aidagarrido/Desktop/DOWNLOAD_TEST"
    #local_directory = input("Local directory for download: ")
    #while not os.path.isdir(local_directory):
    #    local_directory = input("Directory does not exist. Try again: ")

    while True:
        if lp.token_expired():
            lp.refresh_access_token()
        changes = lp.longpoll(cursor, timeout)
        if changes:
            print("changes")
            lp.timer(10)
            lp.list_changes(cursor)
            cursor = lp.get_cursor(path)
        else:
            print('no changes')

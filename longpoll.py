import datetime
import requests
import json
import time
import os
import sendnetworkmail
import sys
import atexit


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
        ## AG's personal dropbox
        self.client_id = 'bsp8x2pbkklqbz8'
        self.client_secret = 'c3po7io03u5zgtt'
        self.refresh_token = 'diOhyTjXTgsAAAAAAAAAAfak8rrGSeI0tELBy1SdQceJyvoei6qBfsSXFvAMOzio'
        self.ACCESS_TOKEN = ''

        ## CS's personal dropbox
        #self.client_id = 'wjmmemxgpuxh911'
        #self.client_secret = 'mynnf0nelu4xahk'
        #self.refresh_token = 'ST-MxmX3A50AAAAAAAAAAahnN5Tez_DKUHRTFfp9-VhLcf73AzHQlyJQdVxdDrZM'
        #self.ACCESS_TOKEN = ''

        # Keeping track of access token's expiration
        self.time_now = ''
        self.time_expire = ''

        # Local directory for downloads
        self.local_directory = ''

        # Array of detects images
        self.images_detected = []


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

    def latest_cursor(self, path):

        # Define the URL and the access token
        url = "https://api.dropboxapi.com/2/files/list_folder/get_latest_cursor"

        # Define the headers
        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        # Define the data payload
        data = {
            "include_deleted": False,
            "include_has_explicit_shared_members": False,
            "include_media_info": False,
            "include_mounted_folders": True,
            "include_non_downloadable_files": True,
            "path": path,
            "recursive": True
        }

        # Send the POST request
        response = requests.post(url, headers=headers, json=data)

        # Check the response status and print the result
        if response.status_code == 200:
            print("Success:", response.json())
            return response.json()['cursor']
        else:
            print("Error:", response.status_code, response.text)

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
            print(response.json())

    def image_detect(self, response):
        # Check if token is expired
        if self.token_expired():
            self.refresh_access_token()

        # Loop through the entries and select those where .tag is 'file'
        file_entries = [entry['path_display'] for entry in response['entries'] if entry['.tag'] == 'file']

        # Print the file entries
        for entry in file_entries:
            if '.' in entry:
                extension = entry.rsplit('.', 1)[1]
                if extension in self.image_extensions:
                    print(f"- Detected new image upload: {entry}")
                    print(entry)
                    self.images_detected.append(entry)
                    self.download(entry)

    def get_unique_filename(self, directory, filename):
        # Get the full path of the file
        base_name, extension = os.path.splitext(filename)

        # Start with the original filename
        new_filename = filename
        counter = 1

        # Loop until the file does not exist in the directory
        while os.path.exists(os.path.join(directory, new_filename)):
            # If the file exists, append a counter to the base name
            new_filename = f"{base_name}_{counter}{extension}"
            counter += 1

        return new_filename

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

            # Ensure unique file path
            #download_path = self.get_unique_filename(download_path, dropbox_path)

            # Save the binary data to a file
            with open(download_path, "wb") as file:
                file.write(binary_data)

            print(f"File downloaded successfully to: {download_path}")
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            print(response.text)

    def email_notification(self, unexpected_quit=False):
        time_stamp = datetime.datetime.now()

        notification = sendnetworkmail.SendNetworkEmail()
        notification.sender("library@tv.cuny.edu")
        # notification.recipients(["library@tv.cuny.edu"])
        notification.recipients(["aida.garrido@tv.cuny.edu"])

        if not unexpected_quit:
            notification.subject(f"Dropbox images digest: {time_stamp}")

            # Initialize an HTML formatted string for key-value pairs
            html_output = ""

            for file in self.images_detected:
                html_output += f"{file}<br>\n"

            html_content = f"""
                    <html>
                      <body>
                        <p>Hello, </p>
                        <p>The following images were recently uploaded to dropbox:</p>
                        {html_output}
                        <p></p>
                        Best,
                        <br>Library Bot
                      </body>
                    </html>
                    """

            # Set notification content
            notification.html_content(html_content)

            # Send the notification
            notification.send()
        else:
            notification.subject(f"ERROR: {os.path.basename(__file__)} unexpectedly quit")

            html_content = f"""<p>{os.path.basename(__file__)}, the program which detects new dropbox image uploads unexpectedly quit.</p>"""

            # Set notification content
            notification.content(html_content)

            # Send the notification
            notification.send()


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
    db_path = ""
    
    # Get cursor
    cursor = lp.latest_cursor(db_path)

    # Specify timeout
    timeout = 30

    # Specify local directory for downloads
    lp.local_directory = "/Users/aidagarrido/Desktop/DOWNLOAD_TEST"
    # lp.local_directory = input("Local directory for download: ")
    # while not os.path.isdir(local_directory):
    #    lp.local_directory = input("Directory does not exist. Try again: ")

    while True:
        if lp.token_expired():
            lp.refresh_access_token()
        changes = lp.longpoll(cursor, timeout)
        if changes:
            print("changes")
            lp.timer(30)
            new_cursor = lp.latest_cursor(db_path)
            lp.list_changes(cursor)

            if lp.images_detected:
                lp.email_notification()

            cursor = new_cursor
            lp.images_detected = []
        else:
            print('no changes')

    ## Next, checksum verification
    ## Send email if application quits
    ## Schedule
    ## Create icon?

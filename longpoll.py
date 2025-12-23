import datetime
import requests
import json
import time
import os
import sendnetworkmail

class LongPoll:
    # Two types of processes, specify by string: 'remote' and 'photo'
    def __init__(self):
        # Credentials for creating access token
        ## AG's personal dropbox
        #self.client_id = 'bsp8x2pbkklqbz8'
        #self.client_secret = 'c3po7io03u5zgtt'
        #self.refresh_token = 'diOhyTjXTgsAAAAAAAAAAfak8rrGSeI0tELBy1SdQceJyvoei6qBfsSXFvAMOzio'
        #self.ACCESS_TOKEN = ''

        ## ag's dropbox
        self.client_id = 'wmub6kuvhq3xviy'
        self.client_secret = '9blokt7f8ac0v9c'
        self.refresh_token = '04OpIpx9TukAAAAAAAAAAcI1CpMvfrjlRkpUzG9hTdOFY5Be-R6unYHdLBcnR8No'
        self.ACCESS_TOKEN = ''

        # Keeping track of access token's expiration
        self.time_now = ''
        self.time_expire = ''

        # Nested dictionary
        self.folders_files_detected = {}
        self.folder_files = {"old_names": [], "share_link": None, "files": []}

        # Activate API variables
        self.refresh_access_token()

    def timer(self, timeout):
        for remaining in range(timeout, 0, -1):
            time.sleep(1)

    def refresh_access_token(self):
        max_retries = 5
        retries = 0

        url = 'https://api.dropboxapi.com/oauth2/token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }

        while retries < max_retries:
            try:
                response = requests.post(url, data=data)

                if response.status_code == 200:
                    response_data = response.json()
                    self.ACCESS_TOKEN = response_data['access_token']
                    expires_in = response_data['expires_in']

                    time_now = datetime.datetime.now()
                    self.time_expire = time_now + datetime.timedelta(
                        seconds=expires_in - 1000)
                    return
                else:
                    print(f"Failed to refresh access token. Status code: {response.status_code}")
                    print(response.text)

            except requests.RequestException as e:
                print(f"Request failed: {e}")

            retries += 1

            if retries < max_retries:
                print(f"Retrying... ({retries}/{max_retries})")
                time.sleep(2)

        print("Max retries reached. Failed to refresh access token.")
        return None

    # Checks if access token has expired
    def token_expired(self):
        time_now = datetime.datetime.now()

        if time_now >= self.time_expire:
            return True
        else:
            return False

    def latest_cursor(self, path):
        max_retries = 5
        retries = 0

        url = "https://api.dropboxapi.com/2/files/list_folder/get_latest_cursor"

        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        data = {
            "include_deleted": False,
            "include_has_explicit_shared_members": False,
            "include_media_info": False,
            "include_mounted_folders": True,
            "include_non_downloadable_files": True,
            "path": path,
            "recursive": True
        }

        while retries < max_retries:
            try:
                response = requests.post(url, headers=headers, json=data)

                if response.status_code == 200:
                    return response.json()['cursor']
                else:
                    print(f"Failed to get cursor. Status code: {response.status_code}")
                    print(response.text)

            except requests.RequestException as e:
                print(f"Request failed: {e}")

            retries += 1

            if retries < max_retries:
                print(f"Retrying... ({retries}/{max_retries})")
                time.sleep(2)

        print("Max retries reached. Failed to get the cursor.")
        return None

    def list_changes(self, cursor):
        max_retries = 5
        retries = 0

        url = "https://api.dropboxapi.com/2/files/list_folder/continue"

        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        data = {
            "cursor": cursor
        }

        while retries < max_retries:
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data))

                if response.status_code == 200:
                    if response.json().get('entries'):
                        return response.json()
                    else:
                        print("No entries found.")
                    return
                else:
                    print(f"Failed to retrieve data. Status code: {response.status_code}")
                    print(response.text)

            except requests.RequestException as e:
                print(f"Request failed: {e}")

            retries += 1

            if retries < max_retries:
                print(f"Retrying... ({retries}/{max_retries})")
                time.sleep(2)

        print("Max retries reached. Failed to process the request.")
        return None

    def guess_type(self, name, max_ext_len=5):
        for i in range(1, max_ext_len + 1):
            if len(name) > i and name[-(i + 1)] == '.':
                return "file"
        return "folder"

    def folders_files_detect(self, response, pattern):
        for entry in response['entries']:
            if self.guess_type(entry['name']) == 'file':  # if file
                path = entry['path_display'].rsplit('/', 1)[0]
                folder_name = path.rsplit('/', 1)[1]
            else:
                path = entry['path_display']
                folder_name = entry['name']

            if pattern.fullmatch(path):
                if path not in self.folders_files_detected:
                    new_dict = {k: [] for k in self.folder_files.keys()}
                    self.folders_files_detected[path] = new_dict
                    if entry['.tag'] == 'deleted':
                        self.folders_files_detected[path]['share_link'] = None
                    else:
                        share_link = self.get_shared_link(entry['path_display'])
                        if share_link:
                            share_link = share_link.split("&")[0]
                        self.folders_files_detected[path]['share_link'] = share_link

                if folder_name != entry['name']:  # if file
                    self.folders_files_detected[path]['files'].append(entry['name'])

        print(self.folders_files_detected)
        # concatenate dictionaries with the same files[],
        # to distinguish new and deleted entries from entries that were renamed or moved
        for folder in list(self.folders_files_detected.keys()):
            if self.folders_files_detected[folder]['share_link']:
                for folder2 in list(self.folders_files_detected.keys()):
                    if folder != folder2 and not self.folders_files_detected[folder2]['share_link'] and sorted(
                            self.folders_files_detected[folder]['files']) == sorted(
                            self.folders_files_detected[folder2]['files']):
                        self.folders_files_detected[folder]['old_names'].append(folder2)
                        del self.folders_files_detected[folder2]

    def download(self, dropbox_path, download_path):
        max_retries = 5
        retries = 0

        if self.token_expired():
            self.refresh_access_token()

        url = "https://content.dropboxapi.com/2/files/download"

        headers = {
            "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            "Dropbox-API-Arg": json.dumps({
                "path": dropbox_path
            })
        }

        while retries < max_retries:
            try:
                response = requests.post(url, headers=headers)

                if response.status_code == 200:
                    binary_data = response.content
                    os.makedirs(os.path.dirname(download_path), exist_ok=True)

                    with open(download_path, "wb") as file:
                        file.write(binary_data)

                    print(f"File downloaded successfully to: {download_path}")
                    return
                else:
                    print(f"Failed to download file. Status code: {response.status_code}")
                    print(response.text)

            except requests.RequestException as e:
                print(f"Request failed: {e}")

            retries += 1
            if retries < max_retries:
                print(f"Retrying... ({retries}/{max_retries})")
                time.sleep(2)

        print("Max retries reached. Failed to download the file.")
        return None

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
                return response.json()['links'][0]['url']
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
            return response.json()['url']
        except requests.exceptions.HTTPError as e:
            return None

    def email_notification(self, unexpected_quit=False):
        time_stamp = datetime.datetime.now()

        notification = sendnetworkmail.SendNetworkEmail()
        notification.sender("library@tv.cuny.edu")
        # notification.recipients(["library@tv.cuny.edu"])
        notification.recipients(["aida.garrido@tv.cuny.edu"])

        if not unexpected_quit:
            notification.subject(f"Dropbox images digest: {time_stamp}")

            html_output = ""

            for file in self.folders_files_detected:
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

            notification.html_content(html_content)
            notification.send()
        else:
            notification.subject(f"ERROR: {os.path.basename(__file__)} unexpectedly quit")

            html_content = f"""<p>{os.path.basename(__file__)}, the program which detects new dropbox image uploads unexpectedly quit.</p>"""

            notification.html_content(html_content)
            notification.send()

    def longpoll(self, cursor, timeout):
        url = "https://notify.dropboxapi.com/2/files/list_folder/longpoll"
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "cursor": cursor,
            "timeout": timeout
        }

        max_retries = 5
        retries = 0

        while retries < max_retries:
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data))

                if response.status_code == 200:
                    return response.json()['changes']

                else:
                    print(f"Error: {response.status_code} - {response.text}")

            except requests.RequestException as e:
                print(f"Request failed: {e}")

            retries += 1

            if retries < max_retries:
                print(f"Retrying... ({retries}/{max_retries})")
                time.sleep(2)

        print("Max retries reached. No successful response received.")
        return None


if __name__ == "__main__":
    # try:
    #    p = sys.argv[1]
    # except:
    #    print("Process not specified.")
    # sys.exit()
    #     p = "remote"

    # Create class instance
    lp = LongPoll()

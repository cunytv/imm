#!/usr/bin/env python3

from datetime import datetime, timedelta
import requests
import time
import json

## CS's personal dropbox
client_id = 'wjmmemxgpuxh911'
client_secret = 'mynnf0nelu4xahk'
refresh_token = 'ST-MxmX3A50AAAAAAAAAAahnN5Tez_DKUHRTFfp9-VhLcf73AzHQlyJQdVxdDrZM'
ACCESS_TOKEN = ''

# Keeping track of access token's expiration
time_now = ''
time_expire = ''

db_main_dir = "/►CUNY TV REMOTE FOOTAGE (for DELIVERY & COPY from)"


# Timer
def timer(timeout):
    for remaining in range(timeout, 0, -1):
        time.sleep(1)


def refresh_access_token():
    global time_now, time_expire, ACCESS_TOKEN

    # Maximum retry attempts
    max_retries = 5
    retries = 0

    url = 'https://api.dropboxapi.com/oauth2/token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }

    while retries < max_retries:
        try:
            # Send the POST request
            response = requests.post(url, data=data)

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the response JSON and update the access token and expiration time
                response_data = response.json()
                ACCESS_TOKEN = response_data['access_token']
                expires_in = response_data['expires_in']

                # Calculate the expiration time
                time_now = datetime.now()
                time_expire = time_now + timedelta(
                    seconds=expires_in - 1000)  # Subtract a buffer (1000 seconds)
                return  # Exit method if successful
            else:
                print(f"Failed to refresh access token. Status code: {response.status_code}")
                print(response.text)

        except requests.RequestException as e:
            # Handle network or request-related errors
            print(f"Request failed: {e}")

        # Increment the retry counter
        retries += 1

        # Wait before retrying
        if retries < max_retries:
            print(f"Retrying... ({retries}/{max_retries})")
            time.sleep(2)  # Wait 2 seconds before retrying (you can adjust this)

    print("Max retries reached. Failed to refresh access token.")
    return None

def list_folder(path):
    # Maximum retry attempts
    max_retries = 5
    retries = 0

    # Define the Dropbox API endpoint
    url = "https://api.dropboxapi.com/2/files/list_folder"

    # Define the headers
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",  # Replace with actual authorization header
        "Content-Type": "application/json"
    }

    # Define the data for the request
    data = {
    "include_deleted": False,
    "include_has_explicit_shared_members": False,
    "include_media_info": False,
    "include_mounted_folders": False,
    "include_non_downloadable_files": False,
    "path": path,
    "recursive": False
    }

    while retries < max_retries:
        try:
            # Send the POST request
            response = requests.post(url, headers=headers, data=json.dumps(data))

            # Check if the request was successful
            if response.status_code == 200:
                # If response contains entries, process them
                return response.json()
            else:
                print(f"Failed to retrieve data. Status code: {response.status_code}")
                print(response.text)

        except requests.RequestException as e:
            # Handle network or request-related errors
            print(f"Request failed: {e}")

        # Increment the retry counter
        retries += 1

        # Wait before retrying
        if retries < max_retries:
            print(f"Retrying... ({retries}/{max_retries})")
            time.sleep(2)  # Wait 2 seconds before retrying (you can adjust this)

    print("Max retries reached. Failed to process the request.")
    return None


def delete_folder(path):
    # Maximum retry attempts
    max_retries = 5
    retries = 0

    # Define the Dropbox API endpoint
    url = "https://api.dropboxapi.com/2/files/delete_v2"

    # Define the headers
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",  # Replace with actual authorization header
        "Content-Type": "application/json"
    }

    # Define the data for the request
    data = {
    "path": path,
    }

    while retries < max_retries:
        try:
            # Send the POST request
            response = requests.post(url, headers=headers, data=json.dumps(data))

            # Check if the request was successful
            if response.status_code == 200:
                return
            else:
                print(f"Failed to retrieve data. Status code: {response.status_code}")
                print(response.text)

        except requests.RequestException as e:
            # Handle network or request-related errors
            print(f"Request failed: {e}")

        # Increment the retry counter
        retries += 1

        # Wait before retrying
        if retries < max_retries:
            print(f"Retrying... ({retries}/{max_retries})")
            time.sleep(2)  # Wait 2 seconds before retrying (you can adjust this)

    print("Max retries reached. Failed to process the request.")
    return None


three_days_before = datetime.now() - timedelta(days=3)
formatted_three_days_before = three_days_before.strftime("%Y.%m.%d")

refresh_access_token()
r = list_folder(db_main_dir)

show_dir = []
for entry in r["entries"]:
    if "►" in entry["name"]:
        show_dir.append(entry["path_display"])

photos_dir =[]
for dir in show_dir:
    r = list_folder(dir)
    for entry in r["entries"]:
        if "PHOTOS" in entry["name"]:
            photos_dir.append(entry["path_display"])

three_day_dir = []
for dir in photos_dir:
    r = list_folder(dir)
    for entry in r["entries"]:
        n = entry["name"]
        if str(formatted_three_days_before) in entry["name"]:
            three_day_dir.append(entry["path_display"])

for dir in three_day_dir:
    r = list_folder(dir)
    if not r["entries"]:
        delete_folder(dir)
        print(f"Deleted {dir}")

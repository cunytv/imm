#!/usr/bin/env python3

import os
import re
import subprocess
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import longpoll

process = "remote"
lp = longpoll.LongPoll()

# Specify default txt file, where cursor is stored
home_dir = os.path.expanduser('~')
documents_path = os.path.join(home_dir, 'Documents', 'longpoll')
os.makedirs(documents_path, exist_ok=True)
cursor_txt_path = os.path.join(documents_path, f"dropbox_longpoll_cursor_{process}.txt")

# DB path to traverse
db_path = "/_CUNY TV CAMERA CARD DELIVERY"

# DB path folder pattern
remote_pattern = re.compile(r"/_CUNY TV CAMERA CARD DELIVERY/[^/]+/([A-Z]+)(\d{4})(\d{2})(\d{2})_(.+)")

# Path for storing share links
link_json_path = os.path.join(home_dir, 'Documents', 'remote_share_links.json')

# Get cursor
cursor = ''
if os.path.exists(cursor_txt_path):
    with open(cursor_txt_path, 'r') as file:
        cursor = file.readline().strip()
else:
    print("Creating cursor")
    cursor = lp.latest_cursor(db_path)
    with open(cursor_txt_path, 'w') as file:
        file.write(cursor)

# Specify timeout
timeout = 30

def update_db_link_by_title():
    result = subprocess.run(["php", "update_db_link_by_title.php", link_json_path], capture_output=True, text=True)
    data = json.loads(result.stdout)

    if data:
        with open(link_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    else:
        os.remove(link_json_path)


# Consider unprocessed folder names
if os.path.exists(link_json_path):
    update_db_link_by_title()

# Begin longpoll
changes = lp.longpoll(cursor, timeout)
if changes:
    new_cursor = lp.latest_cursor(db_path)
    has_more = True
    while has_more:
        response = lp.list_changes(cursor)

        if response and 'entries' in response and response['entries']:
            lp.folders_files_detect(response, remote_pattern)
            # Save detected folders as json
            if lp.folders_files_detected:
                if os.path.exists(link_json_path):
                    with open(link_json_path, "r", encoding="utf-8") as f:
                        unprocessed_folders = json.load(f)
                    lp.folders_files_detected.update(unprocessed_folders)

                with open(link_json_path, "w") as f:
                    json.dump(lp.folders_files_detected, f)
        else:
            break
        has_more = response['has_more']

    # Update cursor
    with open(cursor_txt_path, 'w') as file:
        file.write(new_cursor)

    # Call php script to update links in Resourcespace
    update_db_link_by_title()
else:
    print('No changes')

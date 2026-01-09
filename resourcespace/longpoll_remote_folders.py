#!/usr/bin/env python3

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

def merge_folder_dicts(dict1, dict2):
    merged = dict1.copy()  # start with a copy of dict1

    for folder, info2 in dict2.items():
        if folder in merged:
            info1 = merged[folder]

            # Merge lists without duplicates
            info1["old_names"] = list(set(info1.get("old_names", []) + info2.get("old_names", [])))
            info1["files"] = list(set(info1.get("files", []) + info2.get("files", [])))

            # Keep share_link from dict1 if exists, otherwise use dict2
            if not info1.get("share_link"):
                info1["share_link"] = info2.get("share_link")

            merged[folder] = info1
        else:
            merged[folder] = info2

    return merged

def update_db_link_by_title():
    result = subprocess.run(["php", "/Users/libraryad/Documents/GitHub/imm/resourcespace/update_db_link_by_title.php", link_json_path], capture_output=True, text=True, start_new_session=True)
    print(result.stdout)
    print(result.stderr)
    
# Begin longpoll
changes = lp.longpoll(cursor, timeout)
if changes:
    has_more = True
    while has_more:
        response = lp.list_changes(cursor)
        if response and 'entries' in response and response['entries']:
            cursor = response['cursor']
            lp.folders_files_detect(response, remote_pattern)
        else:
            break
        has_more = response['has_more']

    # Save detected folders as json
    if lp.folders_files_detected:
        if os.path.exists(link_json_path):
            with open(link_json_path, "r", encoding="utf-8") as f:
                unprocessed_folders = json.load(f)
            lp.folders_files_detected = merge_folder_dicts(lp.folders_files_detected, unprocessed_folders)

        with open(link_json_path, "w", encoding="utf-8") as f:
            json.dump(lp.folders_files_detected, f, indent=2, sort_keys=True)

    # Update cursor
    with open(cursor_txt_path, 'w') as file:
        file.write(cursor)
else:
    print('No changes')

# Run title update
if (os.path.exists(link_json_path)):
    update_db_link_by_title()

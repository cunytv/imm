#!/usr/bin/env python3

import os
import re
import subprocess
import json
import sys

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
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

# Begin longpoll
changes = lp.longpoll(cursor, timeout)
if changes:
    new_cursor = lp.latest_cursor(db_path)
    response = lp.list_changes(cursor)

    if response:
        lp.folders_files_detect(response, remote_pattern)

        # Save detected folders as json
        if lp.folders_files_detected:
            print(lp.folders_files_detected)
            json_path = os.path.join(home_dir, 'Documents', 'remote_share_links.json')
            with open(json_path, "w") as f:
                json.dump(lp.folders_files_detected, f)

            # Call php script to update links in Resourcespace
            if lp.folders_files_detected:
                php_script = os.path.join(
                    os.path.dirname(__file__),  "update_db_link_by_title.php"
                )

                result = subprocess.run(["php", php_script, json_path], capture_output=True, text=True)
                print(result.stdout)

            os.remove(json_path)

        # Update cursor
        with open(cursor_txt_path, 'w') as file:
            file.write(new_cursor)
    else:
        print('No changes')
else:
    print('No changes')

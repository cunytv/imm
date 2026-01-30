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


def merge_folder_dicts(up_dict, new_dict):
    merged = up_dict.copy()

    for folder, info2 in new_dict.items():
        exact_match = (folder in merged and merged[folder]["id"] == info2["id"])
        only_id_match = next((k for k, v in merged.items() if v["id"] == info2["id"] and k != folder), None)
        only_name_match = (folder if folder in merged and merged[folder]["id"] != info2["id"] else None)

        if exact_match:  # simple merge
            target_key = folder
        elif only_id_match:  # renamed folder
            target_key = only_id_match
        elif only_name_match and merged[only_name_match]["files"].keys() == info2["files"].keys():  # deleted folder
            target_key = only_name_match
        else:  # new folder
            merged[folder] = info2
            continue

        info1 = merged[target_key]

        # files merge
        files1 = info1.get("files", {})
        files2 = info2.get("files", {})

        for f, f2 in files2.items():
            if f in files1:
                f1 = files1[f]
                f2["old_names"] = list(set(f2.get("old_names", [])) | set(f1.get("old_names", [])))
                if (f1["name"] != f2["name"] and f1["name"] not in f2["old_names"]):
                    f2["old_names"].append(f1["name"])

        info1["files"] = files2

        # share link merge
        info1["share_link"] = info2.get("share_link")

        # old names merge
        info1["old_names"] = list(set(info1.get("old_names", [])) | set(info2.get("old_names", [])))

        # id merge
        info1['id'] = info2.get('id')

        # if not simple merge
        if target_key != folder:
            del merged[target_key]

        merged[folder] = info1

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
            lp.folders_files_detected = merge_folder_dicts(unprocessed_folders, lp.folders_files_detected)

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

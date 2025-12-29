#!/usr/bin/env python3

import re
import shutil
import json
import subprocess
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import longpoll

process = "photo"
lp = longpoll.LongPoll()

# Specify default txt file, where cursor is stored
home_dir = os.path.expanduser('~')
documents_path = os.path.join(home_dir, 'Documents', 'longpoll')
os.makedirs(documents_path, exist_ok=True)
cursor_txt_path = os.path.join(documents_path, f"dropbox_longpoll_cursor_{process}.txt")

# Path to save share links
link_json_path = os.path.join(home_dir, 'Documents', 'photo_share_links.json')

# DB path to traverse
db_path = "/►CUNY TV REMOTE FOOTAGE (for DELIVERY & COPY from)"

# DB path folder pattern
photo_pattern = re.compile(r"/►CUNY TV REMOTE FOOTAGE \(for DELIVERY & COPY from\)/►[^/]+/PHOTOS/(\d{4}\.\d{2}\.\d{2}T[^/]+)")

# Server folder path for downloads
# Specify local directory for downloads
local_directory = "/Volumes/CUNYTVMEDIA/archive_projects/Photos"
#local_directory = "/Users/aidagarrido/Desktop/DOWNLOAD_TEST"
os.makedirs(local_directory, exist_ok=True)

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

# Get local download path from db path ... /Remote/Show/Photos/Date -> RootLocalDir/Show/Date
def get_folder_download_path(f):
    parts = f.strip("/").split("/")
    selected_parts = [parts[1], parts[3]]
    relative_path = os.path.join(*selected_parts)
    full_path = os.path.join(local_directory, relative_path)
    full_path = full_path.replace('►', '')

    return full_path

def transfer_files(src_folder, dst_folder):
    os.makedirs(dst_folder, exist_ok=True)
    for filename in os.listdir(src_folder):
        src_path = os.path.join(src_folder, filename)
        dst_path = os.path.join(dst_folder, filename)

        if os.path.isfile(src_path):
            shutil.move(src_path, dst_path)

        os.rmdir(src_folder)
        os.rmdir(src_folder)


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


def update_db_link_by_folder():
    result = subprocess.run(["php", "/Users/libraryad/Documents/GitHub/imm/resourcespace/update_db_link_by_folder.php", link_json_path], capture_output=True, text=True, start_new_session=True)
    print(result.stdout)
    print(result.stderr)

# Begin longpoll
changes = lp.longpoll(cursor, timeout)
if changes:
    new_cursor = lp.latest_cursor(db_path)
    has_more = True
    while has_more:
        response = lp.list_changes(cursor)

        if response and 'entries' in response and response['entries']:
            lp.folders_files_detect(response, photo_pattern)
            has_more = response['has_more']
            cursor = response['cursor']
        else:
            break

    # Download or transfer files
    for folder in lp.folders_files_detected:
        if lp.folders_files_detected[folder]['share_link']:
            new_download_path = get_folder_download_path(folder)

            if not lp.folders_files_detected[folder]['old_names']:
                print(f"Downloading files from {folder} to {new_download_path}")
                for file in lp.folders_files_detected[folder]['files']:
                    db_file_path = os.path.join(folder, file)
                    file_path_for_download = os.path.join(new_download_path, file)
                    lp.download(db_file_path, file_path_for_download)

            if lp.folders_files_detected[folder]['old_names']:
                already_on_server = False
                for oldfolder in lp.folders_files_detected[folder]['old_names']:
                    old_download_path = get_folder_download_path(oldfolder)

                    if os.path.exists(old_download_path):
                        print(f"Transfering files from {old_download_path} to {new_download_path}")
                        already_on_server = True
                        transfer_files(old_download_path, new_download_path)

                if not already_on_server:
                    print(f"Downloading files from {folder} to {new_download_path}")
                    for file in lp.folders_files_detected[folder]['files']:
                        db_file_path = os.path.join(folder, file)
                        file_path_for_download = os.path.join(new_download_path, file)
                        lp.download(db_file_path, file_path_for_download)
    # Update cursor
    with open(cursor_txt_path, 'w') as file:
        file.write(new_cursor)
else:
    print('No changes')

# Process unmatched values
if os.path.exists(link_json_path):
    with open(link_json_path, "r", encoding="utf-8") as f:
        unprocessed_folders = json.load(f)
    lp.folders_files_detected = merge_folder_dicts(lp.folders_files_detected, unprocessed_folders)

if lp.folders_files_detected:
    with open(link_json_path, "w", encoding="utf-8") as f:
        json.dump(lp.folders_files_detected, f, indent=2, sort_keys=True)

    # Update RS assets with links
    update_db_link_by_folder()
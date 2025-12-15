#!/usr/bin/env python3

import os
import re
import shutil
import json
import sys

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import longpoll

process = "photo"
lp = longpoll.LongPoll()

# Specify default txt file, where cursor is stored
home_dir = os.path.expanduser('~')
documents_path = os.path.join(home_dir, 'Documents', 'longpoll')
os.makedirs(documents_path, exist_ok=True)
cursor_txt_path = os.path.join(documents_path, f"dropbox_longpoll_cursor_{process}.txt")

# DB path to traverse
db_path = "/►CUNY TV REMOTE FOOTAGE (for DELIVERY & COPY from)"

# DB path folder pattern
photo_pattern = re.compile(r"/►CUNY TV REMOTE FOOTAGE \(for DELIVERY & COPY from\)/►[^/]+/PHOTOS/(\d{4}\.\d{2}\.\d{2}T[^/]+)")

# Server folder path for downloads
# Specify local directory for downloads
local_directory = "/Volumes/CUNYTVMEDIA/archive_projects/dropbox_photos"
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

# Begin longpoll
changes = lp.longpoll(cursor, timeout)
if changes:
    new_cursor = lp.latest_cursor(db_path)
    response = lp.list_changes(cursor)

    if response:
        lp.folders_files_detect(response, photo_pattern)

        # Save detected folders as json
        if lp.folders_files_detected:
            json_path = os.path.join(home_dir, 'Documents', 'photo_share_links.json')
            with open(json_path, "w") as f:
                json.dump(lp.folders_files_detected, f)

        # Update cursor
        with open(cursor_txt_path, 'w') as file:
            file.write(new_cursor)

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
    else:
        print('No changes')
else:
    print('No changes')

#!/usr/bin/env python3

import re
import shutil
import json
import subprocess
import sys
import os
import hashlib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from imm import longpoll

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
#local_directory = "/Volumes/CUNYTVMEDIA/archive_projects/Photos"
local_directory = "/Users/aidagarrido/Desktop/DOWNLOAD_TEST"
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

def update_db_link_by_folder():
    result = subprocess.run(["php", "/Users/libraryad/Documents/GitHub/imm/resourcespace/update_db_link_by_folder.php", link_json_path], capture_output=True, text=True, start_new_session=True)
    print(result.stdout)
    print(result.stderr)

def calculate_sha256_checksum(file_path, block_size=4 * 1024 * 1024):
    hash_object = hashlib.sha256()
    block_hashes = []

    with open(file_path, 'rb') as f:
        while True:
            block = f.read(block_size)
            if not block:
                break  # End of file

            block_hash = hashlib.sha256(block).digest()
            block_hashes.append(block_hash)

    final_hash = hash_object.hexdigest()

    return final_hash

def merge_folder_dicts(up_dict, new_dict):
    merged = up_dict.copy()  # start with json saved dicts

    for folder, info2 in new_dict.items():
        only_id_match = next((key for key in merged if new_dict[folder]['id'] == merged[key]['id'] and folder != key), None)
        only_name_match = next((key for key in merged if new_dict[folder]['id'] == merged[key]['id'] and folder == key), None)
        if folder in merged and merged[folder]['id'] == new_dict[folder]['id']:
            info1 = merged[folder]

            # Merge old_names without duplicates
            info1["old_names"] = list(set(info1.get("old_names", []) + info2.get("old_names", [])))

            # Merge file dictionaries
            files1 = info1.get("files")
            files2 = info2.get("files")

            for f in files2:
                if f in files1:
                    files2[f]["old_names"] = list(set(files2[f].get("old_names", []) + files1[f].get("old_names", [])))
                    if files1[f]['name'] != files2[f]['name'] and files1[f]['name'] not in files2[f]['old_names']:
                        files2[f]['old_names'].append(files1[f]['name'])

            info1["files"] = files2

            # Use dict 2 share link
            info1["share_link"] = info2.get("share_link")

            merged[folder] = info1
        elif only_id_match:
            info1 = merged[only_id_match]

            # Merge old_names without duplicates
            info1["old_names"] = list(set(info1.get("old_names", []) + info2.get("old_names", [])))

            # Update name
            info1["old_names"].append(only_id_match[1])

            # Merge file dictionaries
            files1 = info1.get("files")
            files2 = info2.get("files")

            for f in files2:
                if f in files1:
                    files2[f]["old_names"] = list(set(files2[f].get("old_names", []) + files1[f].get("old_names", [])))
                    if files1[f]['name'] != files2[f]['name'] and files1[f]['name'] not in files2[f]['old_names']:
                        files2[f]['old_names'].append(files1[f]['name'])

            info1["files"] = files2

            # Use dict 2 share link
            info1["share_link"] = info2.get("share_link")

            merged[folder] = info1

            del merged[only_id_match]

        elif only_name_match and merged[only_name_match]['files'].keys() == new_dict[only_name_match]['files'].keys():
            info1 = merged[only_name_match]

            # Merge old_names without duplicates
            info1["old_names"] = list(set(info1.get("old_names", []) + info2.get("old_names", [])))

            # Merge file dictionaries
            files1 = info1.get("files")
            files2 = info2.get("files")

            for f in files2:
                if f in files1:
                    files2[f]["old_names"] = list(set(files2[f].get("old_names", []) + files1[f].get("old_names", [])))
                    if files1[f]['name'] != files2[f]['name'] and files1[f]['name'] not in files2[f]['old_names']:
                        files2[f]['old_names'].append(files1[f]['name'])

            info1["files"] = files2

            # Use dict 2 share link
            info1["share_link"] = info2.get("share_link")

            merged[folder] = info1

            del merged[only_name_match]

        else:
            merged[folder] = info2

    return merged

def get_folder_checksum_array(path):
    csums = []

    for root, dirs, files in os.walk(path):
        for n in files:
            path = os.path.join(root, n)
            csum = calculate_sha256_checksum(path)
            csums.append(csum)

    return csums

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
    # Update cursor
    with open(cursor_txt_path, 'w') as file:
        file.write(cursor)

    for folder in lp.folders_files_detected:
        if lp.folders_files_detected[folder]['share_link']:
            new_download_path = get_folder_download_path(folder)

            if not lp.folders_files_detected[folder]['old_names']:
                for file in lp.folders_files_detected[folder]['files']:
                    if not lp.folders_files_detected[folder]['files'][file]['deleted']:
                        file_already_on_server = False

                        # Check through old names
                        for name in lp.folders_files_detected[folder]['files'][file]['old_names']:
                            file_path_for_download = os.path.join(new_download_path, name)
                            if os.path.exists(file_path_for_download):
                                file_already_on_server = True
                                break
                        if not file_already_on_server:
                            db_file_path = os.path.join(folder, lp.folders_files_detected[folder]['files'][file]['name'])
                            file_path_for_download = os.path.join(new_download_path, lp.folders_files_detected[folder]['files'][file]['name'])
                            lp.download(db_file_path, file_path_for_download)
            else:
                folder_already_on_server = False
                for oldfolder in lp.folders_files_detected[folder]['old_names']:
                    old_download_path = get_folder_download_path(oldfolder)

                    if os.path.exists(old_download_path):
                        print(f"Transfering files from {old_download_path} to {new_download_path}")
                        folder_already_on_server = True
                        transfer_files(old_download_path, new_download_path)

                        for file in lp.folders_files_detected[folder]['files']:
                            if not lp.folders_files_detected[folder]['files'][file]['deleted']:
                                file_already_on_server = False
                                # Check through old names
                                for name in lp.folders_files_detected[folder]['files'][file]['old_names']:
                                    file_path_for_download = os.path.join(new_download_path, name)
                                    if os.path.exists(file_path_for_download):
                                        file_already_on_server = True
                                        break
                                if not file_already_on_server:
                                    db_file_path = os.path.join(folder, lp.folders_files_detected[folder]['files'][file]['name'])
                                    file_path_for_download = os.path.join(new_download_path, lp.folders_files_detected[folder]['files'][file]['name'])
                                    lp.download(db_file_path, file_path_for_download)

                if not folder_already_on_server:
                    for file in lp.folders_files_detected[folder]['files']:
                        if not lp.folders_files_detected[folder]['files'][file]['deleted']:
                            db_file_path = os.path.join(folder, lp.folders_files_detected[folder]['files'][file]['name'])
                            file_path_for_download = os.path.join(new_download_path, lp.folders_files_detected[folder]['files'][file]['name'])
                            lp.download(db_file_path, file_path_for_download)
    # Update cursor
    with open(cursor_txt_path, 'w') as file:
        file.write(cursor)
else:
    print('No changes')


# Process unmatched values
if os.path.exists(link_json_path):
    with open(link_json_path, "r", encoding="utf-8") as f:
        unprocessed_folders = json.load(f)
    lp.folders_files_detected = merge_folder_dicts(unprocessed_folders, lp.folders_files_detected)

if lp.folders_files_detected:
    with open(link_json_path, "w", encoding="utf-8") as f:
        json.dump(lp.folders_files_detected, f, indent=2, sort_keys=True)

# Run folder update
if (os.path.exists(link_json_path)):
    update_db_link_by_folder()
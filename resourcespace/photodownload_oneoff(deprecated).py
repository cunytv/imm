#!/usr/bin/env python3

import os
import re
import shutil
import json
import sys

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import longpoll

# DB path to traverse
db_path = "/►CUNY TV REMOTE FOOTAGE (for DELIVERY & COPY from)"

# DB path folder pattern
photo_pattern = re.compile(
    r"/►CUNY TV REMOTE FOOTAGE \(for DELIVERY & COPY from\)"
    r"/►[^/]+"
    r"/PHOTOS"
    r"/(\d{4}\.\d{2}\.\d{2}[^/]+)"
)

# Specify local directory for downloads
local_directory = "/Volumes/CUNYTVMEDIA/archive_projects/Photos"
#local_directory = "/Users/aidagarrido/Downloads/Photos"

# Initialize dictionary
folders_dict = {}

# Get local download path from db path ... /Remote/Show/Photos/Date/file.jpg -> RootLocalDir/Show/Date/file.jpg
def get_file_download_path(f):
    parts = f.strip("/").split("/")
    selected_parts = [parts[1], parts[3], parts[4]]
    relative_path = os.path.join(*selected_parts)
    full_path = os.path.join(local_directory, relative_path)
    full_path = full_path.replace('►', '')

    dir_path = os.path.dirname(full_path)
    os.makedirs(dir_path, exist_ok=True)

    return full_path

lp = longpoll.LongPoll()
r = lp.list_folder(db_path)

while r["has_more"]:
    cursor = (r['cursor'])
    r = lp.list_changes(cursor)
    if not r:
        break;
    if r and 'entries' in r and r['entries']:
        for entry in r['entries']:
            if entry['.tag'] == 'file':
                db_dir = os.path.dirname(entry['path_display'])
                if photo_pattern.fullmatch(db_dir):
                    download_path = get_file_download_path(entry['path_display'])
                    print(f"Downloading file: {entry['path_display']}")
                    if not os.path.exists(download_path):
                        lp.download(entry['path_display'], download_path)
                    if db_dir not in folders_dict:
                        s_link = lp.get_shared_link(db_dir)
                        if s_link:
                            s_link = s_link.split("&")[0]
                            print(s_link)
                            folders_dict[db_dir] = {"old_names": [], "share_link": s_link, "files": [entry['path_display']]}
                    else:
                        folders_dict[db_dir]['files'].append(entry['path_display'])

home_dir = os.path.expanduser('~')

json_path = os.path.join(home_dir, 'Documents', 'photo_share_links.json')
with open(json_path, "w") as f:
    json.dump(folders_dict, f)
#!/usr/bin/env python3

"""
    restructure.py reorganizes files from an XQD card into an organized package. To be expanded
    to handle other card formats
    Last Revised: 2023-04-25
"""

import subprocess
import sys
import os
import shutil 

# drag in your package

try:
    rawpackage = sys.argv[1]
except IndexError:
    print(f'usage: restructurerawfootage.py [package]')

### check for an objects folder ###

### handling of multiple cards ###

objectsdir = os.path.join(rawpackage, "objects")

# if not os.path.exists(objectsdir):
#     os.mkdir(objectsdir)
# else: 
#     print(f'{rawpackage}/objects already exists')

# create a camera logs metadata directory

camera_log_path_xdroot = os.path.join(rawpackage, "metadata/logs/camera/XDROOT")

camera_log_path_clip = os.path.join(rawpackage, "metadata/logs/camera/XDROOT/Clip")


if not os.path.exists(camera_log_path_clip):
    os.makedirs(camera_log_path_clip)
    print(f'creating a folder called metadata/logs/camera_log_path_xdroot')
else:
    print(f' metadata/logs/camera/XDROOT/clip already exists')

# Move camera logs into a metadata/logs/camera folder

for root, dirs, files in os.walk(rawpackage, topdown=False):

    for name in files:
        file_name = os.path.join(root, name)

        searchstring_cueup = 'CUEUP.XML'
        searchstring_discmeta = 'DISCMETA.XML'
        searchstring_mediapro = 'MEDIAPRO.XML'

        if searchstring_cueup in file_name:
            try:
                shutil.move(file_name, camera_log_path_xdroot)
            except shutil.Error:
                continue
        
        if searchstring_discmeta in file_name:
            try:
                shutil.move(file_name, camera_log_path_xdroot)
            except shutil.Error:
                continue
    
        if searchstring_mediapro in file_name:
            try:
                shutil.move(file_name, camera_log_path_xdroot)
            except shutil.Error:
                continue

        if file_name.endswith('.BIM'):
            try:
                shutil.move(file_name, camera_log_path_clip)
            except shutil.Error:
                continue
        
        searchstring_clip = 'Clip' 

        if searchstring_clip in file_name:
            if file_name.endswith('.XML'):
                try:
                    shutil.move(file_name, camera_log_path_clip)
                except shutil.Error:
                    continue

# Delete empty folders

for root, dirs, files in os.walk(rawpackage, topdown=False):

    for empty in dirs:
        if len(os.listdir(os.path.join(root, empty))) == 0:
            os.rmdir(os.path.join(root, empty))
        else:
            print(f'{(os.path.join(root,empty))} is not empty. These will not be removed')


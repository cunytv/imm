#!/usr/bin/env python3

"""
    restructure.py reorganizes files from an XQD card into an organized package.
    Last Revised: 2023-04-20
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


#### handling empty folders ######

# creating a camera logs metadata directory

camera_log_path_xdroot = os.path.join(rawpackage, "metadata/logs/camera/XDROOT")

camera_log_path_clip = os.path.join(rawpackage, "metadata/logs/camera/XDROOT/Clip")


if not os.path.exists(camera_log_path_clip):
    os.makedirs(camera_log_path_clip)
    print(f'creating a folder called metadata/logs/camera_log_path_xdroot')
else:
    print(f' metadata/logs/camera/XDROOT/clip already exists')

# moving metadata camera files into a logs folder

for root, dirs, files in os.walk(rawpackage):
    for name in files:
        file_name = os.path.join(root, name)
        #print(file_name)

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

         

         


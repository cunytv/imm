#!/usr/bin/env python3

"""
    studiochecksum.py takes the studio folder directory, creates and objects folder and then checksums the files. 
    Last Revised: 1/4/2023
"""

import sys
import os
import shutil
import subprocess


try:
    root_dir = sys.argv[1]
except IndexError:
    print(f'usage: studiochecksump.y [folder]')
    exit()

        
for file in os.listdir(root_dir):
    
    path = os.path.join(root_dir, file)
    
    objects_directory = os.path.join(path, r"objects")
    
    if not os.path.exists(objects_directory):
        try: 
            os.mkdir(objects_directory)
        except NotADirectoryError:
            continue
            
    metadata_directory = os.path.join(path, r"metadata")
    
    if os.path.exists(metadata_directory):
        print(f'these files already have checksums')
        exit

    for file in os.listdir(path):
        directory = os.path.join(path, file)

        searchstring = 'Line'
        searchstring2 = 'ISO'

        if searchstring in directory:
            try:
                shutil.move(directory, objects_directory)
            except shutil.Error:
                continue
                
        if searchstring2 in directory:
            try:
                shutil.move(directory, objects_directory)
            except shutil.Error:
                continue
                
    checksum = subprocess.check_output(['checksumpackage', path])


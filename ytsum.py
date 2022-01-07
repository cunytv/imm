#!/usr/bin/env python3

"""
    ystum.py takes a csv file with youtubeids and outputs a csv file onto your desktop with  
    metadata about the youtube upload. 
    Last Revised: 9/28/2021
"""

import subprocess  
import csv
import sys
import os
import time

try: 
    reader = csv.reader(open(sys.argv[1]))
except IndexError:
    print(f'usage: ytsum.py [input.csv]')
    exit()

next(reader)

filepath = os.path.join(os.getenv("HOME"), r"Desktop/youtubesummary_")

timestr = time.strftime("%Y%m%d-%H%M%S")

extension = ".csv"

filename = filepath + timestr + extension

print(f'Your Youtube summary report can be found here: {filename}')
print()
with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(['MediaID', 'YouTubeID', 'Title', 'Extension', 'Size', 'Resolution', 'Frame Rate', 'Captions'])

for line in reader:
    
    youtubeid=(line[1])

    mediaid=(line[0])
    
    title=(line[2])
    
    if youtubeid == '':
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            rows2 = [mediaid, youtubeid, title]
            writer.writerow(rows2) 
        continue
                
    try:
        videoinfo = subprocess.check_output(['youtube-dl', '--list-formats', '--skip-download','--', youtubeid])
    
        videoinfosplit = videoinfo.splitlines()
        videolastline = (videoinfosplit[-1])
        videolastline = videolastline.decode()
    
        videosep = videolastline.split()
        filetype = videosep[1]
        size = videosep[2]
        resolution = videosep[3]
        fps = videosep[7]
    except subprocess.CalledProcessError:
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            rows2 = [mediaid, youtubeid]
            writer.writerow(rows2)
        print(f'{youtubeid} is unavailable')
        continue
    
    subtitles = subprocess.check_output(['youtube-dl', '--skip-download', '--list-subs','--', youtubeid])

    splitsub = subtitles.splitlines()
    subtitles = (splitsub[-1])
    subtitles = subtitles.decode()
    
    if subtitles.startswith(youtubeid):
        subtitles = ''
        
    rows = [mediaid, youtubeid, title, filetype, size, resolution, fps, subtitles]

    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(rows)

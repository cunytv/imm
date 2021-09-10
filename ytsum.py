#!/usr/bin/env python


import subprocess  
import csv
import youtube_dl
import sys
import os
#from datetime import datetime
import time


reader = csv.reader(open(sys.argv[1]))

next(reader)


#date = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")
#print(date)

timestr = time.strftime("%Y%m%d-%H%M%S")
print(timestr)

filename = os.path.join(os.getenv("HOME"), r"Desktop/youtubesummary_{timestr}.csv")
print(f'Your Youtube summary report can be found here: {filename}')
print()
with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(['MediaID', 'YouTubeID', 'Video', 'Captions'])

for line in reader:
    
    youtubeid=(line[1])

    mediaid=(line[0])

    
    size = subprocess.check_output(['youtube-dl', '--list-formats', '--skip-download', youtubeid])
    
    splitvideo = size.splitlines()
    videosize = (splitvideo[-1])
    videosize = videosize.decode()
    print(f'Video information for {mediaid} {youtubeid}:    {videosize}')
    
    subtitles = subprocess.check_output(['youtube-dl', '--skip-download', '--list-subs', youtubeid])

    splitsub = subtitles.splitlines()
    subtitles = (splitsub[-1])
    subtitles = subtitles.decode()
    print(f'Caption information for {mediaid} {youtubeid}:    {subtitles}')

    
    rows = [mediaid, youtubeid, videosize, subtitles]

    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(rows)

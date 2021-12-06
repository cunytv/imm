#!/usr/bin/env python3

"""
    mastercleanup.py takes a csv file and removes the mediaids listed in that file. Used to 
    keep track of what files have been captioned and made accessible.
"""

import subprocess
import sys
import csv
from datetime import datetime
import datetime

# Open upload file and get a unique set of ids
try:
    toremove_csv = csv.DictReader(open(sys.argv[1],'r'))
except IndexError:
    print(f'Drag in csv list of files you would like to remove from master youtube summary file.')
toremove = set(i.get('MediaID') for i in toremove_csv)

#print(toremove)
# Open master file and only retain the data not in the set
master_csv = csv.DictReader(open('youtubesummary_MASTER.csv','r'))
master = [i for i in master_csv if i.get('MediaID') not in toremove]
#print(master)

#Overwrite master file with the new results
filename = 'youtubesummary_captioned_files_removed ' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S.csv")
with open(filename,'w') as file:
    writer = csv.DictWriter(file, master[0].keys(), lineterminator='\n')
    writer.writeheader()
    writer.writerows(master)
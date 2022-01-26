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

# drag in the master csv file followed by csv listing mediaids you would like removed. 
try:
    master_csv = csv.DictReader(open(sys.argv[1],'r'))
except IndexError:
    print(f'Usage: Drag in your master csv file, followed by a csv of the MediaIds you would like removed [master csv file] [csv file with mediaids to remove]')
toremove_csv = csv.DictReader(open(sys.argv[2],'r'))

# finds the mediaids
toremove = set(i.get('MediaID') for i in toremove_csv)

# removes the mediaids from the master file
master = [i for i in master_csv if i.get('MediaID') not in toremove]

# create a new file after removing ids. 
filename = 'youtubesummary_ids_removed ' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S.csv")
with open(filename,'w') as file:
    writer = csv.DictWriter(file, master[0].keys(), lineterminator='\n')
    writer.writeheader()
    writer.writerows(master)
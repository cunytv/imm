# imm

## Introduction

Internal Media Microservices

This collection of scripts, microservices, and documentation supplements the CUNY TV library's public microservice collection that's under development at https://github.com/mediamicroservices/mm. Note that the CUNY TV library also makes regular use of other collaborative repositories such as https://github.com/amiaopensource/vrecord and https://github.com/amiaopensource/ltopers.

## Contents

### bxf2pb

A custom translator to convert BXF scheduling metadata to a proprietary XML format developed by Pebble Beach. The translator incorporates may customizations to optimization exchanges of scheduling metadata within CUNY TV.

### storagereport

`storagereport` is a bash script that assesses online and offline file collections, as well as ProTrack records, lto inventories, and scheduling data in order to guide file migration and retention in a broadcast environment. 

###youtube delivery
####ftpscan
This script is intended to scan a folder for newly uploaded files and then upload those files to youtube automatically. To enable a show to be automatically uploaded, you need to add that prefix to the script. To do this, ssh to archivesx@10.10.200.28. Then type in terminal: nano /usr/local/bin/ftpscan. Scroll down to the list of prefixes and edit or add a prefix. Exit out of nano and answer yes to save. Then press enter. After you edit this, you then need to edit the bash script as well. Then commit your changes in github. 

#!/bin/bash
#This script is used to clean up files that are more than 60 daysold from the studio folder on the XSan Video. 

Cleanupdir="/Volumes/XsanVideo/Camera Card Delivery"
find "$Cleanupdir" -type f -mtime +60d ! -path "*To_Remove*" ! -path "*To_Retain*"| while read file ; do
    movedir=$(dirname "$file" | sed "s|${Cleanupdir}|${Cleanupdir}/To_Remove|g")
    mkdir -p "$movedir/"
    mv -v -n "$file" "$movedir/"
done

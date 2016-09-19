#!/bin/bash
#Clean up 
# Used to clean up files that are more than a month old

Cleanupdir="$1"
find "$Cleanupdir" -type f -mtime +30d -path "*Line_Cut*" ! -path "*Line_Cuts_to_archive*" ! -path "*ISOs_to_delete*"| while read file ; do
    movedir=$(dirname "$file" | sed "s|${Cleanupdir}|${Cleanupdir}/Line_Cuts_to_archive|g")
    mkdir -p "$movedir/"
    mv -v -n "$file" "$movedir/"
done
find "$Cleanupdir" -type f -mtime +30d -path "*ISOs*" ! -path "*ISOs_to_delete*" ! -path "*Line_Cuts_to_archive*"| while read file ; do
    movedir=$(dirname "$file" | sed "s|${Cleanupdir}|${Cleanupdir}/ISOs_to_delete|g")
    mkdir -p "$movedir/"
    mv -v -n "$file" "$movedir/"
done
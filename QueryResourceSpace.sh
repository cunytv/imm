#!/bin/bash

#this script will query resourcespace and ask if a particular file has already been added. If not, 

SCRIPTDIR=$(dirname $(which "${0}"))
. "${SCRIPTDIR}/mmfunctions" || { echo "Missing '${SCRIPTDIR}/mmfunctions'. Exiting." ; exit 1 ;};
REPORTDATE=$(date '+%F')

#ID list is the list of everything on the omneon that belongs to CUNY TV
if [ -d "${1}" ] ; then
	IDLIST=/tmp/querylist.txt
	find "${1}" -type f -mindepth 1 -maxdepth 1 > /tmp/querylist.txt
else
	IDLIST="/Volumes/archivesx/Desktop/REPORTS/${REPORTDATE}/omneon/what_is_on_the_omneon_ids_only_cunytv_only.txt"	
fi

#location of delivery folder
PREPDIR="/Volumes/CUNYTV_Media/archive_projects/PREPPED/"

if [ ! -d "${PREPDIR}" ] ; then
    _report -wt "Error: the delivery folder is not loaded! "
    exit 1
fi

if [ ! -f "${IDLIST}" ] ; then
    _report -wt "Error: I'm not able to load and read the list of IDs on the omneon!"
    exit 1
fi



#comparing the IDs of everything on the omneon to what has been uploaded so far into resource space
while read ID <&3
do
	if [ -d "${1}" ] ; then
		ROOTNAME=$(basename "${ID%.*}")
	else
		ROOTNAME="${ID}"
	fi
	echo -n "Working on ${ROOTNAME}"
	RESULTS="$(curl "http://10.10.200.28/fmi/xml/FMPXMLRESULT.xml?-db=CUNY_TV_archive&-lay=resource_data&-find&resource_type_field=51&value=${ROOTNAME}" 2>/dev/null | xml sel -T -t -m _:FMPXMLRESULT/_:RESULTSET -v @FOUND -n 2>/dev/null)"
	echo "  and found ${RESULTS} records in resourcespace."
    #if the result is 1, the item has been uploaded into resource space. If the result is 0, the file must be transcoded and uploaded to resource space
    if [ "${RESULTS}" == 0 ] ; then
		if [ -d "${1}" ] ; then
			FILELOCATION="${ID}"
		else
	        FILELOCATION=$(grep "clip.dir/${ROOTNAME}.m" "/Volumes/archivesx/Desktop/REPORTS/${REPORTDATE}/omneon/what_is_on_the_omneon_stat.txt" | head -n 1 | cut -d " " -f 7)
		fi
		_report -dt "Encoding ${FILELOCATION}"
        if [ -s "${FILELOCATION}" ] ; then 
            makeresourcespace -o "${PREPDIR}" "${FILELOCATION}"
        fi
    fi
done 3< "${IDLIST}"
rm -v /tmp/querylist.txt

#!/bin/bash

#this script will query resourcespace and ask if a particular file has already been added. If not, 

SCRIPTDIR=$(dirname $(which "${0}"))
. "${SCRIPTDIR}/mmfunctions" || { echo "Missing '${SCRIPTDIR}/mmfunctions'. Exiting." ; exit 1 ;};
CONF_FILE="${SCRIPTDIR}/pbpro.conf"
. "${CONF_FILE}" || { echo "Missing ${CONF_FILE}. Exiting." ; exit 1 ;};

REPORTDATE=$(date '+%F')

_maketemp(){
    mktemp -q "/tmp/$(basename "${0}").XXXXXX"
    if [ "${?}" -ne 0 ]; then
        echo "${0}: Can't create temp file, exiting..."
        _writeerrorlog "_maketemp" "was unable to create the temp file, so the script had to exit."
        exit 1
    fi
}

#ID list is the list of everything on the omneon that belongs to CUNY TV
if [ -d "${1}" ] ; then
    IDLIST=$(_maketemp)
    find "${1}" -type f -mindepth 1 -maxdepth 1 > "${IDLIST}"
elif [ -f "${HOME}/Desktop/REPORTS/${REPORTDATE}/omneon/what_is_on_the_omneon_ids_only_cunytv_only.txt" ] ; then
    IDLIST="${HOME}/Desktop/REPORTS/${REPORTDATE}/omneon/what_is_on_the_omneon_ids_only_cunytv_only.txt"
    STATLIST="${HOME}/Desktop/REPORTS/${REPORTDATE}/internal/what_is_on_the_omneon_stat.txt"
elif [ -f "/Volumes/archivesx/Desktop/REPORTS/${REPORTDATE}/omneon/what_is_on_the_omneon_ids_only_cunytv_only.txt" ] ; then
    IDLIST="/Volumes/archivesx/Desktop/REPORTS/${REPORTDATE}/omneon/what_is_on_the_omneon_ids_only_cunytv_only.txt"
    STATLIST="/Volumes/archivesx/Desktop/REPORTS/${REPORTDATE}/internal/what_is_on_the_omneon_stat.txt"
elif [ ! -f "${IDLIST}" ] ; then
    _report -wt "Error: I'm not able to load and read the list of IDs on the omneon!"
    exit 1
fi

#location of delivery folders
PREPDIR="/Volumes/CUNYTV_Media/archive_projects/filestore/PREPPED/"
PREPPING="/Volumes/CUNYTV_Media/archive_projects/filestore/PREPPING/"

if [ ! -d "${PREPDIR}" ] ; then
    _report -wt "Error: the delivery folder is not loaded! "
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
    RESULTS="$(mysql -BNr -h "${RESOURCESPACE_DB_HOST}" -u "${RESOURCESPACE_DB_USER}" -p"${RESOURCESPACE_DB_PW}" -D "${RESOURCESPACE_DB_NAME}" -e "SELECT COUNT(resource) FROM resource_data WHERE resource_type_field=8 and value='${ROOTNAME}' ;")"
    echo "  and found ${RESULTS} records in resourcespace."
    #if the result is 1, the item has been uploaded into resource space. If the result is 0, the file must be transcoded and uploaded to resource space
    if [ "${RESULTS}" == 0 ] ; then
        if [ -d "${1}" ] ; then
            FILELOCATION="${ID}"
        else
            FILELOCATION=$(grep "clip.dir/${ROOTNAME}.m" "$STATLIST" | head -n 1 | cut -d " " -f 7)
        fi
        _report -dt "Encoding ${FILELOCATION}"
        if [ -s "${FILELOCATION}" ] ; then 
            makeresourcespace -o "${PREPPING}" "${FILELOCATION}"
            #modify permissions and move file to different directory
            chmod 777 "${PREPPING}/${ROOTNAME}.mp4"
            mv -n -v "${PREPPING}/${ROOTNAME}.mp4" "${PREPDIR}"
        fi
    fi
done 3< "${IDLIST}"
if [ -f "${IDLIST}" ] ; then
    rm -v "${IDLIST}"
fi

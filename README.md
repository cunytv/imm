# imm

## Introduction

Internal Media Microservices

This collection of scripts, microservices, and documentation supplements the CUNY TV library's public microservice collection that's under development at https://github.com/mediamicroservices/mm. Note that the CUNY TV library also makes regular use of other collaborative repositories such as https://github.com/amiaopensource/vrecord and https://github.com/amiaopensource/ltopers.

## Contents

### bxf2pb

A custom translator to convert BXF scheduling metadata to a proprietary XML format developed by Pebble Beach. The translator incorporates may customizations to optimization exchanges of scheduling metadata within CUNY TV.

### storagereport

`storagereport` is a bash script that assesses online and offline file collections, as well as ProTrack records, lto inventories, and scheduling data in order to guide file migration and retention in a broadcast environment. 

### youtube delivery
#### ftpscan
This script is intended to scan a folder for newly uploaded files and then upload those files to youtube automatically. To enable a show to be automatically uploaded, you need to add that prefix to the script. To do this, ssh to archivesx@10.10.200.28. Then type in terminal: nano /usr/local/bin/ftpscan. Scroll down to the list of prefixes and edit or add a prefix. Exit out of nano and answer yes to save. Then press enter. After you edit this, you then need to edit the bash script as well. Then commit your changes in github. 

### ingestremote.py
August 27, 2025

Field footage is brought to the library by videographers on XQD cards (most common), solid state drives (radio recordings), SXS cards. and iPhones. 

The script is designed to handle multiple volumes that are mounted at the same time, as well as multiple volumes that need to be mounted sequentially (in the event the number of cards from a shoot exceed the number of card readers).

The ingest processs:

1. Transfers media to the desktop in archival package format
2. Runs makewindow, makemetadata, and makechecksumpackage on that package
3. Transfers the archival package to CUNYTVMEDIA
4. Tranfers the delivery package to TIGERVOLUME
5. Uploads delivery package to Dropbox (and notifies library and any designated recipients)
6. Uploads the windowdub to Resourcespace
7. Sends email report to library in the event of errors
8. Fixity check is run at every point where file is transferred

<img width="1174" height="182" alt="image" src="https://github.com/user-attachments/assets/0de25cf6-d3cd-4fc2-8364-fff7b7c01190" />

The package names follow this format:
- SHOWCODEYYYYMMDD_DESCRIPTION_OF_SHOOT
- LTNS20250827_TINABETH_TOSSES

The files from cards/drives are nested in subfolders that are named after the physical labels on the cards/drives:
- L14
- 235
- CAM_4

An archival package bifurcates audiovisual media and metadata. It is structured in this way:
- PACKAGENAME -> "objects" -> CARD# -> media
- PACKAGENAME -> "metadata" -> "logs" -> CARD# -> metadata

The ingest process comprises the following scripts. Some the helper scripts can be helpful for other coding projects:

[#### ingestremote.py]

This script is a initializes the programs and primarily calls other scripts to do the bulk of the process.

[#### detectrecentlyinserteddrives.py]

A helper script that detects drives that were mounted in the past minute. This short time window is so that you can prompt parallel ingests for different packages.

[#### cunymediaids.py]

A helper script that lists show names and their show codes. It includes functions print_media_dict, check_similarity($string) ((should be renamed find_best_match)), and get_full_show_name($code).

[#### validateuserinput.py]

A helper script that the sanitizes* and/or validates:
- Package names*
- Card names*
- Emails
- File paths

* Sanitize = all capitals and spaces replaced by underscores

[#### sendnetworkmail.py]

A class that simplifies sending network emails. This only works when sending emails to tv.cuny.edu addresses.

email = SendNetworkEmail()
email.sender($string)
email.recipients([array])
email.subject($string)
email.html_content($string)
email.attachment($file_path)
email.embed_img($img_path)
email.send()

[#### detectiphone.py]

Detects mounted iphone using command line. 

[#### downloadlatestiphonemedia.scpt (BETA)]

Recording on iPhone has become increasingly common. The problem is that these devices don't mount like volumes and are not programatically accessible. 

There was a open source project called libimobiledevice which reverse-engineered apple protocals, but has stopped working since iOS ~10.

The Apple application ImageCapture used to have an API, but that has been deprecated around 2022-2024, macOS Ventura/Sonoma/Sequoia.

As a short term solution, this is an AppleScript which controls ImageCapture through its UI. It's awkward, and may not work well. This was coded with the assistance of UI Browser, since Apple has also deprecated the AppleScript dictionary for ImageCapture.

The script downloads the latest photo/video and downloads all other photos/videos from the same date to an intermediary location in the Pictures/Iphone_Ingest_Temp folder. 

[#### restructurepackage.py]

[#### dropboxuploadsession.py]

[#### remote_resource_space_ingest.php]










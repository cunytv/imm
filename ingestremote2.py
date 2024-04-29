#!/usr/bin/env python3

import detectrecentlyinserteddrives
import restructurepackage
import ingestcommands
import validateuserinput
import dropboxuploadsession
import sendnetworkmail
import re
import sys
import os
import subprocess

# Checks if user is connected to server
def server_check():
    if not os.path.exists(server):
        print(f'You might not be connected to the server. Reconnect and try again')
        sys.exit(1)

# Creates dropbox upload prefix by concatenating scoped folder with show code
def dropbox_prefix(s):
    # Split string at first underscore
    s = s.split('_', 1)[0]

    # Find string before first digit
    match = re.search(r'\d', s)
    if match:
        showcode = s[:match.start()]
    else:
        showcode = s

    # Dropbox path
    if showcode:
        return f'/_CUNY TV CAMERA CARD DELIVERY/{showcode}'
    else:
        return '/_CUNY TV CAMERA CARD DELIVERY/NOSHOW'


# Ingests files
def ingest():
    # 1. Transfer files to server
    for package in packages_dict:
        # Create package object from RestructurePackage class
        package_obj = restructurepackage.RestructurePackage()
        for card, input_path in zip(packages_dict[package]["cards"], packages_dict[package]["input_paths"]):
            package_obj.create_output_directory(server, package, card)
            package_obj.restructure_folder(input_path, server, package, card, packages_dict[package]["do_fixity"], packages_dict[package]["do_delete"])
            eject(input_path)
        packages_dict[package]["files_dict"] = package_obj.FILES_DICT
        packages_dict[package]["transfer_okay"] = package_obj.TRANSFER_OKAY

    # 2. Perform ingest scripts on successfully transferred packages
    for package in packages_dict:
        # Run makewindow on succesfully transferred packages
        if packages_dict[package]["transfer_okay"] and packages_dict[package]["do_commands"]:
            makewindow_okay, makewindow_error = ingestcommands.makewindow(os.path.join(server, package_name))
        else:
            packages_dict[package]["makewindow_okay"] = None
            packages_dict[package]["makemetadata_okay"] = None
            packages_dict[package]["makechecksumpackage_okay"] = None
            continue

        # Run makemetadata on package if makewindow was successfully run
        packages_dict[package]["makewindow_okay"] = makewindow_okay
        if makewindow_okay:
            makemetadata_okay, makemetadata_error = ingestcommands.makemetadata(os.path.join(server, package_name))
        else:
            packages_dict[package]["makewindow_error"] = makewindow_error
            packages_dict[package]["makemetadata_okay"] = None
            packages_dict[package]["makechecksumpackage_okay"] = None
            continue

        # Run makechecksum on package if makemetadata was successfully run
        packages_dict[package]["makemetadata_okay"] = makemetadata_okay
        if makemetadata_okay:
            makechecksumpackage_okay, makechecksumpackage_error = ingestcommands.makechecksumpackage(os.path.join(server, package_name))
        else:
            packages_dict[package]["makemetadata_error"] = makemetadata_error
            packages_dict[package]["makechecksumpackage_okay"] = None
            continue

        packages_dict[package]["makechecksumpackage_okay"] = makechecksumpackage_okay
        if not makechecksumpackage_okay:
            packages_dict[package]["makechecksumpackage_error"] = makechecksumpackage_error

    # 3. Upload packages that have at successfully transferred and went through makewindow, and send email notification
    for package in packages_dict:
        if packages_dict[package]["emails"] and packages_dict[package]["transfer_okay"] and (packages_dict[package]["makewindow_okay"] or packages_dict[package]["makewindow_okay"] is None):
            dropbox_directory = dropbox_prefix(package) + f'/{package}'
            server_object_directory = os.path.join(server, package) + "/objects"
            emails = packages_dict[package]["emails"]

            uploadsession = dropboxuploadsession.DropboxUploadSession(server_object_directory)

            for root, directories, files in os.walk(server_object_directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    dropboxpath = dropbox_directory + f"/{filename}"
                    uploadsession.upload_file_to_dropbox(filepath, dropboxpath)
                    uploadsession.share_link = uploadsession.get_shared_link(dropbox_directory)[0]

            notification = sendnetworkmail.SendNetworkEmail()
            notification.sender("library@tv.cuny.edu")
            notification.recipients(emails)
            notification.subject(f"Dropbox Upload: {package}")

            # Write text content with HTML formatting
            html_content = f"""
            <html>
              <body>
                <p>Hello, </p>
                <p></p>
                <p>See the link below: </p>
                <p><a href="{uploadsession.share_link}">{uploadsession.share_link}</a>.</p>
                <p>Best, </p>
                <p>Library Bot</p>
              </body>
            </html>
            """

            notification.content(html_content)
            notification.send()


# Ejects mounted drive
def eject(path):
    subprocess.run(["diskutil", "eject", path])
    notification(f"{path} ejected. Safe to remove.")

# Sends onscreen notification
def notification(message):
    applescript = f'''
            display notification "{message}" with title "Ingest Notification"
        '''
    subprocess.run(["osascript", "-e", applescript])

if __name__ == "__main__":
    # Create dictionary of packages
    # Follows the format of Package Name {[cards], [input paths], do_fixity boolean, do_delete boolean, do_commands boolean, {file dictionary}, transfer_okay boolean}
    packages_dict = {}

    # Check if connected to server
    #server = "/Volumes/CUNYTV_Media/archive_projects/sxs_ingests-unique"
    #server_check()
    server = "/Users/archivesx/Desktop"

    # Detect recently inserted drives and cards
    volume_paths = detectrecentlyinserteddrives.volume_paths()

    # Organizes user inputs into dictionary
    if not volume_paths:
        print("No cards detected")
    else:
        print(f"{len(volume_paths)} card(s) detected")

        for input_path in volume_paths:
            print(f"- {input_path}")

            package_name = validateuserinput.card_package_name(input(f"\tEnter a package name: "))
            camera_card_number = validateuserinput.card_subfolder_name(input(f"\tEnter the corresponding card number or name on sticker (serialize from 1 if none): "))

            if package_name not in packages_dict:
                # Additional file processing options
                do_fixity = (input("\tFixity check before and after transfer? y/n: ")).lower() == 'y'
                #do_delete = (input("\tDelete original files after successful transfer? y/n: ")).lower() == 'y'
                do_delete = False
                do_commands = (input("\tRun makewindow, makemetdata, checksumpackage? y/n: ")).lower() == 'y'
                do_dropbox = (input("\tUpload to dropbox? y/n: ")).lower() == 'y'
                emails = []
                if do_dropbox:
                    emails = validateuserinput.emails(input("\tList email(s) delimited by space or press enter to continue: "))
                    emails.extend(["library@tv.cuny.edu"])

                # Create key-value pair
                packages_dict[package_name] = {
                    "cards": [camera_card_number],
                    "input_paths": [input_path],
                    "do_fixity": do_fixity,
                    "do_delete": do_delete,
                    "do_commands": do_commands,
                    "emails": emails
                }

            else:
                # Edit existing key-value pair
                packages_dict[package_name]["cards"].append(camera_card_number)
                packages_dict[package_name]["input_paths"].append(input_path)

        # Begin ingest
        ingest()

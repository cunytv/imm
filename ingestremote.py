#!/usr/bin/env python3

import detectrecentlyinserteddrives
import restructurepackage
import ingestcommands
import validateuserinput
import dropboxuploadsession
import cunymediaids
from dropboxuploadsession import DropboxUploadSession
import sendnetworkmail
import re
import sys
import os
import subprocess
import time
import shutil
import json


# Checks if user is connected to server
def server_check(s):
    if not os.path.exists(s):
        print(f'{s} not found. You might not be connected to the server. Reconnect and try again')
        sys.exit(1)


# Timer, used as buffer between mounting of hard drive and start of program
def countdown(seconds):
    for i in range(seconds, 0, -1):
        print(i, end='...', flush=True)
        time.sleep(1)
    print()


# Prints first ten filenames in a directory
def print_first_ten_filenames(src_dir):
    file_count = 0  # Counter for files found
    filenames = []  # List to store the filenames

    # Traverse the source directory
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            filenames.append(file)  # Add the filename to the list
            file_count += 1

            if file_count >= 10:  # Stop after collecting 5 files
                break
        if file_count >= 10:  # Break the outer loop as well
            break

    if filenames:
        print("...".join(filenames))  # Print the filenames joined by semicolons
    else:
        print("No files found in the directory.")


# Checks if file is mac system metadata
def mac_system_metadata(file):
    if '.' not in file or file.startswith('.'):
        return True


# Extracts showcode from package name string
def get_showcode(input_string):
    # Split at first underescore
    input_string = input_string.split('_', 1)[0]  # Max split of 1

    # Search for the first digit in the string
    match = re.search(r'(\d)', input_string)

    if not match:
        # No numbers found, return the whole string
        return input_string.strip()

    # If a number is found, get the position of the first digit
    first_number_index = match.start()

    # Extract the substring before the first number
    substring = input_string[:first_number_index].strip()

    if substring:  # If there's something before the number
        return substring
    else:  # If there's nothing before the first number
        return "NOSHOW"


# Creates dropbox upload prefix by concatenating scoped folder with show code
def dropbox_prefix(s):
    showcode = get_showcode(s)
    return f'/_CUNY TV CAMERA CARD DELIVERY/{showcode}'


def XSAN_access_transfer(package_obj, package, access_input_path, access_output_path):
    for foldername, subfolders, filenames in os.walk(access_input_path, topdown=False):
        for file in filenames:
            # Construct file path names
            input_path = os.path.join(foldername, file)
            output_path = os.path.join(access_output_path, file)

            # Checksum variables
            cs1 = None
            cs2 = None

            # Create pre-transfer checksum
            if do_fixity:
                cs1 = package_obj.calculate_sha256_checksum(input_path)


            # Transfer file using file_transfer method, which returns boolean upon succesful or unsuccesful transfer
            error, packages_dict[package]['DELIVERY_transfer_okay'] = package_obj.file_transfer(input_path,
                                                                                           output_path)

            if not packages_dict[package]['DELIVERY_transfer_okay']:
                packages_dict[package]['DELIVERY_files_dict'][(input_path, output_path)] = [cs1, cs2, False]
                packages_dict[package]['DELIVERY_transfer_error'] = error
                continue  # Continue to next file on unsuccessful transfer

            # If checksum validation unsuccessful, retry file_transfer method up to 3 times
            max_retries = 3
            retries = 0
            while retries < max_retries:
                if do_fixity:
                    cs2 = package_obj.calculate_sha256_checksum(output_path)
                    if cs1 == cs2:
                        print(f'File {file} transferred and passed fixity check')
                        packages_dict[package]['DELIVERY_files_dict'][(input_path, output_path)] = [cs1, cs2, True]
                        break  # Exit on succesful transfer
                    else:
                        if retries >= max_retries:
                            print(
                                f"Failed to transfer {input_path} after {max_retries} attempts. Moving to the next file.")
                            packages_dict[package]['DELIVERY_files_dict'][(input_path, output_path)] = [cs1, cs2, False]
                            packages_dict[package]['DELIVERY_transfer_okay'] = False
                            packages_dict[package]['DELIVERY_transfer_error'] = 'Fixity check'
                            break  # Exit on max retries

                        print(f'File {file} transferred but did not pass fixity check. Retrying file transfer.')
                        retries += 1
                        os.remove(output_path)
                        error, packages_dict[package]['DELIVERY_transfer_okay'] = package_obj.file_transfer(input_path,
                                                                                                       output_path)

                        if not packages_dict[package]['DELIVERY_transfer_okay']:
                            packages_dict[package]['DELIVERY_files_dict'][(input_path, output_path)] = [cs1, None, False]
                            packages_dict[package]['DELIVERY_transfer_error'] = error
                            break  # Exit on file transfer failure
                else:
                    packages_dict[package]['DELIVERY_files_dict'][(input_path, output_path)] = [cs1, cs2, None]
                    break  # No fixity check, exit loop


def print_log(log_dest, package, packages_dict):
    # Specify the order for printing
    keys_order = [
        'cards',
        'input_paths',
        'do_delete',
        'do_fixity',
        'do_commands',
        'do_dropbox',
        'emails',
        'ARCHIVE_transfer_okay',
        'ARCHIVE_transfer_error',
        'DELIVERY_transfer_okay',
        'DELIVERY_transfer_error',
        'MAKEWINDOW_okay',
        'MAKEWINDOW_error',
        'MAKEMETADATA_okay',
        'MAKEMETADATA_error',
        'MAKECHECKSUMPACKAGE_okay',
        'MAKECHECKSUMPACKAGE_error',
        'DROPBOX_transfer_okay',
        'ARCHIVE_files_dict',
        'DELIVERY_files_dict',
        'DROPBOX_files_dict'
    ]

    with open(log_dest, 'w') as f:
        f.write(f"Contents of '{package}':\n")
        f.write("=" * 30 + "\n")  # Separator line
        for key in keys_order:
            if key in packages_dict[package]:
                value = packages_dict[package][key]
                f.write(f"{key}:\n")

                if isinstance(value, list):
                    for item in value:
                        f.write(f"  - {item}\n")
                elif isinstance(value, dict):
                    f.write(f"Contents of '{key}':\n")
                    f.write("-" * 30 + "\n")  # Separator line
                    for sub_key, sub_value in value.items():
                        f.write(f"{sub_key}:\n")
                        if isinstance(sub_value, list):
                            for item in sub_value:
                                f.write(f"  - {item}\n")
                        elif isinstance(sub_value, dict):
                            for inner_key, inner_value in sub_value.items():
                                f.write(f"  {inner_key}:\n")
                                for val_item in inner_value:
                                    f.write(f"    - {val_item}\n")
                        else:
                            f.write(f"  {sub_value}\n")
                else:
                    f.write(f"  {value}\n")

                f.write("\n")  # Extra newline for spacing

    ato = packages_dict[package]["ARCHIVE_transfer_okay"]
    dto = packages_dict[package]["DELIVERY_transfer_okay"]
    mwo = packages_dict[package]["MAKEWINDOW_okay"]
    mmo = packages_dict[package]["MAKEMETADATA_okay"]
    mcpo = packages_dict[package]["MAKECHECKSUMPACKAGE_okay"]
    dbto = packages_dict[package]["DROPBOX_transfer_okay"]

    if not all([ato, dto, mwo, mmo, mcpo, dbto]):
        notification = sendnetworkmail.SendNetworkEmail()
        notification.sender("library@tv.cuny.edu")
        #notification.recipients(["library@tv.cuny.edu"])
        notification.recipients(["aida.garrido@tv.cuny.edu"])
        notification.subject(f"Ingest error: {package}")

        # Exclude the last three keys
        keys_to_print = keys_order[3:7]
        keys_to_print2 = keys_order[7:-3]

        # Initialize an HTML formatted string for key-value pairs
        html_output = "<div>\n<p>"

        for key in keys_to_print:
            if key in packages_dict[package]:
                value = packages_dict[package].get(key) # Use package-specific dictionary
                keyf = key.lower()
                valuef = str(value).upper()
                html_output += f"  {keyf}: {valuef}<br>\n"

        html_output += "</p>\n<p>"

        for key in keys_to_print2:
            if key in packages_dict[package]:
                value = packages_dict[package].get(key)  # Use package-specific dictionary
                keyf = key.lower()
                valuef = str(value).upper()
                if value == False or "error" in keyf:
                    html_output += f"  <u><strong>{keyf}: {valuef}</strong></u><br>\n"
                else:
                    html_output += f"  {keyf}: {valuef}<br>\n"

        html_output += "</p>\n</div>"

        # Create the main HTML content
        html_content = f"""
                <html>
                  <body>
                    <p>Hello, </p>
                    <p>An error occurred during ingest:</p>
                    <br>
                    {html_output}
                    <br>
                    <p>Check attachment for more information or navigate to {os.path.join(server, package, "metadata", "ingestlog.txt")}</p>
                    <p>Best, </p>
                    <p>Library Bot</p>
                  </body>
                </html>
                """

        # Set notification content
        notification.content(html_content)

        # Specify the attachment path
        attachment_path = os.path.join(server, package, "metadata", "ingestlog.txt")

        # Add the attachment
        notification.attachment(attachment_path)

        # Send the notification
        notification.send()

# Ingests files
def ingest():
    # 1. Transfer files to server
    for package in packages_dict:
        # Create package object from RestructurePackage class
        package_obj = restructurepackage.RestructurePackage(server, package)
        for card, input_path in zip(packages_dict[package]["cards"], packages_dict[package]["input_paths"]):
            package_obj.create_output_directory(server, package, card)
            # Transfer files to CUNYTV_Media
            package_obj.archive_restructure_folder(input_path, server, package, card, packages_dict[package]["do_fixity"],
                                           packages_dict[package]["do_delete"])
            eject(input_path)


        # Save archive transfer results and checksums
        packages_dict[package]["ARCHIVE_files_dict"] = package_obj.ARCHIVE_FILES_DICT
        packages_dict[package]["ARCHIVE_transfer_okay"] = package_obj.ARCHIVE_TRANSFER_OKAY
        if package_obj.ARCHIVE_TRANSFER_ERROR:
            packages_dict[package]["ARCHIVE_transfer_error"] = package_obj.ARCHIVE_TRANSFER_ERROR

        # Transfer files to XSAN
        package_obj.delivery_restructure_folder(os.path.join(server, package, "objects"), os.path.join(server2, get_showcode(package)), package, packages_dict[package]["do_fixity"], packages_dict[package]["ARCHIVE_files_dict"])

        # Save delivery transfer results and checksums
        packages_dict[package]["DELIVERY_files_dict"] = package_obj.DELIVERY_FILES_DICT
        packages_dict[package]["DELIVERY_transfer_okay"] = package_obj.DELIVERY_TRANSFER_OKAY
        if package_obj.DELIVERY_TRANSFER_ERROR:
            packages_dict[package]["DELIVERY_transfer_error"] = package_obj.DELIVERY_TRANSFER_ERROR

        #print
        #print(packages_dict[package])

    # 2. Perform ingest scripts on successfully transferred packages
    for package in packages_dict:
        # Run makewindow on succesfully transferred packages
        if packages_dict[package]["ARCHIVE_transfer_okay"] and packages_dict[package]["do_commands"]:
            makewindow_okay, makewindow_error = ingestcommands.makewindow(os.path.join(server, package_name))
        else:
            packages_dict[package]["MAKEWINDOW_okay"] = None
            packages_dict[package]["MAKEMETADATA_okay"] = None
            packages_dict[package]["MAKECHECKSUMPACKAGE_okay"] = None
            continue

        # Run makemetadata on package if makewindow was successfully run
        packages_dict[package]["MAKEWINDOW_okay"] = makewindow_okay
        if makewindow_okay:
            makemetadata_okay, makemetadata_error = ingestcommands.makemetadata(os.path.join(server, package_name))

            # Transfer access copies to XSAN
            access_input_path = os.path.join(server, package, "objects", "access")
            access_output_path = os.path.join(server2, get_showcode(package), package)
            XSAN_access_transfer(package_obj, package, access_input_path, access_output_path)

        else:
            packages_dict[package]["MAKEWINDOW_error"] = makewindow_error
            packages_dict[package]["MAKEMETADATA_okay"] = None
            packages_dict[package]["MAKECHECKSUMPACKAGE_okay"] = None
            continue

        # Run makechecksum on package if makemetadata was successfully run
        packages_dict[package]["MAKEMETADATA_okay"] = makemetadata_okay
        if makemetadata_okay:
            makechecksumpackage_okay, makechecksumpackage_error = ingestcommands.makechecksumpackage(
                os.path.join(server, package_name))
        else:
            packages_dict[package]["MAKEMETADATA_error"] = makemetadata_error
            packages_dict[package]["MAKECHECKSUMPACKAGE_okay"] = None
            continue

        packages_dict[package]["MAKECHECKSUMPACKAGE_okay"] = makechecksumpackage_okay
        if not makechecksumpackage_okay:
            packages_dict[package]["MAKECHECKSUMPACKAGE_error"] = makechecksumpackage_error

    # 3. Upload to dropbox that have successfully transferred, went through makewindow, and send email notification
    for package in packages_dict:
        do_dropbox = packages_dict[package]["emails"] and packages_dict[package]["ARCHIVE_transfer_okay"] and (
                    packages_dict[package]["MAKEWINDOW_okay"] or packages_dict[package]["MAKEWINDOW_okay"] is None)

        server_object_directory = os.path.join(server2, get_showcode(package), package)
        dropbox_directory = dropbox_prefix(package) + f'/{package}'
        emails = packages_dict[package]["emails"]

        if do_dropbox:
            uploadsession = dropboxuploadsession.DropboxUploadSession(server_object_directory)

            for root, _, files in os.walk(server_object_directory):
                for filename in files:
                    if not mac_system_metadata(filename):
                        filepath = os.path.join(root, filename)
                        dropboxpath = os.path.join(dropbox_directory, filename)

                        try:
                            uploadsession.upload_file_to_dropbox(filepath, dropboxpath, packages_dict[package]["do_fixity"], packages_dict[package]["DELIVERY_files_dict"])
                        except ConnectionError:
                            print("Connection error.")

            packages_dict[package]["DROPBOX_files_dict"] = uploadsession.DROPBOX_FILES_DICT
            packages_dict[package]["DROPBOX_transfer_okay"] = uploadsession.DROPBOX_TRANSFER_OKAY


            # Send email notification if Dropbox transfer goes well.
            if packages_dict[package]["DROPBOX_transfer_okay"]:
                # Bifurcate email type
                cuny_emails = []
                other_emails = []
                if emails:
                    for email in emails:
                        if "@tv.cuny.edu" in email:
                            cuny_emails.append(email)
                        else:
                            other_emails.append(email)

                # Send network email to CUNY recipients
                uploadsession.share_link = uploadsession.get_shared_link(dropbox_directory)[0]
                notification = sendnetworkmail.SendNetworkEmail()
                notification.sender("library@tv.cuny.edu")
                notification.recipients(cuny_emails)
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

                # Send dropbox notification to non-CUNY recipients
                if other_emails is not None:
                    msg = f"{dropbox_directory} has finished uploading."
                    uploadsession.add_folder_member(other_emails, uploadsession.get_shared_folder_id(dropbox_directory),
                                                    False, msg)
        else:
            packages_dict[package]["DROPBOX_files_dict"] = None
            packages_dict[package]["DROPBOX_transfer_okay"] = None


    # 4. Print logs and send email to library in case of errror
    for package in packages_dict:
        # Write dictionary to a text file
        log_dest = os.path.join(server, package, "metadata", "ingestlog.txt" )
        print_log(log_dest, package, packages_dict)

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

    # Check if connected to servers
    #server = "/Volumes/CUNYTV_Media/archive_projects/camera_card_ingests"
    #server_check(server)
    server = "/Users/aidagarrido/Desktop"

    server2 = "/Users/aidagarrido/Desktop/Camera Card Delivery"
    #server2 = "/Volumes/XsanVideo/Camera Card Delivery"
    #server_check(server2)

    # Detect recently inserted drives and cards
    countdown(5)
    volume_paths = detectrecentlyinserteddrives.volume_paths()

    # Organizes user inputs into dictionary
    if not volume_paths:
        print("No cards detected")
    else:
        cunymediaids.print_media_dict()
        print()
        print(f"{len(volume_paths)} card(s) detected")

        for input_path in volume_paths:
            print(f"- {input_path}")
            print_first_ten_filenames(input_path)

            package_name = validateuserinput.card_package_name(input(f"\tEnter a package name: "))
            camera_card_number = validateuserinput.card_subfolder_name(
                input(f"\tEnter the corresponding card number or name on sticker (serialize from 1 if none): "))

            if package_name not in packages_dict:
                # Additional file processing options
                do_fixity = (input("\tFixity check before and after transfer? y/n: ")).lower() == 'y'
                # do_delete = (input("\tDelete original files after successful transfer? y/n: ")).lower() == 'y'
                do_delete = False
                do_commands = (input(
                    "\tRun makewindow, makemetdata, checksumpackage? If ingesting multiple cards, run this command when ingesting the last card. y/n?: ")).lower() == 'y'
                do_dropbox = (input(
                    "\tUpload to dropbox? If ingesting multiple cards, run this command when ingesting the last card. y/n: ")).lower() == 'y'
                emails = []
                if do_dropbox:
                    emails = validateuserinput.emails(
                        input("\tList email(s) delimited by space or press enter to continue: "))
                    #emails.extend(["library@tv.cuny.edu"])
                    emails.extend(["agarrkoch@gmail.com"])
                    # email_input = input("\tList email(s) delimited by space or press enter to continue: ")
                    # emails = validateuserinput.emails(email_input)

                # Create key-value pair
                packages_dict[package_name] = {
                    "cards": [camera_card_number],
                    "input_paths": [input_path],
                    "do_fixity": do_fixity,
                    "do_delete": do_delete,
                    "do_commands": do_commands,
                    "do_dropbox": do_dropbox,
                    "emails": emails
                }

            else:
                # Edit existing key-value pair
                packages_dict[package_name]["cards"].append(camera_card_number)
                packages_dict[package_name]["input_paths"].append(input_path)

        # Begin ingest
        ingest()

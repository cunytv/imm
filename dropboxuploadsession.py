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
from datetime import datetime
import json

# Specify the order for printing
keys_order = [
    'cards',
    'input_paths',
    'do_drive_delete',
    'do_fixity',
    'do_commands',
    'do_dropbox',
    'emails',
    'ARCHIVE_transfer_okay',
    'ARCHIVE_transfer_error',
    'ONE2ONECOPY_transfer_okay',
    'ONE2ONECOPY_transfer_error',
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
    'ONE2ONECOPY_files_dict',
    'DELIVERY_files_dict',
    'DROPBOX_files_dict'
]

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

def append_after_text(log_path, key, package, packages_dict):

    # Step 1: Open the file and read all lines
    with open(log_path, 'r') as file:
        lines = file.readlines()

    # Step 2: Find the line containing 'cards'
    target_index = -1
    for i, line in enumerate(lines):
        if key + ":" in line:  # Case sensitive search, use `.lower()` for case-insensitive
            target_index = i
            break

    if target_index == -1:
        print(f"Error: '{key}:' not found in the file.")
        return

    # Step 3: Find the closest blank line after the target line
    insert_index = target_index + 1
    while insert_index < len(lines) and lines[insert_index].strip() != '':
        insert_index += 1

    # Step 4: Insert the new content after the blank line
    value = packages_dict[package][key]
    if isinstance(value, list):
        for item in value:
            lines.insert(insert_index, f"  - {item}\n")
            insert_index += 1
    elif isinstance(value, dict):
        for sub_key, sub_value in value.items():
            lines.insert(insert_index, f"{sub_key}:\n")
            insert_index += 1
            if isinstance(sub_value, list):
                for item in sub_value:
                    lines.insert(insert_index, f"  - {item}\n")
                    insert_index += 1
            elif isinstance(sub_value, dict):
                for inner_key, inner_value in sub_value.items():
                    lines.insert(insert_index, f"  {inner_key}:\n")
                    insert_index += 1
                    for val_item in inner_value:
                        lines.insert(insert_index, f"    - {val_item}\n")
                        insert_index += 1
            else:
                lines.insert(insert_index, f"  {sub_value}\n")
                insert_index += 1
    else:
        lines.insert(insert_index, f"  {value}\n")
        insert_index += 1

    # Step 5: Write the updated content back to the file
    with open(log_path, 'w') as file:
        file.writelines(lines)


def print_log(log_dest, package, packages_dict):
    log_exists = False
    log_path = ''
    for filename in os.listdir(log_dest):
        # Check if the filename starts with "ingestlog"
        if filename.startswith("ingestlog"):
            log_exists = True
            log_path = os.path.join(log_dest, filename)
            break

    # If part of multi-batch process and not yet last batch
    if log_exists and not packages_dict[package]['do_desktop_delete']:

        # Move existing log to desktop to append values (doesn't work when trying to write directly to server)
        home_dir = os.path.expanduser('~')
        desktop_path = os.path.join(home_dir, 'Desktop')
        desktop_log = os.path.join(desktop_path, f"ingestlog{package}.txt")
        shutil.move(log_path, desktop_log)

        # Update these values
        append_after_text(desktop_log, 'cards', package, packages_dict)
        append_after_text(desktop_log, 'input_paths', package, packages_dict)
        append_after_text(desktop_log, 'ARCHIVE_files_dict', package, packages_dict)

        # Move log back to server; append time to avoid cache issues
        now = datetime.now()
        time_str = now.strftime("%H%M%S")

        shutil.move(desktop_log, os.path.join(server, package, "metadata", f"ingestlog{package}_{time_str}.txt"))

    # If part of multi-batch process and last batch
    elif log_exists and packages_dict[package]['do_desktop_delete']:
        # Move existing log to desktop to append values (doesn't work when trying to write directly to server)
        home_dir = os.path.expanduser('~')
        desktop_path = os.path.join(home_dir, 'Desktop')
        desktop_log = os.path.join(desktop_path, f"ingestlog{package}.txt")
        shutil.move(log_path, desktop_log)

        # Update these values
        append_after_text(desktop_log, 'cards', package, packages_dict)
        append_after_text(desktop_log, 'input_paths', package, packages_dict)
        append_after_text(desktop_log, 'ARCHIVE_files_dict', package, packages_dict)

        # Delete the values between 'do_fixity' and 'ARCHIVE_files_dict'
        with open(desktop_log, 'r') as file:
            lines = file.readlines()

        deleting = False
        filtered_lines = []

        for line in lines:
            # Start deleting from the line containing 'do_fixity'
            if 'do_drive_delete' in line:
                deleting = True

            # If we are deleting, skip the line
            if deleting:
                # If we encounter 'ARCHIVE_files_dict', stop deleting
                if 'ARCHIVE_files_dict' in line:
                    filtered_lines.append(line)  # Include this line to keep it
                    deleting = False
                continue

            # If not deleting, keep the line
            filtered_lines.append(line)

        # Insert the new values after the deletion
        with open(desktop_log, 'w') as file:
            file.writelines(filtered_lines)

        # Now, insert the new values
        with open(desktop_log, 'r') as file:
            lines = file.readlines()

        # Find the target index for insertion
        target_index = -1
        for i, line in enumerate(lines):
            if 'input_paths' + ":" in line:  # Case sensitive search
                target_index = i
                break

        # Calculate the insertion index (next blank line)
        insert_index = target_index + 1
        while insert_index < len(lines) and lines[insert_index].strip() != '':
            insert_index += 1

        # Insert the keys from the dictionary into the file
        for key in keys_order[2:20]:
            if key in packages_dict[package]:
                value = packages_dict[package][key]
                lines.insert(insert_index, f"\n{key}:\n")
                insert_index += 1
                # Step 4: Insert the new content after the blank line
                if isinstance(value, list):
                    for item in value:
                        lines.insert(insert_index, f"  - {item}\n")
                        insert_index += 1
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        lines.insert(insert_index, f"{sub_key}:\n")
                        insert_index += 1
                        if isinstance(sub_value, list):
                            for item in sub_value:
                                lines.insert(insert_index, f"  - {item}\n")
                                insert_index += 1
                        elif isinstance(sub_value, dict):
                            for inner_key, inner_value in sub_value.items():
                                lines.insert(insert_index, f"  {inner_key}:\n")
                                insert_index += 1
                                for val_item in inner_value:
                                    lines.insert(insert_index, f"    - {val_item}\n")
                                    insert_index += 1
                        else:
                            lines.insert(insert_index, f"  {sub_value}\n")
                            insert_index += 1
                else:
                    lines.insert(insert_index, f"  {value}\n")
                    insert_index += 1

        # Write the modified lines (with inserted values) back to the file
        with open(desktop_log, 'w') as file:
            file.writelines(lines)

        # Add these values
        with open(desktop_log, 'a') as f:
            for key in keys_order[-3:]:
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
        # Move log back to server; append time to avoid cache issues
        now = datetime.now()
        time_str = now.strftime("%H%M%S")

        shutil.move(desktop_log, os.path.join(server, package, "metadata", f"ingestlog{package}_{time_str}.txt"))

    # If only batch or first batch
    else:
        # Move log back to server; append time to avoid cache issues
        now = datetime.now()
        time_str = now.strftime("%H%M%S")

        log_path = os.path.join(server, package, "metadata", f"ingestlog{package}_{time_str}.txt")

        with open(log_path, 'w') as f:
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

def error_report(log_dest, package, packages_dict):
    ato = packages_dict[package]["ARCHIVE_transfer_okay"]
    oto = packages_dict[package]["ONE2ONECOPY_transfer_okay"]
    dto = packages_dict[package]["DELIVERY_transfer_okay"]
    mwo = packages_dict[package]["MAKEWINDOW_okay"]
    mmo = packages_dict[package]["MAKEMETADATA_okay"]
    mcpo = packages_dict[package]["MAKECHECKSUMPACKAGE_okay"]
    dbto = packages_dict[package]["DROPBOX_transfer_okay"]

    # Treat None as True
    variables = [v if v is not None else True for v in [ato, oto, dto, mwo, mmo, mcpo, dbto]]

    if not all(variables):
        notification = sendnetworkmail.SendNetworkEmail()
        notification.sender("library@tv.cuny.edu")
        notification.recipients(["library@tv.cuny.edu"])
        #notification.recipients(["aida.garrido@tv.cuny.edu"])
        notification.subject(f"Ingest error: {package}")

        # Exclude the last four keys
        keys_to_print = keys_order[3:7]
        keys_to_print2 = keys_order[7:-4]

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

        log_path = ''
        for filename in os.listdir(log_dest):
            # Check if the filename starts with "ingestlog"
            if filename.startswith("ingestlog"):
                log_path = os.path.join(log_dest, filename)
                break

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
                    <p>Check attachment for more information or navigate to {log_path}</p>
                    <p>Best, </p>
                    <p>Library Bot</p>
                  </body>
                </html>
                """

        # Set notification content
        notification.content(html_content)

        # Add the attachment
        notification.attachment(log_path)

        # Send the notification
        notification.send()


def runcommands(filepath, package):
    if packages_dict[package]["ARCHIVE_transfer_okay"] and packages_dict[package]["do_commands"]:
        makewindow_okay, makewindow_error = ingestcommands.makewindow(filepath)
    else:
        packages_dict[package]["MAKEWINDOW_okay"] = None
        packages_dict[package]["MAKEMETADATA_okay"] = None
        packages_dict[package]["MAKECHECKSUMPACKAGE_okay"] = None
        return

    # Run makemetadata on package if makewindow was successfully run
    packages_dict[package]["MAKEWINDOW_okay"] = makewindow_okay
    if makewindow_okay:
        makemetadata_okay, makemetadata_error = ingestcommands.makemetadata(filepath)

    else:
        packages_dict[package]["MAKEWINDOW_error"] = makewindow_error
        packages_dict[package]["MAKEMETADATA_okay"] = None
        packages_dict[package]["MAKECHECKSUMPACKAGE_okay"] = None
        return

    # Run makechecksum on package if makemetadata was successfully run
    packages_dict[package]["MAKEMETADATA_okay"] = makemetadata_okay
    if makemetadata_okay:
        makechecksumpackage_okay, makechecksumpackage_error = ingestcommands.makechecksumpackage(filepath)
    else:
        packages_dict[package]["MAKEMETADATA_error"] = makemetadata_error
        packages_dict[package]["MAKECHECKSUMPACKAGE_okay"] = None
        return

    packages_dict[package]["MAKECHECKSUMPACKAGE_okay"] = makechecksumpackage_okay
    if not makechecksumpackage_okay:
        packages_dict[package]["MAKECHECKSUMPACKAGE_error"] = makechecksumpackage_error


# Ingests files
def ingest():
    # 1. Transfer files and run commands

    # Create desktop file path
    # Get the path to the user's home directory
    home_dir = os.path.expanduser('~')
    # Path to the Desktop folder (typically under the user's home directory)
    desktop_path = os.path.join(home_dir, 'Desktop')

    for package in packages_dict:
        # Create package object from RestructurePackage class
        package_obj = restructurepackage.RestructurePackage(desktop_path, package)
        for card, input_path in zip(packages_dict[package]["cards"], packages_dict[package]["input_paths"]):
            package_obj.create_output_directory(desktop_path, package, card)
            # Transfer files to Desktop
            package_obj.archive_restructure_folder(input_path, desktop_path, package, card, packages_dict[package]["do_fixity"],
                                           packages_dict[package]["do_drive_delete"])
            eject(input_path)

        # Save desktop transfer results and checksums
        packages_dict[package]["ARCHIVE_files_dict"] = package_obj.ARCHIVE_FILES_DICT
        packages_dict[package]["ARCHIVE_transfer_okay"] = package_obj.ARCHIVE_TRANSFER_OKAY
        if package_obj.ARCHIVE_TRANSFER_ERROR:
            packages_dict[package]["ARCHIVE_transfer_error"] = package_obj.ARCHIVE_TRANSFER_ERROR

        # Run commands
        if packages_dict[package]["do_commands"]:
            runcommands(os.path.join(desktop_path, package), package)
        else:
            packages_dict[package]["MAKEWINDOW_okay"] = None
            packages_dict[package]["MAKEMETADATA_okay"] = None
            packages_dict[package]["MAKECHECKSUMPACKAGE_okay"] = None

        # Transfer to server if last batch or only batch in process
        if packages_dict[package]["do_desktop_delete"]:
            # Transfer files to XSAN
            package_obj.delivery_restructure_folder(os.path.join(desktop_path, package, "objects"),
                                                    os.path.join(server2, get_showcode(package)),
                                                    package, packages_dict[package]["do_fixity"],
                                                    False,
                                                    packages_dict[package]["ARCHIVE_files_dict"])

            # Transfer files to CUNY TV Media
            package_obj.one2one_copy_folder(os.path.join(desktop_path, package), os.path.join(server, package),
                                            packages_dict[package]["do_fixity"],
                                            False,
                                            packages_dict[package]["ARCHIVE_files_dict"])

            # Save delivery transfer results and checksums
            packages_dict[package]["DELIVERY_files_dict"] = package_obj.DELIVERY_FILES_DICT
            packages_dict[package]["DELIVERY_transfer_okay"] = package_obj.DELIVERY_TRANSFER_OKAY
            if package_obj.DELIVERY_TRANSFER_ERROR:
                packages_dict[package]["DELIVERY_transfer_error"] = package_obj.DELIVERY_TRANSFER_ERROR

            # Save delivery transfer results and checksums
            packages_dict[package]["ONE2ONECOPY_files_dict"] = package_obj.ONE2ONECOPY_FILES_DICT
            packages_dict[package]["ONE2ONECOPY_transfer_okay"] = package_obj.ONE2ONECOPY_TRANSFER_OKAY
            if package_obj.DELIVERY_TRANSFER_ERROR:
                packages_dict[package]["ONE2ONECOPY_transfer_error"] = package_obj.ONE2ONECOPY_TRANSFER_ERROR
        else:
            packages_dict[package]["DELIVERY_transfer_okay"] = None
            packages_dict[package]["ONE2ONECOPY_transfer_okay"] = None

        #print
        #print(packages_dict[package])

    # 2. Upload to dropbox that have successfully transferred, went through makewindow, and send email notification
    for package in packages_dict:
        no_error = packages_dict[package]["ARCHIVE_transfer_okay"] and (
                    packages_dict[package]["MAKEWINDOW_okay"] or packages_dict[package]["MAKEWINDOW_okay"] is None)
        do_dropbox = packages_dict[package]["emails"]

        server_object_directory = os.path.join(desktop_path, package, "objects")
        dropbox_directory = dropbox_prefix(package) + f'/{package}'
        emails = packages_dict[package]["emails"]

        if no_error and do_dropbox:
            uploadsession = dropboxuploadsession.DropboxUploadSession(server_object_directory)

            for root, _, files in os.walk(server_object_directory, topdown=False):
                for filename in files:
                    if not mac_system_metadata(filename):
                        filepath = os.path.join(root, filename)
                        dropboxpath = os.path.join(dropbox_directory, filename)

                        try:
                            fixity_pass = uploadsession.upload_file_to_dropbox(filepath, dropboxpath, packages_dict[package]["do_fixity"], packages_dict[package]["DELIVERY_files_dict"])

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
            #packages_dict[package]["DROPBOX_files_dict"] = None
            packages_dict[package]["DROPBOX_transfer_okay"] = None


    # 3. Print logs and send email to library in case of error
    for package in packages_dict:
        # Write dictionary to a text file
        log_dest = os.path.join(server, package, "metadata")

        # Check if the directory exists, if not, create it
        if not os.path.exists(log_dest):
            os.makedirs(log_dest)

        print_log(log_dest, package, packages_dict)
        error_report(log_dest, package, packages_dict)

        if packages_dict[package]['do_desktop_delete']:
            shutil.rmtree(os.path.join(desktop_path, package))

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
    # Follows the format of Package Name {[cards], [input paths], do_fixity boolean, do_drive_delete boolean, do_commands boolean, {file dictionary}, transfer_okay boolean}
    packages_dict = {}

    # Check if connected to servers
    server = "/Volumes/CUNYTV_Media/archive_projects/camera_card_ingests"
    server_check(server)
    #server = "/Users/aidagarrido/Desktop"

    server2 = "/Users/aidagarrido/Desktop/Camera Card Delivery"
    #server2 = "/Volumes/TigerVideo/Camera Card Delivery"
    server_check(server2)

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
                multibatch = input(
                    "\tIs this a multi-batch process? (i.e. does the number of cards/drives exceed the number of readers?) y/n: ").lower() == 'y'
                if multibatch:
                    last_batch = input(
                        "\tIs this the last batch? y/n: ").lower() == 'y'
                if multibatch and not last_batch:
                    # Additional file processing options
                    do_fixity = (input("\tFixity check before and after transfer? y/n: ")).lower() == 'y'

                    # Create key-value pair
                    packages_dict[package_name] = {
                        "cards": [camera_card_number],
                        "input_paths": [input_path],
                        "do_fixity": do_fixity,
                        "do_drive_delete": False,
                        "do_desktop_delete": False,
                        "do_commands": False,
                        "do_dropbox": False,
                        "emails": False
                    }

                else:
                    # Additional file processing options
                    do_fixity = (input("\tFixity check before and after transfer? y/n: ")).lower() == 'y'
                    # do_drive_delete = (input("\tDelete original files after successful transfer? y/n: ")).lower() == 'y'
                    do_drive_delete = False
                    do_commands = (input(
                        "\tRun makewindow, makemetdata, checksumpackage? y/n: ")).lower() == 'y'
                    do_dropbox = (input(
                        "\tUpload to dropbox? y/n: ")).lower() == 'y'
                    emails = []
                    if do_dropbox:
                        emails = validateuserinput.emails(
                            input("\tList email(s) delimited by space or press enter to continue: "))
                        emails.extend(["library@tv.cuny.edu"])
                        #emails.extend(["aida.garrido@tv.cuny.edu"])

                    # Create key-value pair
                    packages_dict[package_name] = {
                        "cards": [camera_card_number],
                        "input_paths": [input_path],
                        "do_fixity": do_fixity,
                        "do_drive_delete": do_drive_delete,
                        "do_desktop_delete": True,
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

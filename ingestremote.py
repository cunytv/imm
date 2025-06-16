#!/usr/bin/env python3

import detectrecentlyinserteddrives
import restructurepackage
import ingestcommands
import validateuserinput
import dropboxuploadsession
import cunymediaids
import sendnetworkmail
import re
import sys
import os
import subprocess
import time
import shutil
from datetime import datetime
import json
import detectiphone
from pathlib import Path

# Tiger server flag; proceed with all other aspects of ingest if tiger_down true
tiger_down = False

# iphone flag; proceed accordingly if true
iphone = False

# Create dictionary of packages
packages_dict = {}

# Create dictionary structure for one package
package_dict = {
    "cards": None,
    "input_paths": None,
    "do_fixity": True,
    "do_drive_delete": False,
    "do_desktop_delete": False,
    "do_commands": False,
    "do_dropbox": False,
    "emails": None,
    "DROPBOX_link": None,
    "DESKTOP_transfer_okay": None,
    "DESKTOP_transfer_not_okay_reason": None,
    "MAKEWINDOW_okay": None,
    "MAKEWINDOW_not_okay_reason": None,
    "MAKEMETADATA_okay": None,
    "MAKEMETADATA_not_okay_reason": None,
    "MAKECHECKSUMPACKAGE_okay": None,
    "MAKECHECKSUMPACKAGE_not_okay_reason": None,
    "ARCHIVE_transfer_okay": None,
    "ARCHIVE_transfer_not_okay_reason": None,
    "DELIVERY_transfer_okay": None,
    "DELIVERY_transfer_not_okay_reason": None,
    "DROPBOX_transfer_okay": None,
    "DROPBOX_transfer_not_okay_reason": None,
    "DESKTOP_files_dict": None,
    "ARCHIVE_files_dict": None,
    "DELIVERY_files_dict": None,
    "DROPBOX_files_dict": None
}

# Checks if user is connected to server
def server_check(s, s_type):
    global tiger_down
    if not os.path.exists(s):
        print(f'{s} not found. You might not be connected to the server.')
        if s_type == 'tiger':
            cont = (input("Continue ingest anyway? y/n: ")).lower() == 'y'
            if cont:
                tiger_down = True
                return
            else:
                sys.exit(1)
        else:
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


def print_log(log_dest, package):
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
        desktop_log = os.path.join(desktop_path, f"ingestlog{package}.json")
        shutil.move(log_path, desktop_log)

        with open(desktop_log, "r") as file:
            log_data = json.load(file)

        # Update these values
        # Find the cards and input_paths tag, and append new values
        log_data['cards'] += f", {', '.join(map(str, packages_dict[package]['cards']))}"
        log_data['input_paths'] += f", {', '.join(map(str, packages_dict[package]['input_paths']))}"

        # Find DESKTOP_transfer_okay and replace value
        log_data['DESKTOP_transfer_okay'] = packages_dict[package]['DESKTOP_transfer_okay']
        if not log_data['DESKTOP_transfer_okay']:
            log_data['DESKTOP_transfer_not_okay_reason'] = packages_dict[package]['DESKTOP_transfer_not_okay_reason']

        # Append DESKTOP_files_dict
        for file_data in packages_dict[package]['DESKTOP_files_dict']:
            log_data['DESKTOP_files_dict'].append(file_data)

        with open(desktop_log, "w") as file:
            json.dump(log_data, file, indent=4)

        # Move log back to server; append time to avoid cache issues
        now = datetime.now()
        time_str = now.strftime("%H%M%S")

        shutil.move(desktop_log, os.path.join(archive_server, package, "metadata", f"ingestlog{package}_{time_str}.json"))

    # If part of multi-batch process and last batch
    elif log_exists and packages_dict[package]['do_desktop_delete']:
        # Move existing log to desktop to append values (doesn't work when trying to write directly to server)
        home_dir = os.path.expanduser('~')
        desktop_path = os.path.join(home_dir, 'Desktop')
        desktop_log = os.path.join(desktop_path, f"ingestlog{package}.json")
        shutil.move(log_path, desktop_log)

        # Load the json file
        with open(desktop_log, "r") as file:
            log_data = json.load(file)

        # Find the cards and input_paths tag, and append new values
        log_data['cards'] += f", {', '.join(map(str, packages_dict[package]['cards']))}"
        log_data['input_paths'] += f", {', '.join(map(str, packages_dict[package]['input_paths']))}"

        # Replace or create these values
        log_data['do_fixity'] = packages_dict[package]['do_fixity']
        log_data['do_drive_delete'] = packages_dict[package]['do_drive_delete']
        log_data['do_desktop_delete'] = packages_dict[package]['do_desktop_delete']
        log_data['do_commands'] = packages_dict[package]['do_commands']
        log_data['do_dropbox'] = packages_dict[package]['do_dropbox']
        if packages_dict[package]['emails']:
            log_data['emails'] = ", ".join(map(str, packages_dict[package]['emails']))
        if packages_dict[package]['DROPBOX_transfer_okay']:
            log_data['DROPBOX_link'] = packages_dict[package]["DROPBOX_link"]
        log_data['MAKEWINDOW_okay'] = packages_dict[package]['MAKEWINDOW_okay']
        if not log_data['MAKEWINDOW_okay']:
            log_data['MAKEWINDOW_not_okay_reason'] = packages_dict[package]['MAKEWINDOW_not_okay_reason']
        log_data['MAKEMETADATA_okay'] = packages_dict[package]['MAKEMETADATA_okay']
        if not log_data['MAKEMETADATA_okay']:
            log_data['MAKEMETADATA_not_okay_reason'] = packages_dict[package]['MAKEMETADATA_not_okay_reason']
        log_data['MAKECHECKSUMPACKAGE_okay'] = packages_dict[package]['MAKECHECKSUMPACKAGE_okay']
        if not log_data['MAKECHECKSUMPACKAGE_okay']:
            log_data['MAKECHECKSUMPACKAGE_not_okay_reason'] = packages_dict[package]['MAKECHECKSUMPACKAGE_not_okay_reason']
        log_data['DELIVERY_transfer_okay'] = packages_dict[package]['DELIVERY_transfer_okay']
        if not log_data['DELIVERY_transfer_okay']:
            log_data['DELIVERY_transfer_not_okay_reason'] = packages_dict[package]['DELIVERY_transfer_not_okay_reason']
        log_data['ARCHIVE_transfer_okay'] = packages_dict[package]['ARCHIVE_transfer_okay']
        if not log_data['ARCHIVE_transfer_okay']:
            log_data['ARCHIVE_transfer_not_okay_reason'] = packages_dict[package]['ARCHIVE_transfer_not_okay_reason']
        log_data['DROPBOX_transfer_okay'] = packages_dict[package]['DROPBOX_transfer_okay']
        if not log_data['DROPBOX_transfer_okay']:
            log_data['DROPBOX_transfer_not_okay_reason'] = packages_dict[package]['DROPBOX_transfer_not_okay_reason']
        log_data['ARCHIVE_files_dict'] = packages_dict[package]['ARCHIVE_files_dict']
        log_data['DELIVERY_files_dict'] = packages_dict[package]['DELIVERY_files_dict']
        log_data['DROPBOX_files_dict'] = packages_dict[package]['DROPBOX_files_dict']

        # Append DESKTOP_files_dict
        for file_data in packages_dict[package]['DESKTOP_files_dict']:
            log_data['DESKTOP_files_dict'].append(file_data)

        # Remove none values
        log_data = remove_none(log_data)

        with open(desktop_log, "w") as file:
            json.dump(log_data, file, indent=4)

        # Move log back to server; append time to avoid cache issues
        now = datetime.now()
        time_str = now.strftime("%H%M%S")

        shutil.move(desktop_log, os.path.join(archive_server, package, "metadata", f"ingestlog{package}_{time_str}.json"))

    # If only batch or first batch
    else:
        now = datetime.now()
        time_str = now.strftime("%H%M%S")

        log_path = os.path.join(archive_server, package, "metadata", f"ingestlog{package}_{time_str}.json")

        packages_dict[package]['cards'] = ", ".join(map(str, packages_dict[package]['cards']))
        packages_dict[package]['input_paths'] = ", ".join(map(str, packages_dict[package]['input_paths']))

        # Create a custom structure
        log_data = {
            "package": f"{package}",
            **packages_dict[package]  # Unpack the dictionary and add its keys/values
        }

        # if only batch, and not first batch
        if packages_dict[package]['do_desktop_delete']:
            if log_data['emails']:
                log_data['emails'] = ", ".join(map(str, log_data['emails']))
            log_data = remove_none(log_data)

        with open(log_path, "w") as file:
            json.dump(log_data, file, indent=4)

#Remove keys with None values from a dictionary (non-recursively).
def remove_none(d):
    if isinstance(d, dict):
        return {k: v for k, v in d.items() if v is not None and v != 'null'}
    elif isinstance(d, list):
        return [v for v in d if v is not None and v != 'null']
    else:
        return d

def error_report(log_dest, package):
    dpto = packages_dict[package]["DESKTOP_transfer_okay"]
    mwo = packages_dict[package]["MAKEWINDOW_okay"]
    mmo = packages_dict[package]["MAKEMETADATA_okay"]
    mcpo = packages_dict[package]["MAKECHECKSUMPACKAGE_okay"]
    ato = packages_dict[package]["ARCHIVE_transfer_okay"]
    dyto = packages_dict[package]["DELIVERY_transfer_okay"]
    dbto = packages_dict[package]["DROPBOX_transfer_okay"]

    event_keys = ["DESKTOP_transfer_okay", "MAKEWINDOW_okay", "MAKEMETADATA_okay", "MAKECHECKSUMPACKAGE_okay", "ARCHIVE_transfer_okay", "DELIVERY_transfer_okay", "DROPBOX_transfer_okay"]
    event_values = [dpto, mwo, mmo, mcpo, ato, dyto, dbto]

    print(event_keys)
    print(event_values)


    # Treat None as True
    variables = [v if v is not None else True for v in event_values]

    if not all(variables):
        notification = sendnetworkmail.SendNetworkEmail()
        notification.sender("library@tv.cuny.edu")
        notification.recipients(["library@tv.cuny.edu"])
        #notification.recipients(["aida.garrido@tv.cuny.edu"])
        notification.subject(f"Ingest error: {package}")


        notification.html_content("<p>Hello, </p><p>Error(s) occurred during ingest:</p>")
        notification.html_content("<u>user input</u><br>")
        notification.html_content(f"do_dropbox: {packages_dict[package]['do_dropbox']}<br>")
        print(packages_dict[package]["do_dropbox"])
        if packages_dict[package]["do_dropbox"]:
            notification.html_content(f"emails: {', '.join(map(str, packages_dict[package]['emails']))}<br>")
        notification.html_content("<br><u>ingest events</u><br>")

        i = 0
        while i < len(event_keys):
            if event_values[i] is False:
                notification.html_content(f"<u><strong>{event_keys[i]}: {event_values[i]}</strong></u><br>")
            else:
                notification.html_content(f"{event_keys[i]}: {event_values[i]}<br>")
            i+=1

        log_path = ''
        for filename in os.listdir(log_dest):
            # Check if the filename starts with "ingestlog"
            if filename.startswith("ingestlog"):
                log_path = os.path.join(log_dest, filename)
                break

        notification.html_content(f"<p>Check attachment for more information or navigate to {log_path}</p>Best, <br>Library Bot")

        # Add the attachment
        notification.attachment(log_path)

        # Send the notification
        notification.send()

def makegif(directory):
    # Get the path to the user's home directory
    home_dir = os.path.expanduser('~')
    # Path to the Desktop folder (typically under the user's home directory)
    desktop_path = os.path.join(home_dir, 'Desktop')
    name = directory.rsplit('/', 1)[1] + '.gif'

    gif_output_filepath = os.path.join(desktop_path, name)
    command = f"makegifsummary -o {gif_output_filepath} {directory}"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True)
    for line in process.stdout:
        print(line, end='')
    process.wait()
    if process.returncode == 0:
        return gif_output_filepath
    else:
        return process.returncode

def runcommands(filepath, package):
    if packages_dict[package]["DESKTOP_transfer_okay"] and packages_dict[package]["do_commands"]:
        makewindow_okay, makewindow_error = ingestcommands.makewindow(filepath)
    else:
        return

    # Run makemetadata on package if makewindow was successfully run
    packages_dict[package]["MAKEWINDOW_okay"] = makewindow_okay
    if makewindow_okay:
        makemetadata_okay, makemetadata_error = ingestcommands.makemetadata(filepath)
    else:
        packages_dict[package]["MAKEWINDOW_not_okay_reason"] = {
                "timestamp": str(datetime.now()),
                "error_type": makewindow_error,
            }

        return

    # Run makechecksum on package if makemetadata was successfully run
    packages_dict[package]["MAKEMETADATA_okay"] = makemetadata_okay
    if makemetadata_okay:
        makechecksumpackage_okay, makechecksumpackage_error = ingestcommands.makechecksumpackage(filepath)
    else:
        packages_dict[package]["MAKEMETADATA_not_okay_reason"] = {
                "timestamp": str(datetime.now()),
                "error_type": makemetadata_error
            }
        return

    packages_dict[package]["MAKECHECKSUMPACKAGE_okay"] = makechecksumpackage_okay
    if not makechecksumpackage_okay:
        packages_dict[package]["MAKECHECKSUMPACKAGE_not_okay_reason"] = {
                "timestamp": str(datetime.now()),
                "error_type": makechecksumpackage_error
            }

def empty_iphone_temp():
    # Loop through all files and delete them
    for filename in os.listdir(iphone_temp_folder):
        file_path = os.path.join(iphone_temp_folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

def ingest_desktop_transfer(desktop_path):
    # Create package object from RestructurePackage class
    # Files are first transferred locally to desktop to quicken file processing (e.g. windowdub)
    # File are transformed into archive package
    for package in packages_dict:
        package_obj = restructurepackage.RestructurePackage()
        for card, input_path in zip(packages_dict[package]["cards"], packages_dict[package]["input_paths"]):
            if input_path == iphone_temp_folder:
                ingest_iphone_media()

            package_obj.create_output_directory(desktop_path, package, card)
            # Transfer files to Desktop
            package_obj.restructure_copy("archive", input_path, desktop_path, package, card,
                                         packages_dict[package]["do_fixity"],
                                         packages_dict[package]["do_drive_delete"])
            if input_path == iphone_temp_folder:
                empty_iphone_temp()
            else:
                eject(input_path)

        # Save desktop transfer results and checksums
        packages_dict[package]["DESKTOP_files_dict"] = package_obj.FILES_DICT
        packages_dict[package]["DESKTOP_transfer_okay"] = package_obj.TRANSFER_OKAY
        if package_obj.TRANSFER_ERROR:
            packages_dict[package]["DESKTOP_transfer_error"] = package_obj.TRANSFER_ERROR

def ingest_iphone_media():
    # Path to your AppleScript file
    script_dir = Path(__file__).resolve().parent
    script_path = script_dir / "downloadlatestiphonemedia.scpt"

    # Run the script using osascript
    try:
        result = subprocess.run(
            ["osascript", script_path],
            check=True,
            capture_output=True,
            text=True
        )
        print("Script Output:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("AppleScript failed:")
        print(e.stderr)

def ingest_commands(desktop_path):
    # Run commands on local copy if last batch or only batch in process
    # do_commands set accordingly in main
    for package in packages_dict:
        if packages_dict[package]["do_commands"]:
            runcommands(os.path.join(desktop_path, package), package)

def ingest_delivery_transfer(desktop_path):
    for package in packages_dict:
        # Transfer to servers if last batch or only batch in process
        # do_desktop_delete is set accordingly in main
        if packages_dict[package]["do_desktop_delete"]:
            # Transfer files to Tiger
            global tiger_down
            if not tiger_down:
                # Create new package object from RestructurePackage class
                # Files are transferred from desktop to Tiger server
                # File are transformed into delivery package
                package_obj = restructurepackage.RestructurePackage()
                package_obj.restructure_copy("delivery", os.path.join(desktop_path, package, "objects"),
                                             os.path.join(tiger_server, get_showcode(package)),
                                             package, do_fixity=packages_dict[package]["do_fixity"],
                                             do_delete=False,
                                             files_dict=packages_dict[package]["ARCHIVE_files_dict"])

                # Save delivery transfer results and checksums
                packages_dict[package]["DELIVERY_files_dict"] = package_obj.FILES_DICT
                packages_dict[package]["DELIVERY_transfer_okay"] = package_obj.TRANSFER_OKAY
                if package_obj.TRANSFER_ERROR:
                    packages_dict[package]["DELIVERY_transfer_not_okay_reason"] = package_obj.TRANSFER_ERROR
            else:
                packages_dict[package]["DELIVERY_transfer_okay"] = False
                packages_dict[package]["DELIVERY_transfer_not_okay_reason"] = {"timestamp": str(datetime.now()),
                                                                               "error_type": None,
                                                                               "message": "Tiger volume is down"}

def ingest_archive_transfer(desktop_path):
    for package in packages_dict:
        # Create new package object
        # Files are transferred from desktop to CUNYTVMedia
        # File are not transformed, since desktop copy is already an archive package; thus one2one method
        package_obj = restructurepackage.RestructurePackage()
        package_obj.restructure_copy("one2one", os.path.join(desktop_path, package),
                                     os.path.join(archive_server, package),
                                     do_fixity=packages_dict[package]["do_fixity"],
                                     do_delete=False,
                                     files_dict=packages_dict[package]["DESKTOP_files_dict"])

        # Save delivery transfer results and checksums
        packages_dict[package]["ARCHIVE_files_dict"] = package_obj.FILES_DICT
        packages_dict[package]["ARCHIVE_transfer_okay"] = package_obj.TRANSFER_OKAY
        if package_obj.TRANSFER_ERROR:
            packages_dict[package]["ARCHIVE_transfer_not_okay_reason"] = package_obj.TRANSFER_ERROR

def ingest_dropbox_upload(desktop_path):
    # Upload to dropbox that have successfully transferred, went through makewindow, and send email notification
    for package in packages_dict:
        no_error = packages_dict[package]["DESKTOP_transfer_okay"]
        do_dropbox = packages_dict[package]["do_dropbox"]

        desktop_object_directory = os.path.join(desktop_path, package, "objects")
        dropbox_directory = dropbox_prefix(package) + f'/{package}'
        emails = packages_dict[package]["emails"]

        if no_error and do_dropbox:
            uploadsession = dropboxuploadsession.DropboxUploadSession(desktop_object_directory)

            for root, _, files in os.walk(desktop_object_directory, topdown=False):
                for filename in files:
                    if not mac_system_metadata(filename):
                        filepath = os.path.join(root, filename)
                        dropboxpath = os.path.join(dropbox_directory, filename)

                        uploadsession.upload_file_to_dropbox(filepath, dropboxpath,
                                                             packages_dict[package]["do_fixity"],
                                                             packages_dict[package]["DESKTOP_files_dict"])

            packages_dict[package]["DROPBOX_files_dict"] = uploadsession.DROPBOX_FILES_DICT
            packages_dict[package]["DROPBOX_transfer_okay"] = uploadsession.DROPBOX_TRANSFER_OKAY
            if not packages_dict[package]["DROPBOX_transfer_okay"]:
                packages_dict[package][
                    "DROPBOX_transfer_not_okay_reason"] = uploadsession.DROPBOX_TRANSFER_NOT_OKAY_REASON

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
                packages_dict[package]["DROPBOX_link"] = uploadsession.share_link
                window_dub_share_link = uploadsession.get_shared_link(f"{dropbox_directory}/{package}_WINDOW.mp4")[0]

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
                        Click the link below to stream the window dub:
                        <br><a href="{window_dub_share_link}">{window_dub_share_link}</a>.
                        <p></p>
                        Click the link below to access all files, including the window dub:
                        <br><a href="{uploadsession.share_link}">{uploadsession.share_link}</a>.
                        <p></p>
                        Best
                        <br>
                        Library Bot
                        <p></p>
                      </body>
                    </html>
                    """

                notification.html_content(html_content)

                gif_path = makegif(os.path.join(archive_server, package))
                notification.embed_img(gif_path)

                notification.send()
                os.remove(gif_path)

                # Send dropbox notification to non-CUNY recipients
                if other_emails is not None:
                    msg = f"{dropbox_directory} has finished uploading."
                    uploadsession.add_folder_member(other_emails, uploadsession.get_shared_folder_id(dropbox_directory),
                                                    False, msg)

def ingest_log_and_errors(desktop_path):
    for package in packages_dict:
        log_dest = os.path.join(archive_server, package, "metadata")
        # Check if the log exists, if not, create it
        if not os.path.exists(log_dest):
            os.makedirs(log_dest)

        print_log(log_dest, package)
        error_report(log_dest, package)

        if packages_dict[package]['do_desktop_delete']:
            shutil.rmtree(os.path.join(desktop_path, package))

def ingest_resourcespace():
    script_dir = Path(__file__).resolve().parent
    php_script_path = script_dir / "remote_resource_space_ingest.php"

    for package in packages_dict:
        no_error = (packages_dict[package]["ARCHIVE_transfer_okay"] and packages_dict[package]["MAKEWINDOW_okay"])

        if no_error:
            dir = os.path.join(archive_server, package, "objects")
            dropbox_link = packages_dict[package]['DROPBOX_link']
            if dropbox_link is None:
                dropbox_link = ""
            else:
                dropbox_link = dropbox_link.split('&', 1)[0]

            command = f"php {php_script_path} {dir} {dropbox_link}"
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True)

            for line in process.stdout:
                print(line, end='')
                process.wait()

            print("Exit code:", process.returncode)

# Ingests files
def ingest():
    home_dir = os.path.expanduser('~')
    desktop_path = os.path.join(home_dir, 'Desktop')

    ingest_desktop_transfer(desktop_path)
    ingest_commands(desktop_path)

    ## multi thread these three
    ingest_delivery_transfer(desktop_path)
    ingest_archive_transfer(desktop_path)
    ingest_dropbox_upload(desktop_path)

    ingest_log_and_errors(desktop_path) # Deletes dekstop transfer at this point
    ingest_resourcespace() # Uses archive package since filestore and cc ingests are on the same server

if __name__ == "__main__":
    # Check if connected to servers
    archive_server = "/Volumes/CUNYTVMEDIA/archive_projects/camera_card_ingests"
    #archive_server = "/Users/aidagarrido/Desktop/camera_card_ingests"
    server_check(archive_server, "archive")

    # tiger_server = "/Users/aidagarrido/Desktop/Camera Card Delivery"
    tiger_server = "/Volumes/TigerVideo/Camera Card Delivery"
    server_check(tiger_server, "tiger")

    # path to Iphone temp folder
    #iphone_temp_folder = '/Users/aidagarrido/Pictures/Iphone_Ingest_Temp'
    iphone_temp_folder = '/Users/libraryad/Pictures/Iphone_Ingest_Temp'

    # Detect recently inserted drives, cards, and iphone
    countdown(5)
    volume_paths = detectrecentlyinserteddrives.volume_paths()
    # At the moment, script only works with one iphone at a time
    # iPhone protocols don't mount iphone as a drive and make it impossible get iphone name from terminal
    num_iphones = detectiphone.count_connected_iphones()

    # Organizes user inputs into dictionary
    if not volume_paths and num_iphones == 0:
        print("No cards detected")
    else:
        cunymediaids.print_media_dict()
        print()
        print(f"{len(volume_paths)} card(s) detected and {num_iphones} iphone(s) detected.")

        if num_iphones > 0:
            input("Please ensure iPhone remains unlocked during ingest. Press enter to continue. ")
            iphone = True
            volume_paths.insert(0, iphone_temp_folder)

        for input_path in volume_paths:
            if input_path == iphone_temp_folder:
                print(f"- iPhone")
            else:
                print(f"- {input_path}")
                print_first_ten_filenames(input_path)

            package_name = validateuserinput.card_package_name(input(f"\tEnter a package name: "))
            camera_card_number = validateuserinput.card_subfolder_name(
                input(f"\tEnter the corresponding card number or name on sticker (serialize from 1 if none): "))

            if package_name in packages_dict:
                # Edit existing key-value pair
                packages_dict[package_name]["cards"].append(camera_card_number)
                packages_dict[package_name]["input_paths"].append(input_path)

            else:
                package_dict['cards'] = [camera_card_number]
                package_dict['input_paths'] = [input_path]

                multibatch = input(
                    "\tIs this a multi-batch process? (i.e. does the number of cards/drives exceed the number of readers?) y/n: ").lower() == 'y'
                last_batch = False
                if multibatch:
                    last_batch = input(
                        "\tIs this the last batch? y/n: ").lower() == 'y'

                if multibatch and not last_batch:
                    # Create key-value pair using default initialized values
                    packages_dict[package_name] = package_dict
                else:
                    do_dropbox = (input(
                        "\tUpload to dropbox? y/n: ")).lower() == 'y'

                    if do_dropbox:
                        emails = validateuserinput.emails(
                            input("\tList email(s) delimited by space or press enter to continue: "))
                        emails.extend(["library@tv.cuny.edu"])
                        #emails.extend(["aida.garrido@tv.cuny.edu"])
                        # Update key-value pair from default
                        package_dict['do_dropbox'] = True
                        package_dict['emails'] = emails

                    # Update key-value pair from default
                    package_dict['do_desktop_delete'] = True
                    package_dict['do_commands'] = True

                    packages_dict[package_name] = package_dict
        # Begin ingest
        ingest()

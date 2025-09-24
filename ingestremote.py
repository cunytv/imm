#!/usr/bin/env python3

# top of your script, before anything else
#import builtins
#import traceback

#original_print = print

#def debug_print(*args, **kwargs):
#    stack = traceback.extract_stack(limit=3)
#    filename, lineno, func, _ = stack[0]
#    original_print(f"[PRINT from {filename}:{lineno} in {func}] ", *args, **kwargs)

#builtins.print = debug_print

import detectrecentlyinserteddrives
import restructurepackage
import ingestcommands
import validateuserinput
import dropboxuploadsession
import cunymediaids
import sendnetworkmail
import multiprogressbar
import threading
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

# Because cards mount generically as Untitled volumes
currentcards = []

# Create dictionary of packages
packages_dict = {}

# Array of incomplete multibatch packages
incomplete_multibatch = []

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

DESKTOP_obj = ''

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

def merge_dicts(d1, d2):
    merged = dict(d1)  # start with a copy of d1
    for k, v in d2.items():
        if k in merged:
            if isinstance(merged[k], dict) and isinstance(v, dict):
                merged[k] = merge_dicts(merged[k], v)
            elif isinstance(merged[k], list) and isinstance(v, list):
                merged[k] = merged[k] + v  # concatenate lists
            elif v is not None:
                merged[k] = v  # overwrite if new value not None
        else:
            merged[k] = v
    return merged

def print_log(log_dest, package):
    # Check if there is an existing log
    old_log_exists = False
    old_log_path = ''
    old_log_data = {}
    for filename in os.listdir(log_dest):
        if filename.startswith("ingestlog"):
            old_log_exists = True
            old_log_path = os.path.join(log_dest, filename)
            with open(old_log_path, "r") as f:
                old_log_data = json.load(f)
            break

    # Create a new log
    now = datetime.now()
    time_str = now.strftime("%H%M%S")

    new_log_path = os.path.join(archive_server, package, "metadata", f"ingestlog{package}_{time_str}.json")

    new_log_data = {
        "package": package,
        **packages_dict[package]
    }

    # Write data to json file
    if old_log_exists:
        overlap = all(d in new_log_data for d in old_log_data)
        if overlap:
            old_log_data["DESKTOP_files_dict"] = []
        merged_data = merge_dicts(old_log_data, new_log_data)
        with open(new_log_path, "w") as file:
            json.dump(merged_data, file, indent=4)
        os.remove(old_log_path)
    else:
        with open(new_log_path, "w") as file:
            json.dump(new_log_data, file, indent=4)

def error_report(log_dest, package):
    dpto = packages_dict[package]["DESKTOP_transfer_okay"]
    mwo = packages_dict[package]["MAKEWINDOW_okay"]
    mmo = packages_dict[package]["MAKEMETADATA_okay"]
    mcpo = packages_dict[package]["MAKECHECKSUMPACKAGE_okay"]
    ato = packages_dict[package]["ARCHIVE_transfer_okay"]
    dyto = packages_dict[package]["DELIVERY_transfer_okay"]
    dbto = packages_dict[package]["DROPBOX_transfer_okay"]

    event_keys = ["DESKTOP_transfer_okay", "MAKEWINDOW_okay", "MAKEMETADATA_okay", "MAKECHECKSUMPACKAGE_okay",
                  "ARCHIVE_transfer_okay", "DELIVERY_transfer_okay", "DROPBOX_transfer_okay"]
    event_values = [dpto, mwo, mmo, mcpo, ato, dyto, dbto]

    # Treat None as True
    variables = [v if v is not None else True for v in event_values]

    if not all(variables):
        print("\033[31mAn error occured during ingest.\033[0m")
        notification = sendnetworkmail.SendNetworkEmail()
        notification.sender("library@tv.cuny.edu")
        notification.recipients(["library@tv.cuny.edu"])
        #notification.recipients(["aida.garrido@tv.cuny.edu"])
        notification.subject(f"Ingest error: {package}")

        notification.html_content("<p>Hello, </p><p>Error(s) occurred during ingest:</p>")
        notification.html_content("<u>user input</u><br>")
        notification.html_content(f"do_dropbox: {packages_dict[package]['do_dropbox']}<br>")
        if packages_dict[package]["do_dropbox"]:
            notification.html_content(f"emails: {', '.join(map(str, packages_dict[package]['emails']))}<br>")
        notification.html_content("<br><u>ingest events</u><br>")

        i = 0
        while i < len(event_keys):
            if event_values[i] is False:
                notification.html_content(f"<u><strong>{event_keys[i]}: {event_values[i]}</strong></u><br>")
                print(f"{event_keys[i]}: {event_values[i]}")
            else:
                notification.html_content(f"{event_keys[i]}: {event_values[i]}<br>")
            i += 1

        log_path = ''
        for filename in os.listdir(log_dest):
            if filename.startswith("ingestlog"):
                log_path = os.path.join(log_dest, filename)
                break

        print(f"See {log_path} for more information.")
        notification.html_content(
            f"<p>Check attachment for more information or navigate to {log_path}</p>Best, <br>Library Bot")

        notification.attachment(log_path)
        with open(os.devnull, "w") as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = devnull
            sys.stderr = devnull
            try:
                notification.send()
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
    else:
        print(f"\033[32mIngest succesfully completed\033[0m")

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


def ingest_desktop_transfer(package_obj, package, desktop_path, input_path, card):
    # Create package object from RestructurePackage class
    # Files are first transferred locally to desktop to quicken file processing (e.g. windowdub)
    # File are transformed into archive package
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
    except subprocess.CalledProcessError as e:
        print("AppleScript failed:")
        print(e.stderr)


def ingest_commands(desktop_path):
    # Run commands on local copy if last batch or only batch in process
    # do_commands set accordingly in main
    for package in packages_dict:
        if packages_dict[package]["do_commands"]:
            runcommands(os.path.join(desktop_path, package), package)


def ingest_delivery_transfer(desktop_path, package, package_obj):
    # Transfer to servers if last batch or only batch in process
    # do_desktop_delete is set accordingly in main
    if packages_dict[package]["do_desktop_delete"]:
        # Transfer files to Tiger
        global tiger_down
        if not tiger_down:
            # Create new package object from RestructurePackage class
            # Files are transferred from desktop to Tiger server
            # File are transformed into delivery package
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


def ingest_archive_transfer(desktop_path, package, package_obj):
    # Transfer to servers if last batch or only batch in process
    # do_desktop_delete is set accordingly in main
    if packages_dict[package]["do_desktop_delete"]:
        # Create new package object
        # Files are transferred from desktop to CUNYTVMedia
        # File are not transformed, since desktop copy is already an archive package; thus one2one method
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


def ingest_dropbox_upload(desktop_path, package, uploadsession):
    # Upload to dropbox that have successfully transferred, went through makewindow, and send email notification
    no_error = packages_dict[package]["DESKTOP_transfer_okay"] and packages_dict[package]["MAKEWINDOW_okay"]
    do_dropbox = packages_dict[package]["do_dropbox"]

    desktop_object_directory = os.path.join(desktop_path, package, "objects")
    dropbox_directory = dropbox_prefix(package) + f'/{package}'
    emails = packages_dict[package]["emails"]

    if no_error and do_dropbox:
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
            uploadsession.ingestremote_email(desktop_path, emails, dropbox_directory, package)
            packages_dict[package]["DROPBOX_link"] = uploadsession.share_link

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

    to_delete = [pkg for pkg in packages_dict if pkg not in incomplete_multibatch]
    for pkg in to_delete:
        del packages_dict[pkg]


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

    for package in packages_dict:
        for card, input_path in zip(packages_dict[package]["cards"], packages_dict[package]["input_paths"]):

            print(f"\033[32m-----{package}; Card: {card}-----\033[0m")
            package_obj = restructurepackage.RestructurePackage()

            mpb = multiprogressbar.MultiProgressBar()
            mpb.add_task("Desktop Transfer", package_obj, 'TOTAL_BYTES', 'TOTAL_FILES', 'PROG_BYTES', 'PROG_FILES',
                             'CURRENT_PROCESS')


            # Create threads for each function
            t1 = threading.Thread(target=ingest_desktop_transfer, args=(package_obj, package, desktop_path,input_path, card,))
            stop_event = threading.Event()
            t2 = threading.Thread(target=mpb.render, args=(stop_event,))

            for t in (t1, t2):
                t.start()

            t1.join()

            stop_event.set()

            t2.join()

            # Save desktop transfer results and checksums
            if packages_dict[package]["DESKTOP_files_dict"]:
                packages_dict[package]["DESKTOP_files_dict"] += package_obj.FILES_DICT
            else:
                packages_dict[package]["DESKTOP_files_dict"] = package_obj.FILES_DICT
            if packages_dict[package]["DESKTOP_transfer_okay"] is not False:
                packages_dict[package]["DESKTOP_transfer_okay"] = package_obj.TRANSFER_OKAY
            if package_obj.TRANSFER_ERROR:
                if packages_dict[package]["DESKTOP_transfer_error"]:
                    packages_dict[package]["DESKTOP_transfer_error"] += package_obj.TRANSFER_ERROR
                else:
                    packages_dict[package]["DESKTOP_transfer_error"] = package_obj.TRANSFER_ERROR

    ingest_commands(desktop_path)

    for package in packages_dict:
        if package not in incomplete_multibatch:
            print(f"\033[32m-----{package}-----\033[0m")
            archive_obj = restructurepackage.RestructurePackage()
            delivery_obj = restructurepackage.RestructurePackage()

            desktop_object_directory = os.path.join(desktop_path, package, "objects")
            db_obj = dropboxuploadsession.DropboxUploadSession(desktop_object_directory, packages_dict[package]["DESKTOP_files_dict"])

            mpb = multiprogressbar.MultiProgressBar()
            if packages_dict[package]["do_dropbox"]:
                mpb.add_task("Dropbox Upload", db_obj, 'total_size', 'total_files', 'bytes_read', 'files_read',
                         'current_process')
            mpb.add_task("Archive Transfer", archive_obj, 'TOTAL_BYTES', 'TOTAL_FILES', 'PROG_BYTES', 'PROG_FILES',
                             'CURRENT_PROCESS')
            mpb.add_task("Delivery Transfer", delivery_obj, 'TOTAL_BYTES', 'TOTAL_FILES', 'PROG_BYTES', 'PROG_FILES',
                         'CURRENT_PROCESS')

            # Create threads for each function
            t1 = threading.Thread(target=ingest_dropbox_upload, args=(desktop_path, package, db_obj,))
            t2 = threading.Thread(target=ingest_delivery_transfer, args=(desktop_path, package, delivery_obj,))
            t3 = threading.Thread(target=ingest_archive_transfer, args=(desktop_path, package, archive_obj,))

            stop_event = threading.Event()
            t4 = threading.Thread(target=mpb.render, args=(stop_event,))

            mpb.threads = [t1, t2, t3]

            # Start all threads
            for t in (t1, t2, t3, t4):
                t.start()

            for t in (t1, t2, t3):
                t.join()

            stop_event.set()

            t4.join()

    #ingest_resourcespace()  # Uses archive package since filestore and cc ingests are on the same server

    ingest_log_and_errors(desktop_path)  # Deletes dekstop transfer at this point

def startup(multibatchname=None):
    global tiger_down, iphone, packages_dict, incomplete_multibatch, package_dict, samebatch, currentcards

    # Organizes user inputs into dictionary
    if not volume_paths and num_iphones == 0:
        print("No cards detected")
        #add mistaken batch process?
    else:
        if not currentcards or not multibatchname::
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

            if multibatchname and len(packages_dict) == 1:
                package_name = multibatchname
            elif (not multibatchname and packages_dict) or (multibatchname and len(packages_dict) > 1):
                packages_string = ''
                i = 1
                for p in packages_dict:
                    packages_string += f"({i}){p} "
                    i += 1
                package_name = input(f"\tSpecify package name using integer or enter new package name - {packages_string}: ")
                while not package_name.isdigit() and not validateuserinput.is_valid_package_name(package_name):
                    package_name = input("\033[31mInput is neither integer nor valid package name, e.g. LTNS20250919_SHOW_DESCRIPTION. Try again: \033[0m")
                if package_name.isdigit():
                    package_name = list(packages_dict.keys())[int(package_name)-1]
                    multibatchname = package_name
            else:
                package_name = validateuserinput.card_package_name(input(f"\tEnter a package name: "))

            if input_path == iphone_temp_folder and not package_name.endswith("IPHONE"):
                package_name += "_IPHONE"
                print(f"\tPackage renamed to {package_name}")

            camera_card_number = validateuserinput.card_subfolder_name(
                input(f"\tEnter the corresponding card number or name on sticker (serialize from 1 if none): "))
            currentcards.append(camera_card_number)

            if package_name in packages_dict:
                # Edit existing key-value pair
                packages_dict[package_name]["cards"].append(camera_card_number)
                packages_dict[package_name]["input_paths"].append(input_path)

            # Check if in current batch options have already been run through using existing card
            if package_name in packages_dict:
                overlap = bool(set(currentcards[:-1]) & set(packages_dict[package_name]["cards"]))
            else:
                overlap = False

            if package_name not in packages_dict or (incomplete_multibatch and not overlap):
                new_package_dict = package_dict.copy()
                new_package_dict['cards'] = [camera_card_number]
                new_package_dict['input_paths'] = [input_path]

                if not multibatchname:
                    multibatch = input(
                        "\tIs this a multi-batch process? (i.e. does the number of cards/drives exceed the number of readers?) y/n: ").lower() == 'y'
                else:
                    multibatch = True
                last_batch = False

                if multibatch:
                    last_batch = input(
                        "\tIs this the last batch? y/n: ").lower() == 'y'
                    if not last_batch and package_name not in incomplete_multibatch:
                        incomplete_multibatch.append(package_name)
                    else:
                        if package_name in incomplete_multibatch and last_batch:
                            incomplete_multibatch.remove(package_name)

                if multibatch and not last_batch:
                    # Create key-value pair using default initialized values
                    packages_dict[package_name] = new_package_dict
                else:
                    do_dropbox = (input(
                        "\tUpload to dropbox? y/n: ")).lower() == 'y'

                    if do_dropbox:
                        emails = validateuserinput.emails(
                            input("\tList email(s) delimited by space or press enter to continue: "))
                        emails.extend(["library@tv.cuny.edu"])
                        #emails.extend(["aida.garrido@tv.cuny.edu"])
                        # Update key-value pair from default
                        new_package_dict['do_dropbox'] = True
                        new_package_dict['emails'] = emails

                    # Update key-value pair from default
                    new_package_dict['do_desktop_delete'] = True
                    new_package_dict['do_commands'] = True

                    packages_dict[package_name] = new_package_dict

if __name__ == "__main__":
    # Check if connected to servers
    archive_server = "/Volumes/CUNYTVMEDIA/archive_projects/camera_card_ingests"
    #archive_server = "/Users/aidagarrido/Desktop/camera_card_ingests"
    server_check(archive_server, "archive")

    #tiger_server = "/Users/aidagarrido/Desktop/Camera Card Delivery"
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

    startup()
    ingest()

    while incomplete_multibatch:
        currentcards = []
        for package in incomplete_multibatch:
            input(f"\033[31m{package} is an incomplete multibatch package. Insert next card(s) and press enter to continue.\033[0m")
            countdown(5)
            startup(package)
        ingest()

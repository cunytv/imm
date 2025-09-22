#!/usr/bin/env python3

import ingestcommands
import validateuserinput
import sys
import os
import hashlib
import subprocess
import shutil
import time
import datetime
import threading
import re
import filetype

class RestructurePackage:
    def __init__(self):
        self.FILES_DICT = []
        self.TRANSFER_OKAY = True
        self.TRANSFER_ERROR = []

        self.FILES_TO_TRANSFER = []

        self.PROG_FILES = 0
        self.TOTAL_FILES = 0
        self.PROG_BYTES = 0
        self.TOTAL_BYTES = 0
        self.CURRENT_PROCESS = ''


    # Checks if directory is a mounted volume
    def mounted_volume(self, directory):
        parent_device = os.stat(os.path.dirname(directory)).st_dev
        directory_device = os.stat(directory).st_dev
        return parent_device != directory_device

    # Creates a directory using package and card names from user input
    def create_output_directory(self, output_directory, package, subfolder):
        os.makedirs(output_directory + f'/{package}', exist_ok=True)
        os.makedirs(self.unique_directory_path(output_directory + f'/{package}' + f'/metadata/logs/{subfolder}'))
        os.makedirs(self.unique_directory_path(output_directory + f'/{package}' + f'/objects/{subfolder}'))

    def get_directory_stats(self, dir, transfer_type, files_dict=None, checksum=None):
        total_size = 0
        total_files = 0

        archive_nondict_file_bytes = 0

        for dirpath, _, filenames in os.walk(dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)

                if transfer_type == 'delivery' and self.file_type(fp) != 'objects':
                    continue

                if self.mac_system_metadata(fp) or os.path.getsize(fp) == 0:
                    continue

                try:
                    total_size += os.path.getsize(fp)
                    total_files += 1
                    self.FILES_TO_TRANSFER.append(fp)

                    if files_dict and all(f["dest"] != fp for f in files_dict):
                        archive_nondict_file_bytes += os.path.getsize(fp)
                except (OSError, FileNotFoundError):
                    pass

        if checksum and files_dict:
            self.TOTAL_BYTES = (total_size * 2) + archive_nondict_file_bytes
        elif checksum and not files_dict:
            self.TOTAL_BYTES = total_size * 3
        else:
            self.TOTAL_BYTES = total_size

        self. TOTAL_FILES = total_files

    # Checks if file is mac system metadata, e.g. .DS_STORE
    def mac_system_metadata(self, file):
        if "uuid" in file.lower() or file.startswith('.'):
            return True
        if any(pattern in file.lower() for pattern in
               ['tmp', 'spotlight', 'map', 'index', 'dbStr', '0.directory', '0.index', 'indexState', 'live.', 'reverse',
                'shutdown', 'store', 'plist', 'cab', 'psid.db', 'Exclusion', 'Lion']):
            return True

    # Checks if folder is empty
    def empty_folder(self, folder):
        return len(os.listdir(folder)) == 0

    # Checks if there is a file in the output directory with the same name and returns a unique file name with counter
    def unique_file_path(self, file_path):
        if not os.path.exists(file_path):
            return file_path

        # If file already exists
        counter = 2
        parts = file_path.rsplit(f".", 1)
        if bool(re.search(r"_\d+$", parts[0])):
            parts[0] = parts[0].rsplit("_", 1)[0]
        file_path = f"{parts[0]}_{counter}.{parts[1]}"
        while os.path.exists(file_path):
            file_name = file_path.rsplit(f"_{counter}", 1)[0]
            file_ext = file_path.rsplit(f".", 1)[1]
            counter += 1
            file_path = f"{file_name}_{str(counter)}.{file_ext}"
        return file_path

    # Checks if there is a directory in the package with the same name and returns a unique path with counter
    def unique_directory_path(self, directory_path):
        if not os.path.isdir(directory_path):
            return directory_path

        # If directory already exists
        counter = 2
        if bool(re.search(r"_\d+$", directory_path)):
            directory_path = directory_path.rsplit("_", 1)[0] + f"_{counter}"
        while os.path.exists(directory_path):
            counter += 1
            directory_path = directory_path.rsplit("_", 1)[0] + f"_{counter}"
        return directory_path

    # Determines file type using FFMPEG to bifurcate audio/video from all other kinds of file types
    def file_type(self, file_path):
        if filetype.is_av(file_path):
            return ("objects")
        else:
            return ("metadata/logs")

    # Copies file from source to destination, returns error and success bool tuple
    def copy_file(self, input_file_path, output_file_path, buffer_size=1024 * 1024):
        self.CURRENT_PROCESS = f'Transferring {os.path.basename(input_file_path)}'
        max_retries = 3
        retries = 0
        # Copy file from source to destination
        while retries < max_retries:
            try:
                if not os.path.exists(input_file_path):
                    raise FileNotFoundError(f"{input_file_path} does not exist.")

                with open(input_file_path, 'rb') as fsrc, open(output_file_path, 'wb') as fdst:
                    while True:
                        buf = fsrc.read(buffer_size)
                        if not buf:
                            break
                        fdst.write(buf)
                        self.PROG_BYTES += len(buf)
                # If successful, break out of the retry loop
                return None, True

            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    return e, False
                else:
                    time.sleep(2)  # Wait before retrying

    # Creates checksum, as per dropbox
    def calculate_sha256_checksum(self, file_path, block_size=4 * 1024 * 1024):
        self.CURRENT_PROCESS = f'Calculating checksum for {os.path.basename(file_path)}'

        # Get the total size of the file
        hash_object = hashlib.sha256()
        block_hashes = []

        # Open the file for reading in binary mode
        with open(file_path, 'rb') as f:
            while True:
                # Read a block of data
                block = f.read(block_size)
                if not block:
                    break  # End of file

                # Compute the hash of the block and store it
                block_hash = hashlib.sha256(block).digest()
                block_hashes.append(block_hash)

                # Update the total bytes read
                self.PROG_BYTES += len(block)
                # Update the main hash with the current block hash
                hash_object.update(block_hash)

        # Compute the final hash of the concatenated block hashes
        final_hash = hash_object.hexdigest()

        # Move to the next line after progress
        return final_hash

    # uses copy_file function to perform file transfer as per archive standards, e.g. checksum, file dict, error log
    def transfer_file(self, input_file_path, output_file_path, do_fixity, cs1=None):

        # Check if file path is unique, otherwise appends counter
        output_file_path = self.unique_file_path(output_file_path)

        # Checksum variables, with option to pass cs1 through method
        cs2 = None

        # File dict
        file_dict = {"orig": input_file_path,
                     "dest": output_file_path,
                     "checksum_o": cs1,
                     "checksum_d": cs2,
                     "fixity_pass": None
                     }

        # Create pre-transfer checksum or retrieve existing checksum from files_dict
        if do_fixity and cs1 is None:
            cs1 = self.calculate_sha256_checksum(input_file_path)
            file_dict['checksum_o'] = cs1

        # Transfer file using copy_file method, which returns boolean upon succesful or unsuccesful copy
        error, transfer_okay = self.copy_file(input_file_path, output_file_path)

        if not transfer_okay:
            self.TRANSFER_OKAY = False
            self.TRANSFER_ERROR += {
                "timestamp": str(datetime.datetime.now()),
                "error_type": type(error).__name__,
                "message": str(error),
            }
            file_dict['fixity_pass'] = False
            self.FILES_DICT.append(file_dict)
            return

        # If checksum validation unsuccessful, retry copy_file method up to 3 times
        max_retries = 3
        retries = 0
        while retries < max_retries:
            if do_fixity:
                cs2 = self.calculate_sha256_checksum(output_file_path)
                file_dict['checksum_d'] = cs2
                if cs1 == cs2:
                    file_dict["fixity_pass"] = True
                    self.FILES_DICT.append(file_dict)
                    return  # Exit on succesful copy
                else:
                    if retries >= max_retries:
                        file_dict["fixity_pass"] = False
                        self.FILES_DICT.append(file_dict)

                        self.TRANSFER_OKAY = False
                        self.TRANSFER_ERROR += {
                            "timestamp": str(datetime.datetime.now()),
                            "error_type": "Fixity check",
                            "message": f'Retries exceeded. See file {input_file_path.rsplit("/", 1)[1]}'
                        }
                        return  # Exit on max retries

                    retries += 1
                    os.remove(output_file_path)

                    error, transfer_okay = self.copy_file(input_file_path, output_file_path)
                    if not transfer_okay:
                        file_dict["checksum_d"] = None
                        file_dict["fixity_pass"] = False
                        self.FILES_DICT.append(file_dict)
                        self.TRANSFER_OKAY = False
                        self.TRANSFER_ERROR += {
                            "timestamp": str(datetime.datetime.now()),
                            "error_type": type(error).__name__,
                            "message": str(error),
                        }
                        return  # Exit on file copy failure
            else:
                return  # No fixity check, exit loop

    def archive_output_path(self, output_directory, output_package_name, output_subfolder_name, file):
        output_file_path = os.path.join(output_directory, output_package_name,
                                        self.file_type(file),
                                        output_subfolder_name, os.path.basename(file))
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        output_file_path = self.unique_file_path(output_file_path)
        return output_file_path

    def one2one_output_path(self, output_directory, input_file_path, input_folder_path):
        output_file_path = os.path.join(output_directory, os.path.relpath(input_file_path, input_folder_path))
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        output_file_path = self.unique_file_path(output_file_path)
        return output_file_path

    def delivery_output_path(self, output_directory, output_package_name, file):
        output_file_path = os.path.join(output_directory, output_package_name, file)
        os.makedirs(os.path.join(output_directory, output_package_name), exist_ok=True)
        output_file_path = self.unique_file_path(output_file_path)
        return output_file_path

    # core function, as of now, three copy types: archive, delivery, and one2one
    def restructure_copy(self, copy_type, input_folder_path, output_directory, output_package_name=None, output_subfolder_name=None,
                           do_fixity=None, do_delete=None, files_dict=None):

        self.get_directory_stats(input_folder_path, copy_type, files_dict, do_fixity)

        for file in self.FILES_TO_TRANSFER:
            # Initialize variables
            output_file_path = None
            cs1 = None

            if copy_type == "archive":
                output_file_path = self.archive_output_path(output_directory, output_package_name, output_subfolder_name, file)
            if copy_type == "delivery":
                output_file_path = self.delivery_output_path(output_directory, output_package_name, os.path.basename(file))
            if copy_type == "one2one":
                output_file_path = self.one2one_output_path(output_directory, file, input_folder_path)

            if files_dict:
                for f in files_dict:
                    if f['dest'] == file:  # Check the destination path
                        cs1 = f['checksum_d']
                        break

            self.PROG_FILES = self.PROG_FILES + 1
            self.transfer_file(file, output_file_path, do_fixity, cs1)

            if do_delete:
                os.remove(output_file_path)

            if do_delete and not self.mounted_volume(os.path.dirname(file)) and self.empty_folder(os.path.dirname(file)):
                os.rmdir(os.path.dirname(file))

if __name__ == "__main__":
    # Define variables
    # Array of input folder and output subfolder tuples (input, output)
    input_output_tuples = []
    package_name = None
    package_subfolder_name = None
    copy_type = input(f"1) archive, creates archival package with metadata and objects folders"
                      f"\n2) delivery, filters for audiovisual files and places them in a flat directory structure"
                      f"\n3) one2one, a one-to-one copy of the original directory"
                      f"\nSelect copy type: ")

    # Input folder to be restructured
    input_directory = validateuserinput.path(input("Input folder path: "))

    # Option for user to input custom output directory or to default to input directory
    output_directory = input(f"Output directory path. Or press enter to save in default directory {input_directory.rsplit('/', 1)[0]}: ")
    if output_directory == '':
        output_directory = input_directory.rsplit('/', 1)[0]
    else:
        output_directory = validateuserinput.path(output_directory)

    while copy_type != '1' and copy_type != '2' and copy_type != '3':
        input(f"Select one of the following numbers 1) archive 2) delivery 3) one2one: ")
    if copy_type == '1':
        copy_type = 'archive'
        # Package follow the structure of package_name/metadata | objects /subfolder_name
        # The files from the input folder path are saved in the subfolder_name
        package_name = validateuserinput.card_package_name(input(f"Enter package name: "))
        package_subfolder_name = validateuserinput.card_subfolder_name(
            input(f"Enter subfolder name (or serialize from 1 if none): "))
        input_output_tuples.append((input_directory, package_name, package_subfolder_name))
    elif copy_type == '2':
        copy_type = 'delivery'
        package_name = validateuserinput.card_package_name(input(f"Enter output folder name: "))
        input_output_tuples.append((input_directory, package_name, package_subfolder_name))
    else:
        copy_type = 'one2one'
        input_output_tuples.append((input_directory, package_name, package_subfolder_name))


    # Continue processing additional package subfolders if user types 'y'
    if copy_type == 'delivery' or copy_type == 'archive':
        cont = (input("Process additional folders for this package? y/n: ")).lower() == 'y'
        while cont:
            input_directory = validateuserinput.path(input("Input folder path: "))
            if copy_type == 'archive':
                package_subfolder_name = validateuserinput.card_subfolder_name(input(f"Enter subfolder name: "))
            input_output_tuples.append((input_directory, package_name, package_subfolder_name))
            cont = (input("Process additional folders for this package? y/n: ")).lower() == 'y'

    # Additional file processing options
    mdo_fixity = True
    mdo_delete = False

    # Create package object
    package = RestructurePackage()

    # Begin file processing
    for tuple in input_output_tuples:
        package.restructure_copy(copy_type, tuple[0], output_directory, tuple[1], tuple[2], mdo_fixity, mdo_delete)

    # If user wants commands to run and transfer occured with no issues
    if copy_type == 'archive' and package.TRANSFER_OKAY:
        ingestcommands.makewindow(os.path.join(output_directory, package_name))
        ingestcommands.makemetadata(os.path.join(output_directory, package_name))
        ingestcommands.makechecksumpackage(os.path.join(output_directory, package_name))

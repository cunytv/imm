#!/usr/bin/env python3

import ingestcommands
import validateuserinput
import sys
import os
import hashlib
import subprocess
import shutil
import re

class RestructurePackage:
    def __init__(self):
        self.FILES_DICT = {}
        self.TRANSFER_OKAY = True

    # Checks if directory is a mounted volume
    def mounted_volume(self, directory):
        parent_device = os.stat(os.path.dirname(directory)).st_dev
        directory_device = os.stat(directory).st_dev
        return parent_device != directory_device

    # Creates a directory using package and card names from user input
    def create_output_directory(self, output_directory, package, subfolder):
        os.makedirs(output_directory + f'/{package}', exist_ok=True)
        os.makedirs(self.unique_directory_path(output_directory + f'/{package}' + f'/metadata/{subfolder}'))
        os.makedirs(self.unique_directory_path(output_directory + f'/{package}' + f'/objects/{subfolder}'))

    # Checks if file is mac system metadata, e.g. .DS_STORE
    def mac_system_metadata(self, file):
        if "uuid" in file.lower() or file.startswith('.'):
            return True

    # Checks if folder is empty
    def empty_folder(self, folder):
        return len(os.listdir(folder)) == 0

    # Checks if there is a file in the output directory with the same name and returns a unique file name with counter
    def unique_file_path(self, file_path):
        # If there is already a file in the output directory with the same name
        counter = 2
        while os.path.exists(file_path):
            parts = file_path.rsplit(".", 1)
            file_path = parts[0] + f"_{str(counter)}." + parts[1]
            counter += 1
        return file_path

    # Checks if there is a directory in the package with the same name and returns a unique path with counter
    def unique_directory_path(self, directory_path):
        # If there is already a file in the output directory with the same name
        counter = 2
        while os.path.exists(directory_path):
            directory_path = directory_path + f"_{counter}"
            counter += 1
        return directory_path


    # Determines file type using FFMPEG to bifurcate audio/video from all other kinds of file types
    def file_type(self, file_path):

        # Number of streams
        command = f"ffprobe -loglevel quiet {file_path} -show_entries format=nb_streams -of default=nw=1:nk=1"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True)
        nb_streams = process.stdout.readline().strip()

        # Stream duration
        command = f"ffprobe -loglevel quiet {file_path} -show_entries stream=duration -of default=nw=1:nk=1"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True)
        duration = process.stdout.readline().strip()

        if not nb_streams:
            nb_streams = 0
        else:
            nb_streams = int(nb_streams)
        if not duration:
            duration = 0
        else:
            duration = float(duration)

        print(file_path)
        print(nb_streams)
        print(duration)
        print()
        if nb_streams >= 1 and duration > 0:
            return ("objects")
        else:
            return ("metadata")

    # Creates checksum
    def calculate_sha256_checksum(self, file_path):
        # Open the file for reading in binary mode
        total_size = os.path.getsize(file_path)
        block_size = 4096  # Adjust as needed
        hash_object = hashlib.sha256()
        bytes_read = 0

        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(block_size)
                if not chunk:
                    break
                hash_object.update(chunk)
                bytes_read += len(chunk)
                progress = min(int((bytes_read / total_size) * 100), 100)
                sys.stdout.write("\rChecksum progress: [{:<50}] {:d}% ".format('=' * (progress // 2), progress))
                sys.stdout.flush()

        return (hash_object.hexdigest())

    # Copies files into package structure, performs fixity check (optional), deletes old directory (optional)
    def restructure_folder(self, input_folder_path, output_directory, output_package_name, output_subfolder_name,
                           do_fixity, do_delete):
        for foldername, subfolders, filenames in os.walk(input_folder_path, topdown=False):
            for file in filenames:
                if self.mac_system_metadata(file):
                    os.remove(os.path.join(foldername, file))
                else:
                    print(f'Transferring file {file}')
                    # Construct input and output paths
                    input_file_path = os.path.join(foldername, file)
                    output_file_path = os.path.join(output_directory, output_package_name, self.file_type(os.path.join(foldername, file)),
                                                    output_subfolder_name, file)
                    # Check if file path is unique, otherwise appends counter
                    output_file_path = self.unique_file_path(output_file_path)
                    # Checksum variables
                    cs1 = None
                    cs2 = None

                    # Create pre-transfer checksum
                    if do_fixity:
                        cs1 = self.calculate_sha256_checksum(input_file_path)

                    # Copy file from source to destination, iterate to next file if error
                    try:
                        shutil.copy2(input_file_path, output_file_path)
                    except Exception as e:
                        self.FILES_DICT[(input_file_path, output_file_path)] = [cs1, cs2, False]
                        self.TRANSFER_OKAY = False
                        print(f"An error occurred while copying the file: {e}")
                        continue

                    # Create post-transfer checksum
                    if do_fixity:
                        cs2 = self.calculate_sha256_checksum(output_file_path)
                        if cs1 == cs2:
                            print(f'File {file} transferred and passed fixity check')
                            self.FILES_DICT[(input_file_path, output_file_path)] = [cs1, cs2, True]
                            if do_delete:
                                os.remove(input_file_path)
                        else:
                            print(f'File {file} transferred but did not pass fixity check')
                            self.FILES_DICT[(input_file_path, output_file_path)] = [cs1, cs2, False]
                            self.TRANSFER_OKAY = False
                    else:
                        self.FILES_DICT[(input_file_path, output_file_path)] = [cs1, cs2, None]
                        if do_delete:
                            os.remove(input_file_path)

                if do_delete and not self.mounted_volume(foldername) and self.empty_folder(foldername):
                    os.rmdir(foldername)


if __name__ == "__main__":
    # Create package object
    package = RestructurePackage()

    # Array of input folder and output subfolder tuples (input, output)
    input_output_tuples = []

    # Input folder to be restructured
    input_directory = validateuserinput.path(input("Input folder path: "))

    # Option for user to input custom output directory or to default to input directory
    output_directory = input(f"Output directory path. Or press enter to save in default directory {input_directory.rsplit('/', 1)[0]}: ")
    if output_directory == '':
        output_directory = input_directory.rsplit('/', 1)[0]
    else:
        output_directory = validateuserinput.path(output_directory)

    # Package follow the structure of package_name/metadata | objects /subfolder_name
    # The files from the input folder path are saved in the subfolder_name
    package_name = validateuserinput.card_package_name(input(f"Enter package name: "))
    package_subfolder_name = validateuserinput.card_subfolder_name(input(f"Enter subfolder name (or serialize from 1 if none): "))
    input_output_tuples.append((input_directory, package_subfolder_name))

    # Continue processing additional package subfolders if user types 'y'
    cont = (input("Process additional folders for this package? y/n: ")).lower() == 'y'
    while cont:
        input_directory = validateuserinput.path(input("Input folder path: "))
        package_subfolder_name = validateuserinput.card_subfolder_name(input(f"Enter subfolder name: "))
        input_output_tuples.append((input_directory, package_subfolder_name))
        cont = (input("Process additional folders for this package? y/n: ")).lower() == 'y'

    # Additional file processing options
    do_fixity = (input("Fixity check before and after transfer? y/n: ")).lower() == 'y'
    do_delete = (input("Delete folder after succesful transfer? y/n: ")).lower() == 'y'
    do_commands = (input("Run makeyoutube, makemetdata, checksumpackage? y/n: ")).lower() == 'y'

    # Begin file processing
    for tuple in input_output_tuples:
        package.create_output_directory(output_directory, package_name, package_subfolder_name)
        package.restructure_folder(tuple[0], output_directory, package_name, tuple[1], do_fixity, do_delete)

    # If user wants commands to run and transfer occured with no issues
    if do_commands and package.TRANSFER_OKAY:
        ingestcommands.commands(os.path.join(output_directory, package_name))

    #print error log in output directory

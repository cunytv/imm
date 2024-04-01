#!/usr/bin/env python3

import os
import subprocess

# Performs CUNY TV bash scripts makeyoutube, makemetadata, and checksumpackage
def commands(directory):
    # Makeyoutube
    command = f"makeyoutube -t {directory}"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True)
    # Print the output line by line in real-time
    for line in process.stdout:
        print(line, end='')
    # Wait for the process to finish
    process.wait()
    # Check the return code
    if process.returncode == 0:
        print("\nCommand executed successfully")
    else:
        print("\nCommand failed with return code:", process.returncode)

    # Makemetadata
    command = f"makemetadata {directory}"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True)
    for line in process.stdout:
        print(line, end='')
    process.wait()
    if process.returncode == 0:
        print("\nCommand executed successfully")
    else:
        print("\nCommand failed with return code:", process.returncode)

    # Checksumpackage
    command = f"checksumpackage {directory}"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True)
    for line in process.stdout:
        print(line, end='')
    process.wait()
    if process.returncode == 0:
        print("\nCommand executed successfully")
    else:
        print("\nCommand failed with return code:", process.returncode)

if __name__ == "__main__":
    input_directory = input("Input folder path(s): ")
    input_directories = input_directory.split()

    for directory in input_directories:
        commands(directory)

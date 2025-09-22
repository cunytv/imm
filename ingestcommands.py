#!/usr/bin/env python3

import os
import subprocess

import validateuserinput


# Performs CUNY TV bash scripts makewindow, makemetadata, and checksumpackage
def makewindow(directory):
    command = f"makewindow {directory}"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True)
    for line in process.stdout:
        if 'time=' in line and 'bitrate=' in line:
            line = line.rstrip('\n')
            print(line, end='\r', flush=True)
        else:
            print(line, end='')
    process.wait()

    if process.returncode == 0:
        return True, None
    else:
        return False, process.returncode
def makemetadata(directory):
    command = f"makemetadata {directory}"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True)
    for line in process.stdout:
        if line.endswith(".left") or not line.strip():
            line = line.rstrip('\n')
            print(line, end='\r', flush=True)
        else:
            print(line, end='')
    process.wait()
    if process.returncode == 0:
        return True, None
    else:
        return False, process.returncode

def makechecksumpackage(directory):
    command = f"checksumpackage {directory}"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True)
    for line in process.stdout:
        if line.endswith(".left") or not line.strip():
            line = line.rstrip('\n')
            print(line, end='\r', flush=True)
        else:
            print(line, end='')
    process.wait()
    if process.returncode == 0:
        return True, None
    else:
        return False, process.returncode

if __name__ == "__main__":
    input_directory = validateuserinput.path(input("Input folder path(s): "))
    input_directories = input_directory.split()

    for directory in input_directories:
        makewindow(directory)
        makemetadata(directory)
        makechecksumpackage(directory)

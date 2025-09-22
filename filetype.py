#!/usr/bin/env python3

import subprocess

# Determines if string can be cast to int
def can_cast_to_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# Determines if file is AV or not
def is_av(file_path):
    # Number of streams
    command = ["ffprobe", "-loglevel", "quiet", file_path, "-show_entries", "format=nb_streams", "-of", "default=nw=1:nk=1"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    nb_streams = process.stdout.readline()

    # Stream duration
    command = ["ffprobe", "-loglevel", "quiet", file_path, "-show_entries", "stream=duration", "-of", "default=nw=1:nk=1"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    duration = process.stdout.readline()

    if not can_cast_to_float(nb_streams):
        nb_streams = 0
    else:
        nb_streams = int(nb_streams)
    if not can_cast_to_float(duration):
        duration = 0
    else:
        duration = float(duration)

    if nb_streams >= 1 and duration > 0:
        return True
    else:
        return False

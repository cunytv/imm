#!/usr/bin/env python3

import subprocess
# Returns disks mounted within the last 10 minutes
def mounted_paths():
    # Define the command to be executed
    command = """log show --last 10m --info --predicate 'eventMessage contains "mounted"'"""

    # Execute the command and capture its output
    output = subprocess.check_output(command, shell=True)

    # Convert the output bytes to string
    output_str = output.decode("utf-8")
    rows = output_str.split('\n')

    # Store mount_paths
    mount_paths = []

    for row in rows:
        if 'diskarbitrationd' in row and 'success' in row and 'unmounted' not in row:
            mount_path = row.split('= ')[1:][0]
            mount_path = mount_path.split(',')[:1][0]
            mount_paths.append(mount_path)

    return mount_paths

# Joins data from the previous command to return volume paths

def volume_paths ():
    mount_paths = mounted_paths()

    # Define the command to be executed
    command = "mount"

    # Execute the command and capture its output
    output = subprocess.check_output(command, shell=True)

    # Convert the output bytes to string
    output_str = output.decode("utf-8")
    rows = output_str.split('\n')

    # Array of volume_paths
    volume_paths = []

    for row in rows:
        row_path = row.split(' ')[:1][0]
        if row_path in mount_paths:
            volume_path = row.split('on ')[1:][0]
            volume_path = volume_path.split(' (')[:1][0]
            volume_paths.append(volume_path)

    return volume_paths

if __name__ == "__main__":
    volume_paths = volume_paths()

    print('Detected: ')
    for path in volume_paths:
        print(path)

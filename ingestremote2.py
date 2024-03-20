import time
import sys
import os
import hashlib
import detectrecentlyinserteddrives
import subprocess
import shutil

# next list all files in directory, populate dictionary, do checksum, move, then checksum again
# shutil.copy2(source_file, destination_folder)

cards_dict = {}
server = "/Volumes/CUNYTV_Media/archive_projects/sxs_ingests-unique"

objects_v = ['mxf', 'mp4', 'avi', 'mkv', 'wmv', 'mov', 'flv', 'webm', '3gp', 'mpeg', 'vob', 'rm', 'ogv', 'asf', 'mpg',
             'm4v']
objects_a = ['mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a', 'wma', 'aiff', 'ape', 'ac3', 'amr', 'au', 'midi', 'mp2', 'ra']
objects_i = ['jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg', 'webp', 'ico', 'jpg', 'tga', 'psd', 'pdf', 'eps', 'ai', 'raw']
metadata = ['exif', 'xmp', 'iptc', 'json', 'xml', 'csv', 'yaml', 'bim', 'md', 'log', 'txt', 'ppn', 'smi', 'motn']

do_checksum = False
do_commands = False
failed_checks0m_f = []
failed_checks0m_c = []


def server_check():
    if not os.path.exists(server):
        print(f'You might not be connected to the server. Reconnect and try again')
        sys.exit(1)

def countdown(s):
    for i in range(s, 0, -1):
        print(f"{i}...", end='', flush=True)
        time.sleep(1)
    print()

def directory_create(p, c):
    os.makedirs(server + f'/{p}', exist_ok=True)
    os.makedirs(server + f'/{p}' + f'/metadata/{c}')
    os.makedirs(server + f'/{p}' + f'/objects/{c}')

def calculate_sha256_checksum(file_path):
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

    print()
    return (hash_object.hexdigest())


def file_type(f):
    f = f.split('.')[1]
    f = f.lower()

    if f in objects_v or f in objects_a or f in objects_i:
        return ('objects')
    elif f in metadata:
        return ('metadata')
    else:
        return ('')


def transfer(d='/Volumes'):
    for c in cards_dict:
        path = os.path.join(d, c)
        for foldername, subfolders, filenames in os.walk(path):
            for f in filenames:
                if not f.startswith('.') and '.' in f:

                    print(f'Transferring file {f}')
                    fp = os.path.join(foldername, f)

                    if do_checksum:
                        cs1 = calculate_sha256_checksum(fp)

                    d = os.path.join(server, cards_dict[c][0], file_type(f), cards_dict[c][1])
                    shutil.copy2(fp, d)

                    if do_checksum:
                        fp2 = os.path.join(d, f)
                        cs2 = calculate_sha256_checksum(fp2)

                        cards_dict[c][2][f] = [cs1, cs2]

                        if cs1 == cs2:
                            print(f'File {f} transferred and passed fixity check')
                        else:
                            print(f'File {f} transferred but did not pass fixity check')
                            failed_checks0m_f.append(fp2)
                            failed_checks0m_c.append(cards_dict[c][0])


def eject(d='/Volumes'):
    print()
    for c in cards_dict:
        path = os.path.join(d, c)
        subprocess.run(["diskutil", "eject", path])

    message = f"Content transferred. Safe to eject all card(s)"
    notification(message)


def notification(message):
    applescript = f'''
            display notification "{message}" with title "Ingest Notifcation"
        '''
    subprocess.run(["osascript", "-e", applescript])


def commands():
    for card in cards_dict:
        if cards_dict[card][0] not in failed_checks0m_c:

            d = os.path.join(server, cards_dict[card][0])

            command = f"makeyoutube -t {d}"
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

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

            command = f"makemetadata {d}"
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

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

            command = f"checksumpackage {d}"
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

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

            message = f"{cards_dict[card][0]} finished ingesting (makeyoutube, makemetadata, checksumpackage)"
            notification(message)


if __name__ == "__main__":
    # Check if connected to server
    server_check()

    # Continue processing camera cards until user types 'q' for quit
    cont = ''

    # Prompt user
    input("Please insert camera card(s). Press enter to continue. ")

    while cont != 'q':
        # Buffer to give sufficient time to mount drive
        countdown(5)

        # Detect inserted drive
        volumesnew = DetectRecentlyInsertedDrives.volume_paths()

        if volumesnew:
            print(f"{len(volumesnew)} card(s) detected")

            for card in volumesnew:
                print(f"- {card}")
                i1 = (input("\tFixity check before and after transfer? y/n: ")).lower()
                i2 = (input("\tRun makeyoutube, makemetdata, checksumpackage? y/n: ")).lower()

                if i1 == 'y':
                    do_checksum = True
                else:
                    do_checksum = False

                if i2 == 'y':
                    do_commands = True
                else:
                    do_commands = False

                package_name = input(f"\tEnter a package name: ")
                camera_card_number = input(f"\tEnter the corresponding card number on sticker (serialize from 1 if none): ")
                camera_card_number = camera_card_number.replace(" ", "_")

                files_dict = {}
                cards_dict[card] = [package_name, camera_card_number, files_dict]
                directory_create(package_name, camera_card_number)

            transfer()
            eject()

            if i2 == 'y':
                commands()

        else:
            print("No cards detected")

        cont = input("Insert another card and press enter to continue or q to quit. ")
        cards = {}
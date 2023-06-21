#!/usr/bin/env python3

"""
    ingestremote.py moves files from a camera card and organizes them into a package. 
    Last Revised: 2023-06-21
"""

import sys
import os
import subprocess
import shutil 

cameradirectory = "/Volumes/Untitled"

# identify camera type

for cameratype in os.listdir(cameradirectory):

	# identify workflow

	searchstring_xdroot = 'XDROOT'

	searchstring_BPAV = 'BPAV'

	# XQD Workflow

	if searchstring_xdroot in cameratype:

		print(f'this is a XAVC (SONY)')

		inputdirectory = "/Volumes/Untitled/"

		package_name = input("Enter a package name for this material: ")

		outputdirectory = "/Volumes/CUNYTV_Media/archive_projects/sxs_ingests-unique/ingestremotetest"
		
		package_destination = os.path.join(outputdirectory, package_name)

		os.makedirs(package_destination)

		
		###### fix while loop later

		camera_card_number = ''

		while camera_card_number != 'DONE':

			camera_card_number = input("Enter the card number. If finished ingesting press control C: ")

			camera_card_number_path = os.path.join(package_destination, camera_card_number)

			os.makedirs(camera_card_number_path)

			subprocess.call(["rsync", "-rtvP", inputdirectory, camera_card_number_path])

			
			# create an objects directory and move files into folder		

			objectspath = os.path.join(package_destination, "objects")
			print(f'this is the {objectspath}')

			if not os.path.exists(objectspath):
				os.mkdir(objectspath)

			if os.path.exists(objectspath) and os.path.exists(camera_card_number_path):
				shutil.move(camera_card_number_path, objectspath)

			
			# create metadata directory and transfer logs

			metadata_directory = os.path.join(package_destination, "metadata")

			if not os.path.exists(metadata_directory):
				os.mkdir(metadata_directory)

			camera_log_path = os.path.join(metadata_directory, camera_card_number)

			if not os.path.exists(camera_log_path):
				os.makedirs(camera_log_path)

			camera_log_path_xdroot = os.path.join(camera_log_path, "logs/camera/XDROOT")

			camera_log_path_clip = os.path.join(camera_log_path, "logs/camera/XDROOT/Clip")

			if not os.path.exists(camera_log_path_clip):
				os.makedirs(camera_log_path_clip)
				
			for root, dirs, files, in os.walk(objectspath):

				for name in files:
					file_name = os.path.join(root,name)

					searchstring_cueup = 'CUEUP.XML'
					searchstring_discmeta = 'DISCMETA.XML'
					searchstring_mediapro = 'MEDIAPRO.XML'

					if searchstring_cueup in file_name:
						try:
							shutil.move(file_name, camera_log_path_xdroot)
						except shutil.Error:
							continue

					if searchstring_discmeta in file_name:
						try: 
							shutil.move(file_name, camera_log_path_xdroot)
						except shutil.Error:
							continue

					if searchstring_mediapro in file_name:
						try:
							shutil.move(file_name, camera_log_path_xdroot)
						except	shutil.Error:
							continue

					if file_name.endswith('.BIM'):
						try:
							shutil.move(file_name, camera_log_path_clip)
						except shutil.Error:
							continue

					searchstring_clip = 'Clip'

					if searchstring_clip in file_name:
						if file_name.endswith('.XML'):
							try:
								shutil.move(file_name, camera_log_path_clip)
							except shutil.Error:
								continue	


			# delete empty folders

			for root, dirs, files in os.walk(package_destination, topdown=False):
				
			 	for empty in dirs:
			  		if len(os.listdir(os.path.join(root, empty))) == 0:
			  			os.rmdir(os.path.join(root, empty))
			  		else: 
			  			print(f'{(os.path.join(root,empty))} is not empty. These will not be removed')


	elif searchstring_BPAV in cameratype:
		
		print(f'this is SONY XDCAM BPAV. These will have to be transcoded')

		inputdirectory = "/Volumes/Untitled/"

		package_name = input("Enter a package name for this material: ")

		outputdirectory = "/Volumes/CUNYTV_Media/archive_projects/sxs_ingests-unique/ingestremotetest"
		
		package_destination = os.path.join(outputdirectory, package_name)

		os.makedirs(package_destination)

		camera_card_number = input("Enter the card number. If finished ingesting press control C: ")

		camera_card_number_path = os.path.join(package_destination, camera_card_number)

		os.makedirs(camera_card_number_path)

		subprocess.call(["rsync", "-rtvP", inputdirectory, camera_card_number_path])

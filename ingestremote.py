#!/usr/bin/env python3

import sys
import os
import subprocess
import shutil 

cameradirectory = "/Volumes/"

for cameratype in os.listdir(cameradirectory):

	searchstring_xdroot = 'Untitled'

	if searchstring_xdroot in cameratype:

		print(f'this is an XAVC (SONY)')

		inputdirectory = "/Volumes/Untitled/"

		package_name = input("Enter a package name for this material: ")

		outputdirectory = "/Volumes/CUNYTV_Media/archive_projects/sxs_ingests-unique/ingestremotetest"
		
		package_destination = os.path.join(outputdirectory, package_name)

		os.makedirs(package_destination)

		camera_card_number = input("Enter the card number: ")

		camera_card_number_path = os.path.join(package_destination, camera_card_number)

		os.makedirs(camera_card_number_path)

		subprocess.call(["rsync", "-rtvP", inputdirectory, camera_card_number_path])

		metadata_directory = os.path.join(package_destination, "metadata")

		if not os.path.exists(metadata_directory):
			os.mkdir(metadata_directory)

		camera_log_path = os.path.join(metadata_directory, camera_card_number)

		os.makedirs(camera_log_path)

		camera_log_path_xdroot = os.path.join(camera_log_path, "logs/camera/XDROOT")

		camera_log_path_clip = os.path.join(camera_log_path, "logs/camera/XDROOT/Clip")

		if not os.path.exists(camera_log_path_clip):
			os.makedirs(camera_log_path_clip)

		for root, dirs, files, in os.walk(package_destination):

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

		# create an objects directory	
			
		#objectspath = os.path.join(package_destination, "objects")
		#print(f'this is the {objectspath}')

		#if not os.path.exists(objectspath):
		#	os.mkdir(objectspath)

		# delete empty folders


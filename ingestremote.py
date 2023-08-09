#!/usr/bin/env python3

"""
    ingestremote.py moves files from a camera card and organizes them into a package. 
    Last Revised: 2023-08-07
"""

import sys
import os
import subprocess
import shutil 

package_name = input("Enter a package name for this material: ")

outputdirectory = "/Volumes/CUNYTV_Media/archive_projects/sxs_ingests-unique"

if not os.path.exists(outputdirectory):
	print(f'you might not be connected to the server. Reconnect and try again')

package_destination = os.path.join(outputdirectory, package_name)

os.makedirs(package_destination)

cameradirectory = "/Volumes/"

for cameratype in os.listdir(cameradirectory):

	searchstring_untitled = "Untitled"

	if searchstring_untitled in cameratype:

		cameracardinput = os.path.join(cameradirectory, cameratype)

		# identify camera card type

		for cameracard_id in os.listdir(cameracardinput):

			searchstring_xdroot = 'XDROOT'
			searchstring_BPAV = 'BPAV'

			# XQD workflow

			if searchstring_xdroot in cameracard_id:
				print(f'This is an XAVC. These files will rsync to the sxs_ingests-unique folder. Logs will be moved to metadata folder')
			
				sourcedirectory = "/Volumes/Untitled/"

				camera_card_number = ''

				while camera_card_number != 'quit':

					camera_card_number = input("Enter the card number. If finished ingesting, type 'quit': ")

					if camera_card_number != 'quit':

						camera_card_number_path = os.path.join(package_destination, camera_card_number)

						os.makedirs(camera_card_number_path)

						subprocess.call(["rsync", "-rtvP", "--exclude=.*", sourcedirectory, camera_card_number_path])

						# create an objects directory and move files into folder		

						objectspath = os.path.join(package_destination, "objects")

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


			#BPAV workflow. This is a workaround to handle shows shot in the radio studio. This will be revised.    				  					
			
			if searchstring_BPAV in cameracard_id:
				print(f'This is SONY XDCAM BPAV. These files will rsync to the sxs_ingests-unique and will be rewrapped')

				sourcedirectory = "/Volumes/Untitled/"

				camera_card_number = ''

				while camera_card_number != 'quit':

					camera_card_number = input("Enter the card number. If finished ingesting, type 'quit': ")

					if camera_card_number != 'quit':
					
						camera_card_number_path = os.path.join(package_destination, camera_card_number)

						os.makedirs(camera_card_number_path)

						subprocess.call(["rsync", "-rtvP", "--exclude=.*", sourcedirectory, camera_card_number_path])

						# create an objects directory and move files into folder		

						objectspath = os.path.join(package_destination, "objects")

						if not os.path.exists(objectspath):
							os.mkdir(objectspath)

						if os.path.exists(objectspath) and os.path.exists(camera_card_number_path):
							shutil.move(camera_card_number_path, objectspath)

						for root, dirs, files, in os.walk(objectspath):
							
							for name in files:
 								file_name = os.path.join(root,name)
 								if file_name.endswith('.MP4'):
 									print(file_name)
 									subprocess.call(["makeprores", file_name])						


	# SSD workflow

	else: 
		searchstring_ssd = "DiskHFS"

		if searchstring_ssd in cameratype:
			print('This material is from an SSD. Will rsync to the sxs_ingests-unique folder')

			inputdirectory = "/Volumes/DiskHFS/"

			camera_card_number = ''

			while camera_card_number != 'quit':

				camera_card_number = input("Enter the card number. If finished ingesting, type 'quit': ")
	
				if camera_card_number != 'quit':

 					camera_card_number_path = os.path.join(package_destination, camera_card_number)

 					os.makedirs(camera_card_number_path)

 					for items in os.listdir(inputdirectory):

 						itemstomove = os.path.join(inputdirectory, items)
 						print(f'this is what i want to move {itemstomove}')

 						subprocess.call(["rsync", "-rtvP", "--exclude=.*", itemstomove, camera_card_number_path])

 					#create an objects directory and move files into folder		

 					objectspath = os.path.join(package_destination, "objects")
 					print(f'this is the {objectspath}')

 					if not os.path.exists(objectspath):
 						os.mkdir(objectspath)

 					if os.path.exists(objectspath) and os.path.exists(camera_card_number_path):
 						shutil.move(camera_card_number_path, objectspath)

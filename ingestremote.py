#!/usr/bin/env python3

import sys
import os
import subprocess
import shutil 

cameradirectory = "/Users/catrionaschlosser/Desktop/restructuretest/"

for cameratype in os.listdir(cameradirectory):

	searchstring_xdroot = 'XDROOT'

	if searchstring_xdroot in cameratype:

		print(f'this is an XAVC (SONY)')

		package_name = input("Enter a package name for this material: ")

		outputdirectory = "/Volumes/G-DRIVE/sxs"
		
		package_destination = os.path.join(outputdirectory, package_name)

		os.makedirs(package_destination)

		camera_card_number = input("Enter the card number: ")

		camera_card_number_path = os.path.join(package_destination, camera_card_number)
		print(camera_card_number_path)

		os.makedirs(camera_card_number_path)
		
		


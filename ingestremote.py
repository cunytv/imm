#!/usr/bin/env python3

import sys
import os
import subprocess
import shutil 

cameradirectory = "/Users/catrionaschlosser/Desktop/restructuretest/"

#outputdirectory = "Users/catrionaschlosser/Desktop/xdrootoutput"

for cameratype in os.listdir(cameradirectory):
#	print(cameratype)

	searchstring_xdroot = 'XDROOT'

	if searchstring_xdroot in cameratype:

		print(f'this is an XAVC (SONY)')

		package_name = input("Enter a package name for this material: ")
		#print(package_name) 

		#if not os.path.exists(package_destination):
		#	os.makedirs(package_destination)

		package_destination = os.path.join(os.getenv("HOME")), r"Desktop/xdrootoutput/"
		print(package_destination)

		#package_destination = os.path.join(outputdirectory, package_name)
		#print(package_destination)
		
		


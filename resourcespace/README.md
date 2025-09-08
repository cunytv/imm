# resourcespace

## Introduction

This is a collection of scripts and documentation on CUNY TV's resourcespace installation

## Contents

### Start up

1. Start the web server
-     sudo apachectl start

2. Start the database
-     brew services start mysql
-     /opt/homebrew/opt/mysql/bin/mysqld_safe --datadir\=/opt/homebrew/var/mysql)

3. Connect to servers
The resourcespace filestore, which is the folder where all media assets are saved, is located on the CUNYTVMEDIA server. The website will not work if the resourcespace computer is not connected that server.
<img width="392" height="391" alt="image" src="https://github.com/user-attachments/assets/d3deb44b-5927-49b3-ab07-e409262535e4" />

4. In case of error, check log
-     open /var/log/resourcespace/resourcespace.log
-     tail -n 100 /var/log/resourcespace/resourcespace.log


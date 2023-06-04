#!/bin/python3
#
# A script to tarball each directory in the given backup directory location, encrypt each tar file with GPG using my own public key and upload those encrypted files to my Dropbox in the cloud.
#
# script writtin by Coen Stam.
# github@theautomation.nl
#

import os
import logging
import tarfile
from datetime import date
import gnupg

# Define the variables
LOG_FILE_LOCATION = os.getenv('LOG_FILE_LOCATION', './backup-to-cloud.log')
BACKUP_DIRECTORY = os.getenv(
    'BACKUP_DIRECTORY', '/home/coen/storage-server/coen/backups-test')
GPG_RECIPIENT = os.getenv('GPG_RECIPIENT', 'gpg@theautomation.nl')
DROPBOX_REMOTE_LOCATION = os.getenv('DROPBOX_REMOTE_LOCATION', '')
# Get the log level from the environment variable
log_level_str = os.getenv('LOG_LEVEL', 'INFO')

# Convert the log level string to the corresponding constant value
log_level = getattr(logging, log_level_str.upper(), logging.INFO)

# Configure the logging system
logging.basicConfig(
    level=log_level, format='%(asctime)s - %(levelname)s - %(message)s', filename=LOG_FILE_LOCATION)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

# Log variable names and values
logging.debug("The following environment variables have been configured:\n"
              "LOG_FILE_LOCATION: %s\n"
              "BACKUP_DIRECTORY: %s\n"
              "GPG_RECIPIENT: %s\n"
              "DROPBOX_REMOTE_LOCATION: %s",
              LOG_FILE_LOCATION, BACKUP_DIRECTORY, GPG_RECIPIENT, DROPBOX_REMOTE_LOCATION)

# Check if the directory exists
if not os.path.exists(BACKUP_DIRECTORY):
    # Create the directory
    os.makedirs(BACKUP_DIRECTORY)
    logging.info("Backup directory created: %s", BACKUP_DIRECTORY)
else:
    logging.debug("Backup directory exists: %s", BACKUP_DIRECTORY)

# Loop through all files and directories within the parent directory
for item in os.listdir(BACKUP_DIRECTORY):
    item_path = os.path.join(BACKUP_DIRECTORY, item)
    if os.path.isdir(item_path):
        # Check if the directory is not empty
        if os.listdir(item_path):
            # Process the non-empty directory
            logging.info("Non-empty directory: %s", item_path)

            # Get the name of the directory that is not empty
            directory_name = os.path.basename(item_path)

            # Get the current date
            current_date = date.today().strftime("%Y-%m-%d")

            # Create the tar archive with the same name as the directory
            output_file = os.path.join(
                BACKUP_DIRECTORY, f"{current_date}_{directory_name}.tar")
            with tarfile.open(output_file, "w") as tar:
                tar.add(item_path, arcname=os.path.basename(item_path))
                tar.close()

            # Encrypt the file
            gpg = gnupg.GPG()

            # Open TAR file
            tar = tarfile.open(tar_file_path, 'r')

            with open(output_file, 'rb') as f:
                status = gpg.encrypt_file(
                    f, recipients=[GPG_RECIPIENT],
                    always_trust=True,
                    output=f"{output_file}.gpg")

            if status.ok:
                print('File encrypted successfully.')
            else:
                print('Error encrypting the file:', status.status)

        else:
            # Directory is empty, skip processing
            logging.info("Empty directory, skipping: %s", item_path)

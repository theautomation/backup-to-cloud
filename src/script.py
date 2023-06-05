#!/bin/python3
#
# A script to tarball each directory in the given backup directory location, encrypt each tar file with GPG using my own public key and upload those encrypted files to my Dropbox in the cloud.
#
# script writtin by Coen Stam.
# github@theautomation.nl
#

import os
import sys
import logging
import tarfile
from datetime import date
import gnupg
import dropbox

# Define the variables
LOG_FILE_LOCATION = os.getenv('LOG_FILE_LOCATION', './backup-to-cloud.log')
BACKUP_DIRECTORY = os.getenv(
    'BACKUP_DIRECTORY', '/home/coen/storage-server/coen/backups-test')
GPG_RECIPIENT = os.getenv('GPG_RECIPIENT', 'gpg@theautomation.nl')
DROPBOX_REMOTE_LOCATION = os.getenv('DROPBOX_REMOTE_LOCATION', '')
DROPBOX_CLIENT_ID = os.getenv('DROPBOX_CLIENT_ID', '')
DROPBOX_CLIENT_SECRET = os.getenv('DROPBOX_CLIENT_SECRET', '')
DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN', '')
TEST_VAR = os.getenv('TEST_VAR', '')
# Get the log level from the environment variable
log_level_str = os.getenv('LOG_LEVEL', 'INFO')

# Convert the log level string to the corresponding constant value
log_level = getattr(logging, log_level_str.upper())

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
              "DROPBOX_REMOTE_LOCATION: %s\n"
              "DROPBOX_REFRESH_TOKEN: %s",
              LOG_FILE_LOCATION, BACKUP_DIRECTORY, GPG_RECIPIENT, DROPBOX_REMOTE_LOCATION, DROPBOX_REFRESH_TOKEN)


def dropbox_upload(file_path, dropbox_path, access_token):
    dbx = dropbox.Dropbox(access_token)
    try:
        with open(file_path, "rb") as file:
            logging.info("Uploading file to Dropbox...")
            dbx.files_upload(file.read(), dropbox_path)
            logging.info("File upload completed successfully.")
    except dropbox.exceptions.DropboxException as e:
        logging.error("Failed uploading file to Dropbox: %s", e)


def dropbox_refresh_access_token(refresh_token, client_id, client_secret, redirect_uri):
    auth_flow = dropbox.DropboxOAuth2Flow(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )

    try:
        refreshed_token = auth_flow.refresh_access_token(refresh_token)
        access_token = refreshed_token.access_token
        print("New access token:", access_token)
        return access_token
    except dropbox.exceptions.AuthError as e:
        print("Error refreshing access token:", e)
        return None

# Check if the directory exists
if not os.path.exists(BACKUP_DIRECTORY):
    # Create the directory
    os.makedirs(BACKUP_DIRECTORY)
    logging.error("Backup directory: %s does not exist", BACKUP_DIRECTORY)
    sys.exit(1)
else:
    logging.debug("Backup directory exists: %s", BACKUP_DIRECTORY)

def get_var_name(variable):
    globals_dict = globals()
    return [
        var_name for var_name in globals_dict
        if globals_dict[var_name] is variable
    ]

def check_empty_env_vars(*args):
    for variable in args:
        if variable == '':
            variable_name = get_var_name(variable)[0] if variable is not None else "Unknown Variable"
            logging.error("Please set a value in the \"" + variable_name + "\" " + "environment variable.")
            sys.exit(1)


check_empty_env_vars(DROPBOX_CLIENT_ID)

# Loop through all files and directories within the parent directory
for item in os.listdir(BACKUP_DIRECTORY):
    item_path = os.path.join(BACKUP_DIRECTORY, item)
    if os.path.isdir(item_path):
        # Check if the directory is not empty
        if os.listdir(item_path):
            # Process the non-empty directory
            logging.info("Found non-empty directory: %s", item_path)

            # Get the name of the directory that is not empty
            directory_name = os.path.basename(item_path)
            # Get the current date
            current_date = date.today().strftime("%Y-%m-%d")
            # Get output filename
            output_filename = f"{current_date}_{directory_name}"

            # Create the tar archive with the same name as the directory
            output_file = os.path.join(
                BACKUP_DIRECTORY, f"{output_filename}.tar.gz")
            with tarfile.open(output_file, "w:gz") as tar:
                tar.add(item_path, arcname=os.path.basename(item_path))
                tar.close()

            # Output filename for encrypted file
            encrypted_filename = f"{output_file}.gpg"
            # Encrypt the file
            gpg = gnupg.GPG()
            with open(output_file, 'rb') as f:
                status = gpg.encrypt_file(
                    f, recipients=[GPG_RECIPIENT],
                    always_trust=True,
                    output=encrypted_filename)
            if status.ok:
                logging.info("File \"" + output_filename +
                             ".tar.gz\" encrypted successfully.")
            else:
                logging.error("Error encrypting the file:", status.status)

            # Upload encrypting file to Dropbox
            dropbox_upload(encrypted_filename, DROPBOX_REMOTE_LOCATION +
                           "/"+encrypted_filename, DROPBOX_REFRESH_TOKEN)

        else:
            # Directory is empty, skip processing
            logging.info("Empty directory, skipping: %s", item_path)

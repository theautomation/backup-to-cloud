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
DROPBOX_REMOTE_LOCATION = os.getenv('DROPBOX_REMOTE_LOCATION')
DROPBOX_CLIENT_ID = os.getenv('DROPBOX_CLIENT_ID', '')
DROPBOX_CLIENT_SECRET = os.getenv('DROPBOX_CLIENT_SECRET', '')
DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN', '')

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


def log_environment_variables(**variables):
    """
    Logs the names and values of the specified variables using the logging module.
    """
    log_message = "The following environment variables have been configured:\n"
    for name, value in variables.items():
        log_message += f"{name}: {value}\n"
    logging.debug(log_message)


def check_directory_exists(directory):
    """
    Checks if directory exists and SystemExit if the backup directory does not exist.
    """
    if not os.path.exists(directory):
        logging.error("Backup directory '%s' does not exist", directory)
        sys.exit(1)
    logging.debug("Backup directory exists: %s", directory)


def check_required_env_variable(*required_variables):
    """
    Check variables and if they have no value, exit.
    """
    for var in required_variables:
        if not var:
            logging.error(
                "Please set a value in the required environment variables.")
            sys.exit(1)


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


def non_empty_directory_path(directory):
    """
    Return a (sub)directory inside the input directory that is not empty.
    """
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path) and os.listdir(item_path):
            logging.info("Found non-empty directory: %s", item_path)
            return item_path


def directory_name(directory_path):
    """
    Return the directory name of the input directory path.
    """
    directory_name = os.path.basename(directory_path)
    return directory_name


log_environment_variables(
    LOG_FILE_LOCATION=LOG_FILE_LOCATION,
    BACKUP_DIRECTORY=BACKUP_DIRECTORY,
    GPG_RECIPIENT=GPG_RECIPIENT,
    DROPBOX_REMOTE_LOCATION=DROPBOX_REMOTE_LOCATION,
    DROPBOX_CLIENT_ID=DROPBOX_CLIENT_ID,
    DROPBOX_CLIENT_SECRET=DROPBOX_CLIENT_SECRET,
    DROPBOX_REFRESH_TOKEN=DROPBOX_REFRESH_TOKEN
)

check_required_env_variable(BACKUP_DIRECTORY, GPG_RECIPIENT, DROPBOX_REMOTE_LOCATION,
                            DROPBOX_CLIENT_ID, DROPBOX_CLIENT_SECRET, DROPBOX_REFRESH_TOKEN)


check_directory_exists(BACKUP_DIRECTORY)


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

#             # Create the tar archive with the same name as the directory
#             output_file = os.path.join(
#                 BACKUP_DIRECTORY, f"{output_filename}.tar.gz")
#             with tarfile.open(output_file, "w:gz") as tar:
#                 tar.add(item_path, arcname=os.path.basename(item_path))
#                 tar.close()

#             # Output filename for encrypted file
#             encrypted_filename = f"{output_file}.gpg"
#             # Encrypt the file
#             gpg = gnupg.GPG()
#             with open(output_file, 'rb') as f:
#                 status = gpg.encrypt_file(
#                     f, recipients=[GPG_RECIPIENT],
#                     always_trust=True,
#                     output=encrypted_filename)
#             if status.ok:
#                 logging.info("File \"" + output_filename +
#                              ".tar.gz\" encrypted successfully.")
#             else:
#                 logging.error("Error encrypting the file:", status.status)

#             # # Upload encrypting file to Dropbox
#             # dropbox_upload(encrypted_filename, DROPBOX_REMOTE_LOCATION +
#             #                "/"+encrypted_filename, DROPBOX_REFRESH_TOKEN)

#         else:
#             # Directory is empty, skip processing
#             logging.info("Empty directory, skipping: %s", item_path)

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
from datetime import datetime
import gnupg
import dropbox
from typing import List

# Define the variables
LOG_FILE_LOCATION = os.getenv('LOG_FILE_LOCATION', './backup-to-cloud.log')
BACKUP_DIRECTORY = os.getenv(
    'BACKUP_DIRECTORY', '/home/coen/storage-server/coen/backups-test')
GPG_RECIPIENT = os.getenv('GPG_RECIPIENT', 'gpg@theautomation.nl')

DROPBOX_UPLOAD = os.getenv('DROPBOX_UPLOAD', True)
DROPBOX_REMOTE_LOCATION = os.getenv('DROPBOX_REMOTE_LOCATION', 'test')
DROPBOX_CLIENT_ID = os.getenv('DROPBOX_CLIENT_ID', 'test')
DROPBOX_CLIENT_SECRET = os.getenv('DROPBOX_CLIENT_SECRET', 'test')
DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN', 'test')

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
    Logs the names and values of the specified variables, only when loglevel debug has been set, using the logging module.

    :param variables: Keyword arguments representing the variables to be logged.
    :return: None

    The function iterates through the keyword arguments provided in the 'variables' parameter.
    For each variable, it constructs a log message that includes the variable name and its corresponding value.
    The log message is then logged at the debug level using the logging module.

    Example usage:
        log_environment_variables(API_KEY="xxxxxx", DATABASE_URL="postgres://user:password@localhost:5432/db")
        This will log the names and values of the "API_KEY" and "DATABASE_URL" variables at the debug level.

    Note: This function requires the 'logging' module to be imported.
    """
    log_message = "The following environment variables have been configured:\n"
    for name, value in variables.items():
        log_message += f"{name}: {value}\n"
    logging.debug(log_message)


def check_directory_exists(directory: str):
    """
    Checks if the specified directory exists and exits if it does not.

    :param directory: The directory path to check.
    :return: None

    The function uses the 'os.path.exists' method to check if the specified directory exists.
    If the directory does not exist, the function logs an error message and exits the program with a status code of 1.
    If the directory exists, a debug-level log message is generated.

    Example usage:
        check_directory_exists("/path/to/backup")
        This will check if the "/path/to/backup" directory exists.
        If the directory does not exist, the function will log an error message and exit the program.

    Note: This function requires the 'logging' and 'sys' modules to be imported.
    """
    if not os.path.exists(directory):
        logging.error("Backup directory '%s' does not exist", directory)
        sys.exit(1)
    logging.debug("Backup directory exists: %s", directory)


def check_required_env_variable(*required_variables):
    """
    Checks if the specified environment variables have a value and exits if any of them is missing.

    :param required_variables: One or more environment variables to check.
    :return: None

    The function iterates through the provided required_variables.
    For each variable, it checks if the variable has a value (i.e., not empty or None).
    If any of the variables is empty or None, the function logs an error message and exits the program with a status code of 1.

    Example usage:
        check_required_env_variable("API_KEY", "DATABASE_URL")
        This will check if the "API_KEY" and "DATABASE_URL" environment variables have a value.
        If any of them is missing or empty, the function will log an error message and exit the program.

    Note: This function requires the 'logging' and 'sys' modules to be imported.
    """
    for var in required_variables:
        if not var:
            logging.error(
                "Please set a value in the required environment variables.")
            sys.exit(1)


def dropbox_refresh_access_token(refresh_token, client_id, client_secret, redirect_uri):
    """
    Refreshes the access token for Dropbox API using the provided refresh token.

    :param refresh_token: The refresh token associated with the Dropbox user.
    :param client_id: The client ID of the Dropbox app.
    :param client_secret: The client secret of the Dropbox app.
    :param redirect_uri: The redirect URI used in the Dropbox app configuration.
    :return: The new access token if it was successfully refreshed, or None if an error occurred.

    The function creates a Dropbox OAuth2 flow object using the provided client ID, client secret,
    and redirect URI. It then attempts to refresh the access token using the refresh token with the
    'refresh_access_token' method of the flow object. If the refresh is successful, the function
    retrieves the new access token and prints it. The new access token is then returned. If an
    'AuthError' occurs during the refresh process, the error message is printed, and None is returned.

    Note: This function requires the 'dropbox' module to be imported.

    Example usage:
        refresh_token = "xxxxxxxxxxxx"
        client_id = "your_client_id"
        client_secret = "your_client_secret"
        redirect_uri = "https://your-redirect-uri.com"
        new_access_token = dropbox_refresh_access_token(refresh_token, client_id, client_secret, redirect_uri)
        The new access token, if refreshed successfully, will be returned, otherwise, None will be returned.
    """
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


def dropbox_upload(file_path: str, dropbox_path: str, access_token: str):
    """
    Uploads a file to Dropbox using the provided access token.

    :param file_path: The path of the file to be uploaded.
    :param dropbox_path: The path in Dropbox where the file will be uploaded.
    :param access_token: The access token for authenticating with the Dropbox API.

    The function creates a Dropbox object using the provided access token.
    It then opens the specified file in binary mode and reads its content.
    The content is then uploaded to the specified Dropbox path using the 'files_upload' method of the Dropbox object.
    Logging messages are generated to indicate the progress and status of the upload process.

    Note: This function requires the 'dropbox' module to be imported.

    Example usage:
        file_path = "/path/to/file.txt"
        dropbox_path = "/destination/folder/file.txt"
        access_token = "your_access_token"
        dropbox_upload(file_path, dropbox_path, access_token)
        This will upload the file at '/path/to/file.txt' to Dropbox at '/destination/folder/file.txt'.
    """
    dbx = dropbox.Dropbox(access_token)
    try:
        with open(file_path, "rb") as file:
            logging.info("Uploading file to Dropbox...")
            dbx.files_upload(file.read(), dropbox_path)
            logging.info("File upload completed successfully.")
    except dropbox.exceptions.DropboxException as e:
        logging.error("Failed uploading file to Dropbox: %s", e)


def non_empty_directory_paths_list(path: str) -> List[str]:
    """
    Returns a list of non-empty directories found within the given path.

    :param path: The path to search for non-empty directories.
    :return: A list of non-empty directory paths found within the given path.

    The function iterates through the items in the specified path using 'os.listdir'.
    For each item, it creates a subpath by joining the item with the parent path using 'os.path.join'.
    If the subpath is a directory, contains no files, but has at least one subdirectory, the function adds it to the result list.
    The function returns the list of non-empty directory paths.

    Example usage:
        path = "/parent/directory/"
        non_empty_dirs = non_empty_directory_paths_list(path)
        # non_empty_dirs may contain ['/parent/directory/non_empty_subdirectory1', '/parent/directory/non_empty_subdirectory2', ...]

    Note: This function requires the 'os' and 'logging' modules to be imported.
    """
    non_empty_dirs = []
    for item in os.listdir(path):
        non_empty_subpath = os.path.join(path, item)
        if os.path.isdir(non_empty_subpath):
            subdirs = [subdir for subdir in os.listdir(non_empty_subpath) if os.path.isdir(
                os.path.join(non_empty_subpath, subdir))]
            if subdirs:
                non_empty_dirs.append(non_empty_subpath)
        else:
            logging.info("Empty directory, skipping: %s", non_empty_subpath)
    return non_empty_dirs


def last_directory_name(path: str) -> str:
    """
    Returns the name of the last directory in the given path.

    :param path: The path from which to extract the last directory name.
    :return: The name of the last directory in the path.

    Example usage:
        path = "/path/to/directory/"
        directory_name = last_directory_name(path)
        directory_name will be "directory"

    Note: This function requires the 'os' module to be imported.
    """
    directory_name = os.path.basename(path)
    return directory_name


def create_tar(input_paths: List[str], output_path: str) -> List[str]:
    """
    Creates compressed tarballs (.tar.gz) from the specified input paths and saves them to the output path.

    :param input_paths: A list of paths to the directories or files to be included in the tarballs.
    :param output_path: The path to the directory where the tarballs will be saved.
    :return: A list of the full filepaths of the created tarballs.

    The function creates a new tarfile for each input path using the output path and a filename derived from the input path,
    prefixed with the current date in the format "yyyy_mm_dd".
    The filename is obtained by using the last folder name in the input path.
    It iterates over each input path and adds their contents to the tarfile, preserving the original directory structure.
    The arcname parameter specifies the name of the top-level directory in the tarfile.
    Finally, the function returns a list of the full filepaths of the created tarballs.

    Example usage:
        input_paths = ["/path/to/files1", "/path/to/files2", "/path/to/files3"]
        output_path = "/path/to/output"
        tarball_paths = create_tar(input_paths, output_path)
        # This will create tarballs from the input paths and save them to the output path.
        # The filename of each tarball will be derived from the last folder name in the input path,
        # prefixed with the current date in the format "yyyy_mm_dd".
        # A list of the full filepaths of the created tarballs will be returned.

    Note: This function requires the 'tarfile', 'os', and 'datetime' modules to be imported.
    """
    current_date = datetime.now().strftime("%Y_%m_%d")
    tarball_paths = []
    for input_path in input_paths:
        output_filepath = os.path.join(
            output_path, f"{current_date}_{os.path.basename(input_path)}.tar.gz")
        with tarfile.open(output_filepath, "w:gz") as tar:
            tar.add(input_path, arcname=os.path.basename(input_path))
        tar.close()
        tarball_paths.append(output_filepath)
    return tarball_paths


def create_gpg(input_filepaths: List[str]):
    gpg = gnupg.GPG()
    for input_filepath in input_filepaths:
        with open(input_filepath, 'rb') as f:
            status = gpg.encrypt_file(
                f, recipients=[GPG_RECIPIENT],
                always_trust=True,
                output=f"{input_filepath}.gpg")
        if status.ok:
            logging.info("File \"" + input_filepath +
                         "\" encrypted successfully.")
        else:
            logging.error("Error encrypting the file:", status.status)

# print(non_empty_directory_paths_list(BACKUP_DIRECTORY))

# log_environment_variables(
#     LOG_FILE_LOCATION=LOG_FILE_LOCATION,
#     BACKUP_DIRECTORY=BACKUP_DIRECTORY,
#     GPG_RECIPIENT=GPG_RECIPIENT,
#     DROPBOX_REMOTE_LOCATION=DROPBOX_REMOTE_LOCATION,
#     DROPBOX_CLIENT_ID=DROPBOX_CLIENT_ID,
#     DROPBOX_CLIENT_SECRET=DROPBOX_CLIENT_SECRET,
#     DROPBOX_REFRESH_TOKEN=DROPBOX_REFRESH_TOKEN
# )

# check_required_env_variable(BACKUP_DIRECTORY, GPG_RECIPIENT)


tarfile = create_tar(non_empty_directory_paths_list(BACKUP_DIRECTORY),
                     BACKUP_DIRECTORY,)

create_gpg(tarfile)

# if DROPBOX_UPLOAD:
#     check_required_env_variable(
#         DROPBOX_REMOTE_LOCATION, DROPBOX_CLIENT_ID, DROPBOX_CLIENT_SECRET, DROPBOX_REFRESH_TOKEN)


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

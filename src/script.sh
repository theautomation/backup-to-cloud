#!/bin/bash
#
# A script to tarball each directory in the given backup directory location, encrypt each tar file with GPG using my own public key and upload those encrypted files to my Dropbox in the cloud.
#
# script writtin by Coen Stam.
# github@theautomation.nl
#

# Optional ENV variables with a default value
DEBUG=${DEBUG:-false}
LOG_FILE_LOCATION=${LOG_FILE_LOCATION:-"./backup-to-cloud.log"}

# Array of specific required environment variables to check
variables=("BACKUP_DIRECTORY" "GPG_RECIPIENT" "DROPBOX_REMOTE_LOCATION" "DROPBOX_ACCESS_TOKEN")

# Loop through specific required variables
for var_name in "${variables[@]}"; do
    # Get the value of the variable
    var_value="${!var_name}"

    # Check if the value is empty or not
    if [[ -z "$var_value" ]]; then
        echo "ERROR: The '$var_name' environment variable is empty."
        exit 1
    fi
done

if [ "$DEBUG" = true ]; then
    set -x
    # Redirect standard output to both the log file and stdout
    exec > >(tee -a "$LOG_FILE_LOCATION") 2>&1
fi

# Function to add timestamp to log messages
log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") $1"
}

# Create output directory if it doesn't exist
mkdir -p "$BACKUP_DIRECTORY"

# # Import GPG puclic key
# gpg --import ./backup-to-cloud_publickey.asc

# Loop through each subdirectory in the backup directory
for directory in "$BACKUP_DIRECTORY"/*; do

    if [[ $directory == *.tar.gz ]]; then
        continue # Skip existing tar.gz files
    fi

    if [ -d "$directory" ] && [ -n "$(find "$directory" -mindepth 1 -type f)" ]; then

        # Get the directory name without the full path
        dir_name=$(basename "$directory")

        # Create the output file name with the directory name and current date
        current_date=$(date +"%Y-%m-%d")
        tar_filename="${dir_name}_${current_date}.tar.gz"
        tar_output_path="${BACKUP_DIRECTORY}/${tar_filename}"

        # Create the tar file for the directory
        tar -czf "$tar_output_path" -C "$directory"

        log "Created tar file: $tar_filename"

        # Remove the contents from the directory
        rm -r "${directory:?}/"*
    else
        log "Skip tarball for \"$directory\", because there where no files found"
    fi
done

# Loop through each tar.gz file in the output directory
for file in "$BACKUP_DIRECTORY"/*"${current_date}.tar.gz"; do
    if [ -f "$file" ]; then
        # Encrypt the tar.gz file using gpg
        gpg --batch --yes --recipient "$GPG_RECIPIENT" --output "$file.gpg" --encrypt "$file"

        if [ $? -eq 0 ]; then
            log "Encryption successful. Encrypted file: $file.gpg"
        else
            log "Encryption failed for file: $file"
            exit 1
        fi
    fi
done

# Loop through each .gpg file in the directory
for file in "$BACKUP_DIRECTORY"/*.gpg; do
    if [ -f "$file" ]; then
        # Upload the file to Dropbox
        curl -X POST https://content.dropboxapi.com/2/files/upload \
            --header "Authorization: Bearer $DROPBOX_ACCESS_TOKEN" \
            --header "Dropbox-API-Arg: {\"path\":\"$DROPBOX_REMOTE_LOCATION/$(basename "$file")\",\"mode\":\"add\",\"autorename\":true,\"mute\":false}" \
            --header "Content-Type: application/octet-stream" \
            --data-binary @"$file"

        if [ $? -eq 0 ]; then
            log "Upload to Dropbox successful: $file"
            # Remove the gpg file after successful upload
            rm "$file"
        else
            log "Upload to Dropbox failed for file: $file"
            exit 1
        fi
    fi
done

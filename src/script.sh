#!/bin/bash
#
# A script to tarball each directory in the given backup directory location, encrypt each tar file with GPG using my own public key and upload those encrypted files to my Dropbox in the cloud.
#
# script writtin by Coen Stam.
# github@theautomation.nl
#

# should be from ENV
backup_directory="/home/coen/storage-server/coen/backups-test"
gpg_recipient="gpg@theautomation.nl"
debug=false
dropbox_remote_location=/backup-to-cloud
DROPBOX_ACCESS_TOKEN=""

# Dropbox script
dropbox_uploader="/home/coen/github/backup-to-cloud/src/dropbox_uploader.sh"

log_file="./backup-to-cloud.log"

if [ "$debug" = true ]; then
    set -x
fi

# Redirect standard output to both the log file and stdout
exec > >(tee -a "$log_file") 2>&1

# Function to add timestamp to log messages
log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") $1"
}

# Create output directory if it doesn't exist
mkdir -p "$backup_directory"

# Loop through each subdirectory in the parent directory
for directory in "$backup_directory"/*; do

    if [[ $directory == *.tar.gz ]]; then
        continue  # Skip existing tar.gz files
    fi

    if [ -d "$directory" ] && [ -n "$(find "$directory" -mindepth 1 -type f)" ]; then

        # Get the directory name without the full path
        dir_name=$(basename "$directory")

        # Create the output file name with the directory name and current date
        current_date=$(date +"%Y-%m-%d")
        tar_filename="${dir_name}_${current_date}.tar.gz"
        tar_output_path="${backup_directory}/${tar_filename}"

        # Create the tar file for the directory
        tar -czf "$tar_output_path" -C "$directory" .

        log "Created tar file: $tar_filename"

        # Remove the contents of the directory
        rm -r "${directory:?}/"*
    else
        log "Skip tarball for \"$directory\", because there where no files found"
    fi
done

# Loop through each tar.gz file in the output directory
for file in "$backup_directory"/*"${current_date}.tar.gz"; do
    if [ -f "$file" ]; then
        # Encrypt the tar.gz file using gpg
        gpg --batch --yes --recipient "$gpg_recipient" --output "$file.gpg" --encrypt "$file"

        if [ $? -eq 0 ]; then
            log "Encryption successful. Encrypted file: $file.gpg"
        else
            log "Encryption failed for file: $file"
            exit 1
        fi
    fi
done

# Loop through each .gpg file in the directory
for file in "$backup_directory"/*.gpg; do
    if [ -f "$file" ]; then
        # Upload the file to Dropbox
        curl -X POST https://content.dropboxapi.com/2/files/upload \
            --header "Authorization: Bearer $DROPBOX_ACCESS_TOKEN" \
            --header "Dropbox-API-Arg: {\"path\":\"$dropbox_remote_location/$(basename "$file")\",\"mode\":\"add\",\"autorename\":true,\"mute\":false}" \
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
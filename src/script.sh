#!/bin/bash
#
# This script will tarball each directory in the given backup folder location, encrypt each tar file with GPG using my own public key and upload those encrypted files to my Dropbox in the cloud.
#
# script writtin by Coen Stam.
# github@theautomation.nl
#

# should be from ENV
backup_directory="/c/Users/coen.stam/Documents/github/scripts/test/dir/backup"
gpg_recipient="gpg@theautomation.nl"
debug=false

# Dropbox script location
dropbox_uploader="/c/Users/coen.stam/Documents/github/scripts/test/dropbox_uploader.sh"


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
    if [ -d "$directory" ]; then
        # Get the directory name without the full path
        dir_name=$(basename "$directory")

        # Create the output file name with the directory name and current date
        current_date=$(date +"%Y-%m-%d")
        output_filename="${dir_name}_${current_date}.tar.gz"
        output_path="${backup_directory}/${output_filename}"

        # Create the tar file for the directory
        tar -czf "$output_path" -C "$directory" .

        log "Created tar file: $output_filename"
    fi
done

# Loop through each tar.gz file in the output directory
for file in "$backup_directory"/*.tar.gz; do
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
        # Upload the .gpg file to Dropbox using https://github.com/andreafabrizi/Dropbox-Uploader
        "$dropbox_uploader" upload "$file" "/Destination/Folder"

        if [ $? -eq 0 ]; then
            log "Upload to Dropbox successful: $file"
            # Remove gpg file when upload succeed
            rm $file
        else
            log "Upload to Dropbox failed for file: $file"
            exit 1
        fi
    fi
done

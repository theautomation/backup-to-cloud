#!/bin/bash

parent_directory="/c/Users/coen.stam/Documents/github/scripts/test/dir/backup"
output_directory="/c/Users/coen.stam/Documents/github/scripts/test/dir/backup"
gpg_recipient="gpg@theautomation.nl"
dropbox_uploader="/c/Users/coen.stam/Documents/github/scripts/test/dropbox_uploader.sh"

# Create output directory if it doesn't exist
mkdir -p "$output_directory"

# Loop through each subdirectory in the parent directory
for directory in "$parent_directory"/*; do
    if [ -d "$directory" ]; then
        # Get the directory name without the full path
        dir_name=$(basename "$directory")

        # Create the output file name with the directory name and current date
        current_date=$(date +"%Y-%m-%d")
        output_filename="${dir_name}_${current_date}.tar.gz"
        output_path="${output_directory}/${output_filename}"

        # Create the tar file for the directory
        tar -czf "$output_path" -C "$directory" .

        echo "Created tar file: $output_filename"
    fi
done

# Loop through each tar.gz file in the directory
for file in "$output_directory"/*.tar.gz; do
    if [ -f "$file" ]; then
        # Encrypt the tar.gz file using gpg
        gpg --batch --yes --recipient "$gpg_recipient" --output "$file.gpg" --encrypt "$file"

        if [ $? -eq 0 ]; then
            echo "Encryption successful. Encrypted file: $file.gpg"
        else
            echo "Encryption failed for file: $file"
        fi
    fi
done

# Loop through each .gpg file in the directory
for file in "$output_directory"/*.gpg; do
    if [ -f "$file" ]; then
        # Upload the .gpg file to Dropbox
        "$dropbox_uploader" upload "$file" "/Destination/Folder"

        if [ $? -eq 0 ]; then
            echo "Upload to Dropbox successful: $file"
        else
            echo "Upload to Dropbox failed for file: $file"
        fi
    fi
done

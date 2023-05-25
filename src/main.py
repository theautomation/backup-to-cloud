# Script written by Coen Stam
#
# Tarball backups directory, encrypt the tar file and upload to Dropbox cloud.
#
# v0.0.1

from datetime import date
import os
import tarfile
import gnupg


directory_path = "/home/coen/github/backup-to-cloud/test/backups"
output_path = "/home/coen/github/backup-to-cloud/test/backups"


def create_tar(directory_path, output_dir):
    # Get the current date
    current_date = date.today().strftime("%Y-%m-%d")

    # Create the output file name with the date
    output_filename = f"{current_date}.tar.gz"
    output_path = os.path.join(output_dir, output_filename)

    with tarfile.open(output_path, "w:gz") as tar:
        tar.add(directory_path, arcname="")


def encrypt_file(filename, recipient):
    # Initialize GPG object
    gpg = gnupg.GPG()

    # Import recipient's public key
    with open('recipient_public_key.asc', 'r') as f:
        key_data = f.read()
        import_result = gpg.import_keys(key_data)

    if not import_result.counts['imported']:
        print("Failed to import recipient's public key.")
        exit()

    # Encrypt the file
    with open(filename, 'rb') as f:
        encrypted_data = gpg.encrypt_file(
            f, recipients=[recipient], output=f"{filename}.gpg")

    if encrypted_data.ok:
        print(f"File encrypted successfully: {filename}.gpg")
    else:
        print("Encryption failed.")


create_tar(directory_path, output_path)


encrypt_file('your_file.tar.gz', 'recipient@example.com')

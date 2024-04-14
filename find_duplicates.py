#!/usr/bin/env python
import time
import hashlib
import os
import sys


def clear_line(begin):
    """Clear the current line and optionally return the cursor to the start of the line.

    @param begin: A boolean indicating whether to return or not the cursor at the start of the line.
    """

    if begin:
        print("\r" + " " * 100, end="\r", flush=True)
    else:
        print("\r" + " " * 100, end="", flush=True)


def reprintscr(to_prt):
    """Clear the current line and print the text provided.

    @param to_prt: The string to print.
    """

    # Clear the line
    clear_line(True)
    # Print the new text
    print(to_prt, end="", flush=True)


def start_bytes(path):
    """Read the first 2048 bytes from a file.

    @param path: The path of the file to read.
    """

    data = b""
    with open(path, "rb") as f:
        data = f.read(2048)
    return data


# Create a 64 byte long file fingerprint
def file_fingerprint(path, file_size, block_nbr=4):
    """Generate a 64 byte-long sequence that would uniquely identify a file's contents.
    This function reads multiple sections of a file to determine its contents.
    The resulting byte-sequence is a fingerprint of the file specified. The fingerprint's
    uniqueness is based on the fact that it is very unlikely that different images would
    contain the same data at various locations in their files.

    @param path: The path of the file to fingerprint.
    @param file_size: The size of the file provided. It is used to avoid redundant operations.
    @param block_nbr: The number of sections to read from the file specified.
    @returns: A fingerprint of 64 bytes or less that uniquely identifies the file specified.
    """

    # Read the totality of the file if it is less than or equal to 64 bytes
    if file_size <= 64:
        with open(path, "rb") as f:
            return f.read()
    else:
        block_length = int(64 / block_nbr)
        file_quarter = int(file_size / block_nbr)
        data = b""
        with open(path, "rb") as f:
            for i in range(block_nbr):
                data += f.read(block_length)
                f.seek(block_nbr * i, 0)
        return data


def find_files(root_path):
    """Generate a list of all the files contained inside the path specified.
    This function is recursive, so it also finds all the files contained in all the subdirectories
    of the root path.

    Code adapted from https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory

    @param root_path: The root folder from where the search should start.
    @returns: A list of all the files contained in the root folder.
    """

    subdirectories = []
    files = []
    # Identify all files and folders in the provided directory
    for path in os.listdir(root_path):    
        full_path = os.path.join(root_path, path)
        if os.path.isdir(full_path):
            subdirectories.append(full_path)
        elif os.path.isfile(full_path):
            files.append(full_path)
    # Loop through every folder and obtain its files recursively
    for folder in subdirectories:
        subfolder_files = find_files(os.path.join(root_path, folder))
        subfolder_files = [os.path.join(folder, f) for f in subfolder_files]
        files += subfolder_files
    # Return all the files found from the root_path recursively
    return files


# Get working directory
cwd = os.getcwd()

# Get all the folders containing the pictures
if len(sys.argv) > 1:
    arg_folders = sys.argv[1:]
else:
    print("No folder provided!")
    sys.exit()

# Check if the folders exist
all_folders = []
for folder in arg_folders:
    if not os.path.isdir(folder):
        print(f"Folder {folder} does not exist!")
        sys.exit()
    else:
        if folder.startswith("/"):
            all_folders.append(folder)
        else:
            folder = os.path.join(cwd, folder)
            all_folders.append(folder)
        print(f"Operating on: {folder}")

# Find all the files in the folders provided
all_files = []
for folder in all_folders:
    all_files += find_files(folder)
nbr_files = len(all_files)
print(f"Total number of pictures/files to check: {nbr_files}")

# Begin verifying all files
duplicates = 0 # Duplicate counter
file_size_info = {} # key=size value=filename
first_bytes_info = {} #key=bytes(2048) value=filename
fingerprint_info = {} # key=fingerprint value=filename

with open("all_duplicates.txt", "w") as duplicates_file, open("info.txt", "w") as info_file:
    info_file.write(f"Duplicate files starting from {all_folders}\n")
    # Loop through all files enumerated
    for i, f in enumerate(all_files):
        # Print progress 
        basename = os.path.basename(f)
        reprintscr(f"[WORKING ON]: {basename} --> {i + 1} of {nbr_files}")
        full_file_path = f # For ease of change
        file_size = os.path.getsize(full_file_path)

        # If the file size is unique, the file is unique
        if file_size in file_size_info:
            file_collided = file_size_info[file_size]
            # Get the first 2048 bytes of the files 
            collided_bytes = start_bytes(file_collided)
            current_bytes = start_bytes(full_file_path)
            # Add hash to the partial file hash info
            first_bytes_info[collided_bytes] = file_size_info[file_size]

            # Check if the file matches any partial hash 
            if current_bytes in first_bytes_info:
                # Compute a full file hash
                collided_fingerprint = file_fingerprint(file_collided, file_size)
                current_fingerprint = file_fingerprint(full_file_path, file_size)
                fingerprint_info[collided_fingerprint] = file_size_info[file_size]

                # Check if the file matches any full hash
                if current_fingerprint in fingerprint_info:
                    # Print that a duplicate file has been found
                    file_collided = fingerprint_info[current_fingerprint]
                    clear_line(True)
                    print(f"Duplicate found: '{basename}' --> '{os.path.basename(file_collided)}'", flush=True)
                    reprintscr(f"[WORKING ON]: {basename} --> {i + 1} of {nbr_files}")
                    duplicates_file.write(f"{f}\n")
                    info_file.write(f"'{f}' --> '{file_collided}'\n")
                    duplicates += 1
                else:
                    # Add the full hash to the dictionnary
                    fingerprint_info[current_fingerprint] = f
            else:
                # Add the partial hash to the dictionnary
                first_bytes_info[current_bytes] = f
        else:
            file_size_info[file_size] = f

clear_line(True)
print(f"Search ended: {duplicates} duplicates found out of {nbr_files} files")

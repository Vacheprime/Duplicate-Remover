import subprocess
import sys
import os
import datetime

# Global variable
year_folders = {}

def find_files(root_path):
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


def get_create_dates(tag, files):
    """Determine the creation date of a file using exiftool.
    
    @param tag: The exiftool tag to use to find the creation date of the file.
    @param files: A list of all the files to process. 
    @returns: A list of datime objects representing the creation date of the files.
    """
    
    # Use exiftool to process all the files at once. Processing as a batch improves performance.
    exif_p = subprocess.run(["exiftool", "-q", "-T", tag] + files, capture_output=True)
    stdout = exif_p.stdout.decode().split("\n")
    stdout = stdout[:-1]
    all_create_dates = []
    # Parse the dates from the output
    for time_elements in stdout:
        time_elements = time_elements.split(" ")
        time_elements = time_elements[0].split(":")
        try:
            create_date = datetime.datetime(int(time_elements[0]), int(time_elements[1]), int(time_elements[2]))
            all_create_dates.append(create_date)
        except Exception as e:
            all_create_dates.append(None)
            continue
    return all_create_dates


def sort_files(all_files, create_dates):
    """Create symbolic links of the files provided and place them in an organised directory structure.
    This function sorts the files provided by creating symbolic links to them in a 
    directory structure that organises the files by year and then by month.
    
    @param all_files: A list of all the files to sort.
    @param create_dates: A list of all the creation dates of the files to sort.
    @returns: A list of all the files that could not be sorted because they possess no creation date.
    """

    global year_folders
    unsorted_f = []
    # Save all of the unsorted fies in a text file
    with open("unsorted.txt", "w") as unsorted_file:
        unsorted_file.write("===================\n")
        for i, f in enumerate(all_files):
            basename = os.path.basename(f)
            create_date = create_dates[i]
            if create_date != None: # Proceed to sort the file
                yr = str(create_date.year)
                mt = str(create_date.month)
                if yr in year_folders:
                    if mt in year_folders[yr]:
                        if os.path.exists(os.path.join(yr, mt, basename)):
                            os.symlink(f, os.path.join(yr, mt, basename + str(i)))
                        else:
                            os.symlink(f, os.path.join(yr, mt, basename))
                    else:
                        year_folders[yr].append(mt)
                        os.mkdir(os.path.join(yr, mt))
                        if os.path.exists(os.path.join(yr, mt, basename)):
                            os.symlink(f, os.path.join(yr, mt, basename + str(i)))
                        else:
                            os.symlink(f, os.path.join(yr, mt, basename))
                else:
                    year_folders[yr] = [mt]
                    os.mkdir(yr)
                    os.mkdir(os.path.join(yr, mt))
                    if os.path.exists(os.path.join(yr, mt, basename)):
                        os.symlink(f, os.path.join(yr, mt, basename + str(i)))
                    else:
                        os.symlink(f, os.path.join(yr, mt, basename))
            else: # Save the file as unsorted
                print(f"{basename} has no date!")
                unsorted_f.append(f)
                unsorted_file.write(f"{f}\n")
    return unsorted_f

# Get arguments
if len(sys.argv) > 1:
    arg_folders = sys.argv[1:]
else:
    print("No folders provided!")
    sys.exit()

# Check if the folders exist
all_folders = []
cwd = os.getcwd()
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

# Find all the files contained in the folders provided.
all_files = []
for folder in all_folders:
    all_files += find_files(folder)
nbr_files = len(all_files)
print(f"Total number of pictures to sort: {nbr_files}")

# Sort by create date
create_dates = get_create_dates("-CreateDate", all_files)
unsorted_files = sort_files(all_files, create_dates)
# Sort by date acquired
create_dates = get_create_dates("-DateAcquired", unsorted_files)
unsorted_files = sort_files(unsorted_files, create_dates)
# Sort by date modified
create_dates = get_create_dates("-FileModifyDate", unsorted_files)
sort_files(unsorted_files, create_dates)

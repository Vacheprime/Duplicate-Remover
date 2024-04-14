# Duplicate-Remover

Two simple python scripts used to find duplicates and sort photos.
To find duplicates, the file size of the files to analyse are first compared, then the first 2048 bytes, and finally a 64-byte long fingerprint.
To sort the files/photo, the file creation date, the date acquired, and the file modification date are used. Those are found using exiftool. 

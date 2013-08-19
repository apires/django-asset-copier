django-asset-copier
===================

This app will go through your static files, media_root and DB, dump all the data and tar it up for you.

Usage:

  - export your DJANGO\_SETTINGS\_MODULE
  
  python writer.py outputfile

  This will create outputfile.tbz2, which contains the following files:
    - dbdump.sql  # redo script for the tables and data in the default DB
    - storage_files.tar # files from MEDIA\_ROOT
    - static_files.tar  # files for STATIC\_ROOT

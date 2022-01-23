#!/usr/bin/env python

from datetime import datetime
from shutil import copy2, copytree
from zipfile import ZipFile
import glob
import hashlib
import json
import os
import sys


try:
    from google.colab import drive
    drive.mount('/content/drive', force_remount=True)
    is_local = False
except ModuleNotFoundError:
    is_local = True


folder_landing = "./landing" if (is_local) else "/content/drive/MyDrive/ADSDB/landing"

folder_temporal = os.path.join(folder_landing, "temporal")
folder_persistent = os.path.join(folder_landing, "persistent")

extract_dir = os.path.join(folder_persistent, "extracted")

glob_meta_file = os.path.join(folder_persistent, "global_metadata.json")

time_format = "%Y/%m/%d %H:%M:%S"


def sha256_file(filename):
    with open(filename,"rb") as f:
        return hashlib.sha256(f.read()).hexdigest();


def landing_file(file_path):
    filename = os.path.basename(file_path)

    modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    modification_timestamp = modification_time.timestamp()

    ingestion_time = datetime.now()
    ingestion_timestamp = ingestion_time.timestamp()

    sha256 = sha256_file(file_path) if os.path.isfile(file_path) else None

    out_dir = os.path.join(extract_dir, f"{filename}-{sha256}-{ingestion_timestamp}")
    os.makedirs(out_dir, exist_ok = True)

    print(out_dir)

    if os.path.isdir(file_path):
        return None
    elif file_path[:-4] == ".zip":
        with ZipFile(file_path, 'r') as zipObj:
            zipObj.extractall(out_dir)
    elif os.path.isfile(file_path):
        copy2(file_path, out_dir)

    file_list = list()
    for (dirpath, dirnames, filenames) in os.walk(out_dir):
        file_list += [
            os.path.relpath(
                os.path.join(dirpath, file),
                start = out_dir
            ) for file in filenames
        ]

    metadata = {
        "filename" : filename,
        "dir" : out_dir,
        "source" : os.path.relpath(file_path, start = folder_landing),
        "sha256" : sha256,

        "contents" : file_list,

        "modification_timestamp" : modification_timestamp,
        "modification_time" : modification_time.strftime(time_format),

        "ingestion_timestamp" : ingestion_timestamp,
        "ingestion_time" : ingestion_time.strftime(time_format),
    }

    with open(os.path.join(out_dir, "metadata.json"), 'w') as outfile:
        json.dump(metadata, outfile, indent=2, sort_keys=True)

    return metadata


def import_with_global_meta(file_list):
    global_metadata = dict()

    for file_path in file_list:
        print(file_path)

        metadata = landing_file(file_path)

        if metadata is None:
            print("SKIP", file_path)
            continue

        print("COPIED", file_path, "=>", metadata['dir'])

        filename = metadata["filename"]
        ingestion_timestamp = metadata["ingestion_timestamp"]

        global_metadata[f"{filename}-{ingestion_timestamp}"] = metadata


    try:
        with open(glob_meta_file, 'r') as f:
            old_meta = json.load(f)
    except FileNotFoundError:
        old_meta = dict()

    joined_meta = {**old_meta, **global_metadata}

    with open(glob_meta_file, 'w') as f:
        old_meta = json.dump(joined_meta, f, indent=2, sort_keys=True)


def main():
    if len(sys.argv) == 1:
        file_list = glob.glob(os.path.join(folder_temporal, "*"))
    else:
        file_list = list()
        for arg in sys.argv[1:]:
            if os.path.isdir(arg):
                file_list += glob.glob(os.path.join(arg, "*"))
            elif os.path.isfile(arg):
                file_list += [arg]
            else:
                print("WARNING: not a file or diretory:", arg, "(IGNORED)")

    import_with_global_meta(file_list)

if __name__ == '__main__':
    main()

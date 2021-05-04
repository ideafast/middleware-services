"""
Requires that /lookups/ has two files:

1. inventory.csv: an export from inventory to obtain all MMM asset IDs and serials
2. patients.csv: contains the table output from MyMcroberts website

Requires a folder /data/ that contains all post-processed data and a metadata file from MMM.
"""
from datetime import datetime
from os import listdir, mkdir
from pathlib import Path
from shutil import copy, make_archive

import pandas as pd

# Enables lookup of Device ID (asset) by serial
inventory = pd.read_csv("lookups/inventory.csv")

# Enables lookup and correction of Patient ID (pid)
# as pid may be incorrect on MMM's platform
patients = pd.read_csv("lookups/patients.csv")


def get_device_id(serial: str) -> str:
    device_id = inventory[inventory["serial"] == int(serial[2:])]["asset"]
    if len(device_id.values.tolist()) == 0:
        raise Exception("Invalid serial ID")
    return device_id.values.item().replace("-", "")


def get_patient_id(subject: str) -> str:
    patient_id = patients[patients["subject_id"] == subject]["patient_id"]
    if len(patient_id.values.tolist()) == 0:
        raise Exception("SubjectID not in lookup table ...")
    return patient_id.values.item()


# All the post-processed files that need moved
csvs = [f for f in listdir("./data") if f.endswith(".csv")]
# There is one file containing metadata for all .omx post-processed files
metadata_file = next(i for i in csvs if "meta" in i)

metadata = pd.read_csv(f"./data/{metadata_file}", sep=";")


def dmp_time(as_str: str) -> str:
    return datetime.strptime(as_str, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d")


for _, row in metadata.iterrows():
    # Which device was it?
    device_id = get_device_id(row["device_serialnumber"])
    # Which patient wore it?
    patient_id = get_patient_id(row["subject_code"])
    # Which post-processed files belong to this patient?
    files = [fname for fname in csvs if str(row["results_id"]) in fname]
    # Prepare a folder with DMP naming conventions
    start = dmp_time(row["measurement_starttime"])
    end = dmp_time(row["measurement_endtime"])
    dmp_path = Path(f"./output/{patient_id}-{device_id}-{start}-{end}")
    if not dmp_path.exists():
        mkdir(dmp_path)

    print("DMP INFO: ", device_id, patient_id, start, end)
    print("    ", f"ALL CREATED FOR {row['results_id']}")
    print("    ", files)

    for fname in files:
        copy(f"./data/{fname}", dmp_path)

    make_archive(str(dmp_path), "zip", dmp_path)

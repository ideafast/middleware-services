"""
WP3 are provided with a zip file from McRobert's containing all post-processed
data for each OMX file uploaded to their platform. This zip contains meta.csv that
outlines metadata for each record (SubjectID, resultsID (of algorithm run), etc) AND
the raw recordings that follow naming as: YEARMONTHDAY_IDEA-FAST_ACTION_RESULTSID_RAW.csv

Where Action is either "lying" or "classification" and CRITICALLY "RESULTSID" is the ID
that McRobert's data pipeline generates that is also included in meta.csv. This is therefore
used below to group CSVs by patient.

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
# For consistency of comparison convert to upper.
patients["subject_id"] = patients["subject_id"].str.upper()
patients["patient_id"] = patients["patient_id"].str.upper()

# Remove private or useless data for analysis
columns = [
    "user_name",
    "user_email",
    "project_name",
    "visit_name",
    "test_name",
    "subject_description",
    "DTF_version",
]


def get_device_id(serial: str) -> str:
    _serial = int(row["device_serialnumber"][2:])
    device_id = inventory[inventory["serial"] == _serial]["asset"]
    if len(device_id.values.tolist()) == 0:
        return None
    return device_id.values.item().replace("-", "").replace(" ", "")


def get_patient_id(subject: str) -> str:
    subject = subject.upper().replace("-", "").strip()
    patient_id = patients[patients["subject_id"] == subject]["patient_id"]
    if len(patient_id.values.tolist()) == 0:
        return None
        # raise Exception(f"SubjectID {subject} not in lookup table ...")
    return patient_id.values.item()


# All the post-processed files that need moved
csvs = [f for f in listdir("./data") if f.endswith(".csv")]
# There is one file containing metadata for all .omx post-processed files
metadata_file = next(i for i in csvs if "meta" in i)

metadata = pd.read_csv(
    f"./data/{metadata_file}",
    sep=";",
    # Not sure why the provided file is encoded in this way
    encoding="iso-8859-1",
)


def dmp_time(as_str: str) -> str:
    return datetime.strptime(as_str, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d")


for _, row in metadata.iterrows():
    # Skip test data
    if "test" in row["subject_code"].lower():
        continue
    # Which device was it?
    device_id = get_device_id(row["device_serialnumber"])
    # Which patient wore it?
    patient_id = get_patient_id(row["subject_code"])

    # One may not exist :(
    if not patient_id or not device_id:
        print(f"No device ({device_id}) or patient id ({patient_id})")
        continue

    # Which post-processed files belong to this patient?
    files = [fname for fname in csvs if str(row["results_id"]) in fname]
    # Prepare a folder with DMP naming conventions
    start = dmp_time(row["measurement_starttime"])
    end = dmp_time(row["measurement_endtime"])
    dmp_path = Path(f"./output/{patient_id}-{device_id}-{start}-{end}")
    if not dmp_path.exists():
        mkdir(dmp_path)

    print("\nDMP INFO: ", device_id, patient_id, start, end)
    print("    ", f"ALL CREATED FOR {row['results_id']}")
    print("    ", files)
    print(device_id)

    for fname in files:
        copy(f"./data/{fname}", dmp_path)

    row.drop(columns, inplace=True)
    row.to_csv(f"{dmp_path}/meta.csv", header=False)

    make_archive(str(dmp_path), "zip", dmp_path)

"""
Transforms and renames .OMX file for upload to DMP, e.g., from
data provided by Newcastle to be manually uploaded.

This depends on two CSVs:

    1. meta.csv:
        metadata associated with the patient; export from post-processed dataset that
        contains all metadata from MMM's platform.
        Used to derive patient/device IDs
    2. patients.csv:
        alias lookup table as PatientIDs in meta.csv may be incorrect as they are manually
        entered into McRobert's platform
"""

import os
from datetime import datetime

import pandas as pd

path = "~/Desktop/mcroberts/RAW/"
files = os.listdir(path)


def to_dmp_dt(part: str) -> str:
    converted = datetime.fromtimestamp(int(part))
    return datetime.strftime(converted, "%Y%m%d")


# Enables lookup and correction of Patient ID (pid)
# as pid may be incorrect on MMM's platform
patients = pd.read_csv("lookups/patients.csv")
# For consistency of comparison convert to upper.
patients["subject_id"] = patients["subject_id"].str.upper()
patients["patient_id"] = patients["patient_id"].str.upper()


def get_patient_id_new(subject: str) -> str:
    subject = subject.upper().replace("-", "").strip()
    patient_id = patients[patients["subject_id"] == subject]["patient_id"]
    if len(patient_id.values.tolist()) == 0:
        return None
        # raise Exception(f"SubjectID {subject} not in lookup table ...")
    return patient_id.values.item()


meta = pd.read_csv("./lookups/meta.csv", sep=";", encoding="iso-8859-1")


def get_patient_id_via_meta(measure_id: str) -> str:
    patient_id = meta[meta["measurement_id"] == int(measure_id)]["subject_code"]
    if len(patient_id.values.tolist()) == 0:
        return None
    return patient_id.values.item()


def get_device_id(serial_id: str) -> str:
    import requests

    response = requests.get(
        f"http://0.0.0.0:8000/inventory/device/byserial/{serial_id}"
    )
    return response.json()["data"]["device_id"].replace("-", "")


for _file in files:
    if "omx" in _file.lower() and "swp" not in _file.lower():
        splitter = _file.split("-")

        patient_id = get_patient_id_via_meta(splitter[0])
        if not patient_id:
            print(f"ERROR: NO PATIENT ID FOR: {_file}")
            continue

        patient_id = get_patient_id_new(patient_id)

        device_id = get_device_id(splitter[2])

        if not device_id:
            print(f"ERROR: NO DEVICE ID FOR: {_file}")
            continue
        start = to_dmp_dt(splitter[-2].split(".")[0])
        end = to_dmp_dt(splitter[-1].replace(".OMX", "").split(".")[0])
        final = f"{patient_id}-{device_id}-{start}-{end}.OMX"
        print(f"{_file}\n\t{final}")

        os.rename(f"{path}/{_file}", f"{path}/{final}")

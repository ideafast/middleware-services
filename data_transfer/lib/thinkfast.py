import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

# These must be stored locally
cantab = pd.read_csv("data/cantab.csv")
thinkfast = pd.read_csv("data/thinkfast.csv")

patient_id_cell = "IDEA-FAST Participant ID"
device_id = "TFAP6RJG3"

start = "Visit Start (Local)"
end = "Visit End (Local)"

thinkfast[patient_id_cell] = thinkfast[patient_id_cell].str.upper()
thinkfast[start] = thinkfast[start].str.upper()


def zip_and_rm(dmp_name: Path) -> None:
    shutil.make_archive(str(dmp_name), "zip", dmp_name)
    shutil.rmtree(dmp_name.with_suffix(""))


for _, row in cantab.iterrows():
    # Get all thinkfast data for the given patient (i.e., in this Cantab row)
    _thinkfast = thinkfast[thinkfast[patient_id_cell] == row[patient_id_cell].upper()]
    # The patient ID
    pid = row[patient_id_cell]
    # Note: if min and max are NaN then there is no ThinkFast usage ...
    _start, _end = _thinkfast[start].min(), _thinkfast[start].max()

    if pd.isnull(_start) or pd.isnull(_end):
        print(f"{pid} has no ThinkFast records.")

        __start = datetime.strptime(row[start], "%Y.%m.%d %H:%M:%S").strftime("%Y%m%d")
        __end = datetime.strptime(row[end], "%Y.%m.%d %H:%M:%S").strftime("%Y%m%d")

        dmp_name = Path(f"{pid}-{device_id}-{__start}-{__end}")

        if not dmp_name.exists():
            dmp_name.mkdir()

        row.to_csv(f"./{dmp_name}/cantab.csv")

        zip_and_rm(dmp_name)
        # Do not run code below and instead skip to next record
        continue

    _start = datetime.strptime(_start, "%Y.%m.%d %H:%M:%S").strftime("%Y%m%d")
    _end = datetime.strptime(_end, "%Y.%m.%d %H:%M:%S").strftime("%Y%m%d")

    dmp_name = Path(f"{pid}-{device_id}-{_start}-{_end}")

    if not dmp_name.exists():
        dmp_name.mkdir()

    _thinkfast.to_csv(f"./{dmp_name}/thinkfast.csv")
    row.to_csv(f"./{dmp_name}/cantab.csv")

    zip_and_rm(dmp_name)

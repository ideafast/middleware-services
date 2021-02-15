import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

cantab = pd.read_csv("data/cantab.csv")
thinkfast = pd.read_csv("data/thinkfast.csv")

patient_id_cell = "IDEA-FAST Participant ID"
device_id = "TFAP6RJG3"

# NOTE: cell names in both CSVs
start = "Visit Start (Local)"
end = "Visit End (Local)"

# NOTE: converted to upper as some Patient IDs are lowercase in thinkfast.csv
thinkfast[patient_id_cell] = thinkfast[patient_id_cell].str.upper()


def zip_and_rm(dmp_path: Path) -> None:
    shutil.make_archive(str(dmp_path), "zip", dmp_path)
    shutil.rmtree(dmp_path.with_suffix(""))


def dmp_time(as_str: str) -> str:
    return datetime.strptime(as_str, "%Y.%m.%d %H:%M:%S").strftime("%Y%m%d")


for _, row in cantab.iterrows():
    # Get all thinkfast data for the given patient (i.e., in this Cantab row)
    _thinkfast = thinkfast[thinkfast[patient_id_cell] == row[patient_id_cell].upper()]
    # The patient ID
    pid = row[patient_id_cell]
    # Note: if min and max are NaN then there is no ThinkFast usage ...
    _start, _end = _thinkfast[start].min(), _thinkfast[start].max()

    if pd.isnull(_start) or pd.isnull(_end):
        print(f"{pid} has no ThinkFast records.")
        _start, _end = dmp_time(row[start]), dmp_time(row[end])
    else:
        _start, _end = dmp_time(_start), dmp_time(_end)

    dmp_name = Path(f"{pid}-{device_id}-{_start}-{_end}")

    if not dmp_name.exists():
        dmp_name.mkdir()

    row.to_csv(f"./{dmp_name}/cantab.csv")

    if not pd.isnull(_start) or not pd.isnull(_end):
        _thinkfast.to_csv(f"./{dmp_name}/thinkfast.csv")

    zip_and_rm(dmp_name)

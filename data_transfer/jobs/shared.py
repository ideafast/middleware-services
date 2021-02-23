from dataclasses import dataclass
from pathlib import Path
from typing import List

from data_transfer.config import config
from data_transfer.db import (
    get_records_in_folder,
    min_max_data_wear_times,
    record_by_filename,
    unfinished_folders,
    update_record,
)
from data_transfer.schemas.record import Record
from data_transfer.services import dmpy

FILE_TYPES = {
    # Possibly move this to utils or embed with the enums
    "DRM": ".h5",
    "SMA": ".zip",
    "BTF": ".csv",
}


def batch_upload_data() -> None:
    """
    Zips and uploads all folders in /uploading/ to the DMP, which
    if successful, updates database record and removes data locally.

    This means that if prior tasks preprocessed multiple files from the same wear
    period, then those files will be uploaded as one request.
    """

    folders_to_upload = [p for p in config.upload_folder.iterdir() if p.is_dir()]

    for data_folder in folders_to_upload:
        zip_path = dmpy.zip_folder(data_folder)
        is_uploaded = dmpy.upload(zip_path)

        # Once uploaded to DMP, update metadata db
        if is_uploaded:
            # All records that were uploaded
            filenames = [f.stem for f in data_folder.iterdir() if "-meta" not in f.name]
            for filename in filenames:
                record = record_by_filename(filename)
                record.is_uploaded = True
                update_record(record)
            dmpy.rm_local_data(zip_path)


def prepare_data_folders() -> None:
    """
    Checks folders present in 'data/upload/ are finished
    and moves them into the upload folder in the format:

        DEVICEID-PATIENTID-STARTWEAR-ENDWEAR
    """

    @dataclass
    class taskObject:
        patient_id: str
        device_id: str
        folder: Path
        records: List[Record]

    ignore_folders = unfinished_folders()
    all_folders = [
        (p.name, d.name)
        for p in config.storage_vol.iterdir()
        if p.is_dir()
        for d in p.iterdir()
        if d.is_dir()
    ]
    ready_folders = [f for f in all_folders if f not in ignore_folders]

    to_process = [
        taskObject(
            folder[0],
            folder[1],
            (config.storage_vol / folder[0] / folder[1]),
            get_records_in_folder(folder[0], folder[1]),
        )
        for folder in ready_folders
    ]

    for task in to_process:
        max_data, min_data = min_max_data_wear_times(task.records)

        start_data = max_data.strftime("%Y%m%d")
        end_data = min_data.strftime("%Y%m%d")

        data_folder_name = (
            f"{task.patient_id}-{task.device_id.replace('-', '')}"
            f"-{start_data}-{end_data}"
        )
        destination = config.upload_folder / data_folder_name

        if not config.upload_folder.exists():
            config.upload_folder.mkdir()

        if not destination.exists():
            destination.mkdir()

        # assuming all downloads went well: move everything and update records
        for fname in task.folder.glob("*.*"):  # grabs all files

            new_path = destination / fname.name
            fname.rename(new_path)

        # update records
        for record in task.records:
            record.is_prepared = True
            update_record(record)

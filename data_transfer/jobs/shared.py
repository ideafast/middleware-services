import logging
from pathlib import Path

from data_transfer.config import config
from data_transfer.db import (
    min_max_data_wear_times,
    records_by_dmp_folder,
    records_not_uploaded,
    update_record,
)
from data_transfer.services import dmpy
from data_transfer.utils import DeviceType

FILE_TYPES = {
    # Possibly move this to utils or embed with the enums
    "DRM": ".h5",
    "SMA": ".zip",
    "BTF": ".csv",
}

log = logging.getLogger(__name__)


def batch_upload_data(device_type: DeviceType) -> None:
    """
    Zips and uploads all folders in /uploading/ to the DMP, which
    if successful, updates database record and removes data locally.

    This means that if prior tasks preprocessed multiple files from the same wear
    period, then those files will be uploaded as one request.
    """
    device_subfolder = config.upload_folder / device_type.name

    if not device_subfolder.exists():
        log.debug("Tried to upload non-existing folder.")
        return

    for data_folder in [p for p in device_subfolder.iterdir() if p.is_dir()]:
        upload_data(data_folder)


def upload_data(data_folder: Path) -> None:
    """Zips and uploads a folder at data_folder."""
    log.debug(f"Uploading: {data_folder}")

    zip_path = dmpy.zip_folder(data_folder)
    # is_uploaded = dmpy.upload(zip_path)

    # if is_uploaded:
    #     for record in records_by_dmp_folder(data_folder.stem):
    #         record.is_uploaded = True
    #         update_record(record)

    #     dmpy.rm_local_data(zip_path)


def prepare_data_folders(device_type: DeviceType) -> None:
    """
    Checks folders present in 'data/upload/ are finished
    and moves them into the upload folder in the format:

        DEVICEID-PATIENTID-STARTWEAR-ENDWEAR
    """
    grouped = records_not_uploaded(device_type)

    # filter sets which have any record with 'is_processed' == False
    # 'is_processed' == False catches the 'False' for any preceding task as well
    to_upload = {k: v for k, v in grouped.items() if all([r.is_processed for r in v])}

    for patient_device in to_upload.keys():
        max_data, min_data = min_max_data_wear_times(to_upload[patient_device])

        start_data = max_data.strftime("%Y%m%d")
        end_data = min_data.strftime("%Y%m%d")

        source = config.storage_vol / device_type.name / patient_device

        dmp_folder = (
            f"{patient_device.replace('-','').replace('/','-')}-{start_data}-{end_data}"
        )

        # patient_device looks like = 'patient-id/device-id'
        destination = config.upload_folder / device_type.name / dmp_folder

        destination.mkdir(parents=True, exist_ok=True)

        source.rename(destination)

        for record in to_upload[patient_device]:
            record.is_prepared = True
            record.dmp_folder = dmp_folder
            update_record(record)

        # check if patient folder is empty, then remove it
        patient_path = (
            config.storage_vol
            / device_type.name
            / to_upload[patient_device][0].patient_id
        )

        if not any(patient_path.iterdir()):
            patient_path.rmdir()
        else:
            log.error("Files left behind when uploading dataset to DMP.")

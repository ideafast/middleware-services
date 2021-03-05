from data_transfer.config import config
from data_transfer.db import (
    min_max_data_wear_times,
    record_by_filename,
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


def prepare_data_folders(device_type: DeviceType) -> None:
    """
    Checks folders present in 'data/upload/ are finished
    and moves them into the upload folder in the format:

        DEVICEID-PATIENTID-STARTWEAR-ENDWEAR
    """
    not_uploaded = records_not_uploaded(device_type)

    grouped: dict = {}
    # transform the result to {PatientID1-DeviceID1: [{Record1}, ... {Record2}], ... }
    [
        grouped.setdefault(f"{r.patient_id}-{r.device_id}", []).append(r)
        for r in not_uploaded
    ]

    # filter sets which have any record with 'is_processed' == False
    # 'is_processed' == False catches the 'False' for any preceding task as well
    to_upload = {k: v for k, v in grouped.items() if all([r.is_processed for r in v])}

    for patient_device in to_upload.keys():
        max_data, min_data = min_max_data_wear_times(to_upload[patient_device])

        start_data = max_data.strftime("%Y%m%d")
        end_data = min_data.strftime("%Y%m%d")

        source = config.storage_vol / patient_device.replace("-", "/", 1)
        destination = config.upload_folder / f"{patient_device}-{start_data}-{end_data}"
        source.rename(destination)

        # don't forget the -meta.json file! Each record in the list has a reference to it
        meta_file_name = f"{to_upload[patient_device][0].manufacturer_ref}-meta.json"
        meta_file_path = config.storage_vol / meta_file_name
        meta_file_path.rename(destination / meta_file_name)

        for record in to_upload[patient_device]:
            record.is_prepared = True
            update_record(record)

        # check if patient folder is empty, then remove it
        patient_path = config.storage_vol / to_upload[patient_device][0].patient_id
        if not any(patient_path.iterdir()):
            # throws if not empty
            patient_path.rmdir()

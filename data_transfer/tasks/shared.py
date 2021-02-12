from data_transfer.config import config
from data_transfer.db import read_record, update_record
from data_transfer.utils import DeviceType

FILE_TYPES = {
    # Possibly move this to utils or embed with the enums
    "DRM": ".h5",
    "SMA": ".zip",
    "BTF": ".csv",
}


def task_prepare_data(device_type: DeviceType, mongo_id: str) -> None:
    """
    Moves all data (meta/raw/preprocessed) from /input/ into one
    folder by Device/Patient ID in /uploading of the format:

        DEVICEID-PATIENTID-STARTWEAR-ENDWEAR

    This simplifies uploading of data where multiple exist for a single wear time.
    """
    record = read_record(mongo_id)

    # DMP requires no dashes in IDs or dates
    # NOTE: could replace this with ID validator/formatter in utils
    patient_id = record.patient_id.replace("-", "")
    device_id = record.device_id.replace("-", "")
    # DMP requires wear period format as: 2020/12/01
    start_wear = record.start_wear.strftime("%Y%m%d")
    end_wear = record.end_wear.strftime("%Y%m%d")

    data_folder_name = f"{patient_id}-{device_id}-{start_wear}-{end_wear}"

    destination = config.upload_folder / data_folder_name
    data_input = config.storage_vol

    if not config.upload_folder.exists():
        config.upload_folder.mkdir()

    if not destination.exists():
        destination.mkdir()

    if device_type is not DeviceType.BTF:
        for extension in [FILE_TYPES[device_type.name], "-meta.json"]:
            fname = f"{record.filename}{extension}"

            old_path = data_input / fname
            new_path = destination / fname

            old_path.rename(new_path)
            record.is_prepared = True
            update_record(record)
    else:
        # BTF only has the metadata file named after the filename, and needs
        # additional logic to pull in other files

        fname = f"{record.filename}-meta.json"

        old_path = data_input / fname
        new_path = destination / fname

        old_path.rename(new_path)

        for linked_file in record.meta["linked_files"]:
            fname = f"{linked_file}{FILE_TYPES[device_type.name]}"

            old_path = data_input / fname
            new_path = destination / fname

            old_path.rename(new_path)

        record.is_prepared = True
        update_record(record)

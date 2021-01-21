from data_transfer.db import records_not_prepared, update_record, read_record
from data_transfer.config import config

from collections import defaultdict
from pathlib import Path


FILE_TYPES = {
    'DRM': '.h5'
}


def prepare_for_upload(mongo_id: str):
    """
    Moves all meta/raw/preprocessed data from /input/ into folders in /processing/ format: 
        DEVICEID-PATIENTID-STARTWEAR-ENDWEAR 

    This simplifies zipping and uploading of data.
    """
    record = read_record(mongo_id)

    # DMP requires no dashes in these IDs or dates
    patient_id = record.patient_id.replace("-", "")
    device_id = record.device_id.replace("-", "")

    start_wear = record.start_wear.strftime("%Y%m%d")
    end_wear = record.end_wear.strftime("%Y%m%d")

    upload_folder = f"{patient_id}-{device_id}-{start_wear}-{end_wear}"

    destination = Path(config.storage_output / upload_folder)
    data_input = Path(config.storage_vol)

    if not config.storage_output.exists():
        config.storage_output.mkdir()
        
    if not destination.exists():
        destination.mkdir()

    device_extension = FILE_TYPES[record.device_id.split("-")[0]]
    
    for extension in [device_extension, "-meta.json"]:
        fname = f'{record.filename}{extension}'
        
        old_path = data_input / fname
        new_path = destination / fname
        
        old_path.rename(new_path)
        record.is_prepared = True
        update_record(record)

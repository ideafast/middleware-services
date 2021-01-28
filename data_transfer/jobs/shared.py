
from data_transfer.db import record_by_filename, update_record
from data_transfer.services import dmpy
from data_transfer.config import config

from pathlib import Path


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
            filenames = [f.stem for f in data_folder.iterdir() if '-meta' not in f.name]
            for filename in filenames:
                record = record_by_filename(filename)
                record.is_uploaded = True
                update_record(record)
            dmpy.rm_local_data(zip_path)
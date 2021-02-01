from data_transfer.config import config
from data_transfer.lib import vttsma as vttsma_api
from data_transfer.services import inventory
from data_transfer.schemas.record import Record
from data_transfer.db import create_record, \
    read_record, update_record, all_filenames
from data_transfer import utils

from pathlib import Path
from datetime import datetime
import json

class Vttsma:
    def __init__(self):
        """
        Set up a session to the s3 bucket to use in multiple steps
        """
        self.bucket = self.authenticate()

    def authenticate(self):
        """
        Authenticate once when object created to share session between requests
        """
        credentials = dict(
            aws_ak=config.vttsma_aws_accesskey, 
            aws_ask=config.vttsma_aws_secret_accesskey, 
            bucket_name=config.vttsma_aws_bucket_name,
            )

        bucket = vttsma_api.get_bucket(credentials)
        return bucket

    def download_metadata(self) -> None:
        """
        Before downloading raw data we need to know which files to download.
        VTT provides a weekly dump in an S3 bucket, with a symbolic structure:
        .
        ├── data_yyyy_mm_dd
        │   ├── users.txt
        │   ├── raw
        │   |   ├── vtt_patient (hash)
        │   |   └── vtt_patient (hash)
        │   |       ├── vtt_patient (hash).zip
        |   |       └── vtt_patient (hash).nfo
        |   └── files
        |           (audio files - unknown structure)
        .
       
        NOTE:
            - users.txt contains the user hashes present in this dump (equal to subfolders)
            - .nfo files contain the time spans of the specific hash dumps, e.g.:
                - Start time : 2020-10-28T00:00:01Z
                - End time   : 2020-11-24T00:00:00.001Z
        
        NOTE/TODO: will run as BATCH job.
        """
        
        # NOTE: includes metadata for ALL data records, therefore we must filter them 
        # NOTE: currently downloads all dumps (inc. historical) TODO: only since last run
        all_records = vttsma_api.get_list(self.bucket)

        # Only add records that are not known in the DB based on stored filename (id = VTT hash id)
        unknown_records = [r for r in all_records if r['id'] not in set(all_filenames())]

        # Aim: construct valid record (metadata) and add to DB
        for item in unknown_records:

            # device_serial = dreem_api.serial_by_device(item['device'])
            # device_id = inventory.device_id_by_serial(device_serial)
            device_id = 'x'

            # NOTE: lookup Patient ID by email: if None (e.g. personal email used), then use inventory
            # patient_id = dreem_api.patient_id_by_user(item['user']) or inventory.patient_id_by_device_id(device_id)
            patient_id = 'x'
            
            # NOTE: using inventory to determine intended wear time period.
            # Useful for historical data, but (TODO) should be replaced with UCAM API. 
            # history = inventory.device_history(device_id)[patient_id]

            # start_wear = utils.format_inventory_weartime(history['checkout'])
            # NOTE: if device not returned the current day is used.
            # end_wear = utils.format_inventory_weartime(history['checkin'])
            start_wear = utils.format_inventory_weartime("2020-01-01 01:01:01")
            end_wear = utils.format_inventory_weartime("2020-01-01 01:01:01")

            record = Record(
                # NOTE: id is the hashedID provided by VTT
                filename=item['id'],
                vttsma_dump_date=item['dumps'][0],
                device_id=device_id,
                patient_id=patient_id,
                start_wear=start_wear,
                end_wear=end_wear
            )

            create_record(record)

            path = Path(config.storage_vol / f'{record.filename}-meta.json')
            # Store metadata from memory to file
            utils.write_json(path, item)
    
    
    def download_file(self, mongo_id: str) -> None:
        """
        Downloads files and store them to {config.storage_vol}

        Tracking: {db.record.is_downloaded} indicates success
        
        NOTE/TODO: is run as a task.
        """
        record = read_record(mongo_id)
        is_downloaded_success = vttsma_api.download_file(self.bucket, record.filename, record.vttsma_dump_date)
        if is_downloaded_success:
            record.is_downloaded = is_downloaded_success
            update_record(record)
        # TODO: otherwise re-start task to try again
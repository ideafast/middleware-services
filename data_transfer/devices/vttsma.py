from pathlib import Path

from mypy_boto3_s3.service_resource import Bucket

from data_transfer import utils
from data_transfer.config import config
from data_transfer.db import all_hashes, create_record, read_record, update_record
from data_transfer.lib import vttsma as vttsma_api
from data_transfer.schemas.record import Record
from data_transfer.services import ucam


class Vttsma:
    def __init__(self) -> None:
        """
        Set up a session to the s3 bucket to use in multiple steps
        """
        self.bucket = self.authenticate()

    def authenticate(self) -> Bucket:
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
        VTT provides a weekly export in an S3 bucket, with a symbolic structure:
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
            - users.txt contains the user hashes present in this export (equal to subfolders)
            - .nfo files contain the time spans of the specific hash exports, e.g.:
                - Start time : 2020-10-28T00:00:01Z
                - End time   : 2020-11-24T00:00:00.001Z

        NOTE/TODO: will run as BATCH job.
        """

        # NOTE: currently downloads all exports (inc. historical) TODO: only since last run
        all_records = vttsma_api.get_list(self.bucket)

        # Only add records that are not known in the DB based on stored filename (id = VTT hash id)
        unknown_records = [r for r in all_records if r["id"] not in set(all_hashes())]

        # Aim: construct valid record (metadata) and add to DB
        for item in unknown_records:

            if patients := ucam.get_one_vtt(item["id"])[0]:
                devices_used = [r for r in patients if r.vttsma_id == item["id"]]

                # Assuming that only one device (phone) is used for the VTT SMA
                # TODO: re-evaluate once data from Newcastle is present on S3
                device_used = devices_used[0]

                record = Record(
                    filename=device_used.vttsma_id,  # NOTE: id is the hashedID provided by VTT
                    device_type=utils.DeviceType.SMA.name,
                    vttsma_export_date=item["exports"][
                        0
                    ],  # TODO: expect data across exports
                    device_id=config.vttsma_global_device_id,  # All VTT-SMA share the same device ID
                    patient_id=patients.patient_id,
                    start_wear=device_used.start_wear,
                    end_wear=device_used.end_wear,
                )

                create_record(record)

                path = Path(config.storage_vol / f"{record.filename}-meta.json")
                # Store metadata from memory to file
                utils.write_json(path, item)

            else:
                # throw / log here
                pass

    def download_file(self, mongo_id: str) -> None:
        """
        Downloads files and store them to {config.storage_vol}

        Tracking: {db.record.is_downloaded} indicates success

        NOTE/TODO: is run as a task.
        """
        record = read_record(mongo_id)
        is_downloaded_success = vttsma_api.download_files(
            self.bucket, record.filename, record.vttsma_export_date
        )
        if is_downloaded_success:
            record.is_downloaded = is_downloaded_success
            update_record(record)
        # TODO: otherwise re-start task to try again

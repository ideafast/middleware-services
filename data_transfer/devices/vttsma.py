import logging
from datetime import datetime
from typing import Dict, List, Optional

import boto3
from mypy_boto3_s3.service_resource import Bucket

from data_transfer import utils
from data_transfer.config import config
from data_transfer.db import all_hashes, create_record, read_record, update_record
from data_transfer.lib import vttsma as vttsma_api
from data_transfer.lib.vttsma import VttsmaRecording
from data_transfer.schemas.record import Record
from data_transfer.services import ucam
from data_transfer.utils import uid_to_hash

log = logging.getLogger(__name__)


class Vttsma:
    def __init__(self) -> None:
        """
        Set up a session to the s3 bucket to use in multiple steps
        """
        self.device_type = utils.DeviceType.SMA
        self.bucket = self.authenticate()

    def authenticate(self) -> Bucket:
        """
        Authenticate once when object created to share session between requests
        """
        session = boto3.session.Session(
            aws_access_key_id=config.vttsma_aws_accesskey,
            aws_secret_access_key=config.vttsma_aws_secret_accesskey,
        )

        s3 = session.resource("s3")
        return s3.Bucket(config.vttsma_aws_bucket_name)

    def download_metadata(self) -> None:
        """
        Before downloading raw data we need to know which files to download.
        VTT provides a weekly export in an S3 bucket, with a symbolic structure,
        which breaks down to key-value pairs, with the key being the path to the value

        NOTE/TODO: will run as BATCH job.
        """

        all_records = vttsma_api.get_list(self.bucket)

        log.info(f"Total vtt_sma records: {len(all_records)} for all study sites")

        unknown_records = self.__unknown_records(all_records)

        log.info(f"Total unknown records: {len(unknown_records.keys())}")

        known, unknown = 0, 0

        for hash_id, item in unknown_records.items():

            # all vtt sma data gets the same device_id
            device_id = config.vttsma_global_device_id

            # our only source of reference is UCAM
            _patient_id = self.__patient_id_from_ucam(
                item.vtt_hash, item.start, item.end
            )

            if not (patient_id := utils.format_id_patient(_patient_id)):
                log.error(
                    f"Record NOT created: Error formatting PatientID ({_patient_id}) for\n{item}\n"
                )
                unknown += 1
                continue

            known += 1

            record = Record(
                hash=hash_id,
                manufacturer_ref=item.full_path,
                device_type=self.device_type.name,
                patient_id=patient_id,
                device_id=device_id,
                start_wear=item.start,
                end_wear=item.end,
            )

            create_record(record)

        log.debug(f"{known} records created and {unknown} NOT this session.")

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

    def __unknown_records(
        self, records: List[VttsmaRecording]
    ) -> Dict[str, VttsmaRecording]:
        """
        Only add records that are not known in the DB based on vtt's hashed full filepath
        """
        results = {}
        known_records = all_hashes()
        for record in records:
            record_hash = uid_to_hash(record.full_path, self.device_type)
            if record_hash not in known_records:
                results[record_hash] = record
        return results

    def __patient_id_from_ucam(
        self, vtt_hash: str, start: datetime, end: datetime
    ) -> Optional[str]:
        """
        Although intended, vtt_hashes can still (historically) occur across patients
        TODO: If multiple patients are found, it will select based on wear period
        TODO: implement ^ once working with live UCAM api
        """
        patient = ucam.record_by_vtt(vtt_hash)
        return patient.patient.id if patient else None

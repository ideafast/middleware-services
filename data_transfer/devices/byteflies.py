from pathlib import Path

import requests

from data_transfer import utils
from data_transfer.config import config
from data_transfer.db import all_filenames, create_record, read_record, update_record
from data_transfer.lib import byteflies as byteflies_api
from data_transfer.schemas.record import Record


class Byteflies:
    def __init__(self) -> None:
        """
        Authenticate with AWS cognito to access ByteFlies resources
        """
        self.session = self.authenticate()

    def authenticate(self) -> requests.Session:
        """
        Authenticate once when object created to share session between requests
        """
        credentials = dict(
            username=config.byteflies_username,
            password=config.byteflies_password,
            client_id=config.byteflies_aws_client_id,
        )
        token = byteflies_api.get_token(credentials)
        session = byteflies_api.get_session(token)
        return session

    def download_metadata(self, from_date: str, to_date: str) -> None:
        """
        Before downloading raw data we need to know which files to download.
        Byteflies offers an API which we can query for a given time period
        ...

        NOTE/TODO: will run as BATCH job.
        """
        # Note: includes metadata for ALL data records, therefore we must filter them
        all_records = byteflies_api.get_list(self.session, from_date, to_date)

        # Only add records that are not known in the DB based on stored filename
        unknown_records = [
            r for r in all_records if r["id"] not in set(all_filenames())
        ]

        # Aim: construct valid record (metadata) and add to DB
        for item in unknown_records:

            # TODO: validate and lookup patientID, e.g.
            # if patient_id := validate_and_format_patient_id(item["patient"]):

            start_wear = utils.format_weartime_from_timestamp(item["startDate"])
            end_wear = utils.get_endwear_by_seconds(start_wear, item["duration"])

            record = Record(
                filename=item["id"],
                device_type=utils.DeviceType.BTF.name,
                device_id=item["dotId"],  # TODO: lookup with IDEAFAST device ID
                patient_id=item["patient"],  # TODO: lookup with IDEAFAST patient ID
                start_wear=start_wear,
                end_wear=end_wear,
                meta=dict(group_id=item["groupId"]),
            )

            create_record(record)

            # NOTE: compared to other devices, ByteFlies metadata is retrieved in
            # the download stage - and a -meta.json file is created there.

    def download_file(self, mongo_id: str) -> None:
        """
        Downloads files and store them to {config.storage_vol}

        Tracking: {db.record.is_downloaded} indicates success

        NOTE/TODO: is run as a task.
        """
        record = read_record(mongo_id)
        is_downloaded_success, metadata, linked_files = byteflies_api.download_file(
            self.session, record.filename, record.meta
        )

        if is_downloaded_success:

            # Store metadata from memory to file
            path = Path(config.storage_vol / f"{record.filename}-meta.json")
            utils.write_json(path, metadata)

            record.is_downloaded = is_downloaded_success
            record.meta["linked_files"] = linked_files
            update_record(record)
        # TODO: otherwise re-start task to try again

from pathlib import Path

import requests

from data_transfer import utils
from data_transfer.config import config
from data_transfer.db import all_filenames, create_record, read_record, update_record
from data_transfer.lib import byteflies as byteflies_api
from data_transfer.schemas.record import Record
from data_transfer.utils import validate_and_format_patient_id


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
        Byteflies offers an API which we can query for a given time period:
        /groups/{groupId}/recordings?begin={begin_date}&end={end_date}
        It returns a list or recordings (see API docs), with most relevant data:

        {
            "id": "...",            # uid of the Recording
            "groupId": "...",       # uid of the group (i.e. study site)
            "patient": "...",       # a patient identifier. Data shows missing and irregular typed ids
            "signals": [            # a list of signal 'objects' containing recordings
                {
                    "id": "...",       # uid of the signal
                    "type": "...",     # type of signals, e.g. ACC, EEG, ECG, GYR ...
                    "quality": "FAIL", # Quality is PASS, CHECK or FAIL
                    "rawData": "https://.." # a url location of the signal data
                },
                ...
            "startDate": 1612439696.583213, # fractional unix timestamp of the start of the recording
            "duration": 32335.190131348,    # fractional unix timestamp of the duration of the recording
            "uploadDate": 1612523536.755,   # fractional unix timestamp of the date of upload
        }
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

            # TODO: integration with UCAM? (Although they don't store byteflies IDs?)
            if patient_id := validate_and_format_patient_id(item["patient"]):

                # NOTE: currently taken from ByteFlies data - not inventory/UCAM
                start_wear = utils.format_weartime_from_timestamp(item["startDate"])
                end_wear = utils.get_endwear_by_seconds(start_wear, item["duration"])

                record = Record(
                    filename=item["id"],
                    device_type=utils.DeviceType.BTF.name,
                    device_id=item[
                        "dotId"
                    ],  # TODO: replace/lookup with IDEAFAST device ID
                    patient_id=patient_id,
                    start_wear=start_wear,
                    end_wear=end_wear,
                )

                create_record(record)

                path = Path(config.storage_vol / f"{record.filename}-meta.json")
                # Store metadata from memory to file
                utils.write_json(path, item)

            else:
                # throw / log here
                print(f"invalid patient ID: {item['patient']}")
                pass

    def download_file(self, mongo_id: str) -> None:
        """
        Downloads files and store them to {config.storage_vol}

        Tracking: {db.record.is_downloaded} indicates success

        NOTE/TODO: is run as a task.
        """
        record = read_record(mongo_id)
        is_downloaded_success = byteflies_api.download_file(
            self.session, record.filename
        )
        if is_downloaded_success:
            record.is_downloaded = is_downloaded_success
            update_record(record)
        # TODO: otherwise re-start task to try again

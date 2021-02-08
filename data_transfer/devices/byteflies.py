from pathlib import Path

import requests

from data_transfer import utils
from data_transfer.config import config
from data_transfer.db import all_filenames, create_record, read_record, update_record
from data_transfer.lib import byteflies as byteflies_api
from data_transfer.schemas.record import Record
from data_transfer.services import inventory


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

    def download_metadata(self) -> None:
        """
        Before downloading raw data we need to know which files to download.
        Byteflies stored data per study site - which we can iterate for metadata.

        This method downloads and stores the metadata as file, and stores most
        relevant metadata as a Record in the database in preparation for next stages.

        NOTE/TODO: will run as BATCH job.
        """
        # Note: includes metadata for ALL data records, therefore we must filter them
        all_records = byteflies_api.get_restricted_list(self.session)

        # Only add records that are not known in the DB based on stored filename
        # i.e. (ID and filename in dreem)
        unknown_records = [
            r for r in all_records if r["id"] not in set(all_filenames())
        ]

        # Aim: construct valid record (metadata) and add to DB
        for item in unknown_records:

            device_serial = byteflies_api.serial_by_device(item["device"])
            device_id = inventory.device_id_by_serial(device_serial)

            # NOTE: lookup Patient ID by email: if None (e.g. personal email used), then use inventory
            patient_id = byteflies_api.patient_id_by_user(
                item["user"]
            ) or inventory.patient_id_by_device_id(device_id)

            # NOTE: using inventory to determine intended wear time period.
            # Useful for historical data, but (TODO) should be replaced with UCAM API.
            history = inventory.device_history(device_id)[patient_id]

            start_wear = utils.format_weartime(history["checkout"], "inventory")
            # NOTE: if device not returned the current day is used.
            end_wear = utils.format_weartime(history["checkin"], "inventory")
            record = Record(
                # NOTE: id is a unique uuid used to GET raw data from Dreem
                filename=item["id"],
                device_type=utils.DeviceType.DRM.name,
                device_id=device_id,
                patient_id=patient_id,
                start_wear=start_wear,
                end_wear=end_wear,
            )

            create_record(record)

            path = Path(config.storage_vol / f"{record.filename}-meta.json")
            # Store metadata from memory to file
            utils.write_json(path, item)

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

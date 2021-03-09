from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import requests

from data_transfer import utils
from data_transfer.config import config
from data_transfer.db import all_hashes, create_record, read_record, update_record
from data_transfer.lib import byteflies as byteflies_api
from data_transfer.schemas.record import Record
from data_transfer.services import inventory, ucam


@dataclass
class BytefliesRecording:
    """
    Stores most relevant metadata for readable lookup.
    """

    # reduces memory by locking the number of fields
    __slots__ = [
        "recording_id",
        "group_id",
        "dock_id",
        "dot_id",
        "patient_id",
        "signal_id",
        "algorithm_id",
        "start",
        "end",
    ]

    recording_id: str
    group_id: str
    dock_id: str
    dot_id: str
    patient_id: str
    signal_id: str

    algorithm_id: Union[str, None]

    start: datetime
    end: datetime


class Byteflies:
    def __init__(self) -> None:
        """
        Authenticate with AWS cognito to access ByteFlies resources
        """
        self.session = self.authenticate()
        self.device_type = utils.DeviceType.BTF.name

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

    def download_metadata(
        self, from_date: str, to_date: str, study_site: utils.StudySite
    ) -> None:
        """
        Before downloading raw data we need to know which files to download.
        Byteflies offers an API which we can query for a given time period
        ...

        NOTE/TODO: will run as BATCH job.
        """
        # Note: includes metadata for ALL data records, therefore we must filter them
        all_records = byteflies_api.get_list(
            self.session, config.byteflies_group_ids[study_site], from_date, to_date
        )
        # utils.write_json("./byteflies.json", all_records)
        # all_records = utils.read_json(Path("./byteflies.json"))

        # Only add records that are not known in the DB based on stored filename
        unknown_records = [
            r for r in all_records if r["IDEAFAST"]["hash"] not in set(all_hashes())
        ]

        for item in unknown_records:
            # Pulls out the most relevant metadata for this recording
            recording = self.recording_metadata(item)

            # NOTE: lookup in .csv export from inventory TODO: translate to inventory api
            if not (
                resolved_device_id := byteflies_api.serial_by_device(recording.dot_id)
            ):
                print(f"Unknown Device:\n   {recording}")
                continue  # Err: SKIP RECORD
            else:
                resolved_device_id = utils.format_id_device(resolved_device_id)

            # saving resolved patient_id back in recording for logging
            recording.patient_id = (
                recording.patient_id  # very sporadically the record has a patient_id already
                or self.__patient_id_from_ucam(
                    resolved_device_id, recording.start, recording.end
                )
                or self.__patient_id_from_inventory(
                    resolved_device_id, recording.start, recording.end
                )
            )

            if not (
                resolved_patient_id := utils.format_id_patient(recording.patient_id)
            ):
                print(f"Unknown Patient:\n   {recording}")
                continue  # Err: SKIP RECORD

            record = Record(
                # can relate to a single download file or a group of files
                hash=item["IDEAFAST"]["hash"],
                manufacturer_ref=recording.recording_id,
                device_type=self.device_type,
                device_id=resolved_device_id,
                patient_id=resolved_patient_id,
                start_wear=recording.start,
                end_wear=recording.end,
                meta=dict(
                    studysite_id=recording.group_id,
                    recording_id=recording.recording_id,
                    signal_id=recording.signal_id,
                    algorithm_id=recording.algorithm_id,
                ),
            )

            create_record(record)
            print(f"Record Created:\n   {record}")

            del item["IDEAFAST"]  # remove record-specific temporary metadata
            path = Path(config.storage_vol / f"{record.manufacturer_ref}-meta.json")
            if not path.exists():
                utils.write_json(path, item)

            print(f"Metadata saved to: {path}\n")

    def download_file(self, mongo_id: str) -> None:
        """
        Downloads files and store them to {config.storage_vol}

        Tracking: {db.record.is_downloaded} indicates success

        NOTE/TODO: is run as a task.
        """
        record = read_record(mongo_id)
        download_folder = f"{record.patient_id}/{record.device_id}"
        is_downloaded_success = byteflies_api.download_file(
            download_folder, self.session, **record.meta
        )

        if is_downloaded_success:
            record.is_downloaded = is_downloaded_success
            update_record(record)

            print(f"Downloaded file for:\n   {record}")
        else:
            print(f"FAILED downloading file for:\n   {record}")

    def recording_metadata(self, recording: dict) -> BytefliesRecording:
        """
        Maps data from ByteFlies response to class to simplify access/logging.
        """
        start_recording = utils.format_weartime_from_timestamp(recording["startDate"])
        end_recording = utils.get_endwear_by_seconds(
            start_recording, recording["duration"]
        )
        signal: dict = next(
            (
                s
                for s in recording["signals"]
                if s["id"] == recording["IDEAFAST"]["signal_id"]
            ),
            None,
        )
        algorithm_id: str = next(
            (
                a["id"]
                for a in signal["algorithms"]
                if a["id"] == recording["IDEAFAST"]["algorithm_id"]
            ),
            None,
        )

        return BytefliesRecording(
            recording["id"],
            recording["groupId"],
            recording["dockName"],
            recording["dotId"],
            recording["patient"],
            signal["id"],
            algorithm_id,
            start_recording,
            end_recording,
        )

    def __patient_id_from_ucam(
        self, device_id: str, start: datetime, end: datetime
    ) -> Optional[str]:
        """
        Determine PatientID by wear period of device in UCAM.
        """
        record = ucam.record_by_wear_period(device_id, start, end)
        if record:
            print("found in UCAM")
        return record.patient_id if record else None

    def __patient_id_from_inventory(
        self, device_id: str, start: datetime, end: datetime
    ) -> Optional[str]:
        """
        Determine PatientID by wear period in inventory.
        """
        record = inventory.record_by_device_id(device_id, start, end)
        if record:
            print("found in Inventory")
        return record.get("patient_id", None) if record else None

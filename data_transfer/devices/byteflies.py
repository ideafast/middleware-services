import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests

from data_transfer import utils
from data_transfer.config import config
from data_transfer.db import all_hashes, create_record, read_record, update_record
from data_transfer.lib import byteflies as byteflies_api
from data_transfer.schemas.record import Record
from data_transfer.services import inventory, ucam
from data_transfer.utils import StudySite

log = logging.getLogger(__name__)


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

    algorithm_id: Optional[str]

    start: datetime
    end: datetime


class Byteflies:
    def __init__(self, study_site: StudySite) -> None:
        """
        Authenticate with AWS cognito to access ByteFlies resources
        """
        self.study_site = study_site
        self.session = self.authenticate()
        self.device_type = utils.DeviceType.BTF.name
        self.file_type = ".csv"

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
        log.info("Authentication successful")
        return session

    def download_metadata(self, from_date: str, to_date: str) -> None:
        """
        Before downloading raw data we need to know which files to download.
        Byteflies offers an API which we can query for a given time period
        ...

        NOTE/TODO: will run as BATCH job.
        """
        # Note: includes metadata for ALL data records, therefore we must filter them
        all_records = byteflies_api.get_list(
            self.session,
            config.byteflies_group_ids[self.study_site],
            from_date,
            to_date,
        )

        log.info(
            f"Total Byteflies records: {len(all_records)} for {self.study_site.name}"
        )

        unknown_records = self.__unknown_records(all_records)

        log.info(f"Total unknown records: {len(unknown_records.keys())}")

        known, unknown = 0, 0

        for hash_id, item in unknown_records.items():
            # Pulls out the most relevant metadata for this recording
            recording = self.recording_metadata(item)

            # NOTE: lookup in .csv export from inventory TODO: translate to inventory api
            if not (_device_id := byteflies_api.serial_by_device(recording.dot_id)):
                log.debug(f"Record NOT created for unknown device\n   {recording}")
                unknown += 1
                continue  # Skip record

            if not (device_id := utils.format_id_device(_device_id)):
                log.error(
                    f"Record NOT created: Error formatting DeviceID ({_device_id}) for\n{recording}\n"
                )
                unknown += 1
                continue

            _patient_id = (
                # To keep UCAM as the source of truth, we ignore the patient_id in the
                # BTF payload - though log to debug later on
                self.__patient_id_from_ucam(device_id, recording.start, recording.end)
                or self.__patient_id_from_inventory(
                    device_id, recording.start, recording.end
                )
            )

            if not (patient_id := utils.format_id_patient(_patient_id)):

                if (api_patient_id := utils.format_id_patient(recording.patient_id)) :
                    log.error(
                        f"Record NOT created: Error finding provided PatientID ({api_patient_id})"
                        f"for\n{recording}\n"
                    )
                else:
                    log.error(
                        f"Record NOT created: Error formatting PatientID ({_patient_id})"
                        f"for\n{recording}\n"
                    )
                unknown += 1
                continue

            known += 1

            record = Record(
                # can relate to a single download file or a group of files
                hash=hash_id,
                manufacturer_ref=recording.recording_id,
                device_type=self.device_type,
                device_id=device_id,
                patient_id=patient_id,
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

            del item["IDEAFAST"]  # remove record-specific temporary metadata
            utils.write_json(record.metadata_path(), item)

        log.debug(f"{known} records created and {unknown} NOT this session.")

    def __unknown_records(self, records: List[dict]) -> Dict[str, dict]:
        """
        Only add records that are not known in the DB, i.e., ID and filename.
        """
        results = {}
        known_records = all_hashes()
        for record in records:
            record_hash = record["IDEAFAST"]["hash"]
            if record_hash not in known_records:
                results[record_hash] = record
        return results

    def download_file(self, mongo_id: str) -> None:
        """
        Downloads files and store them to {config.storage_vol}

        Tracking: {db.record.is_downloaded} indicates success

        NOTE/TODO: is run as a task.
        """
        record = read_record(mongo_id)

        # If pipeline is rerun after an error
        if record.is_downloaded:
            log.debug("Data file already downloaded. Skipping.")
            return

        is_downloaded_success = byteflies_api.download_file(
            self.session,
            record.download_folder(),
            record.meta["studysite_id"],
            record.meta["recording_id"],
            record.meta["signal_id"],
            record.meta["algorithm_id"],
        )

        # filename if succes, False is not
        if is_downloaded_success:
            # Useful metadata for performing pre-processing.
            downloaded_file = Path(
                record.download_folder() / f"{is_downloaded_success}{self.file_type}"
            )
            record.meta["filesize"] = downloaded_file.stat().st_size

            record.is_downloaded = True
            update_record(record)
            log.debug(f"Download SUCCESS for:\n   {record}")
        else:
            log.debug(f"Download FAILED for:\n   {record}")

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

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from data_transfer import utils
from data_transfer.config import config
from data_transfer.db import all_hashes, create_record, read_record, update_record
from data_transfer.lib import dreem as dreem_api
from data_transfer.schemas.record import Record
from data_transfer.services import inventory, ucam
from data_transfer.utils import StudySite, uid_to_hash

log = logging.getLogger(__name__)


@dataclass
class DreemRecording:
    """
    Stores most relevant metadata for readable lookup.
    """

    id: str
    device_id: str
    user_id: str
    start: datetime
    end: datetime


class Dreem:
    def __init__(self, study_site: StudySite):
        """
        Use study_site name to build auth as there are multiple sites/credentials.
        """
        self.study_site = study_site
        self.user_id, self.session = self.authenticate()
        # Used to filter UCAM devices and assign to type to record
        self.device_type = utils.DeviceType.DRM

    def authenticate(self) -> Tuple[str, requests.Session]:
        """
        Authenticate once when object created to share session between requests
        """
        credentials = config.dreem[self.study_site]
        token, user_id = dreem_api.get_token(credentials)
        session = dreem_api.get_session(token)
        log.info(f"Authentication successful: {user_id}")
        return user_id, session

    def download_metadata(self) -> None:
        """
        Before downloading raw data we need to know which files to download.
        Dreem provided a range of metadata (including a report) per data record.

        This method downloads and stores the metadata as file, and stores most
        relevant metadata as a Record in the database in preparation for next stages.

        NOTE/TODO: will run as BATCH job.
        """
        # Note: includes metadata for ALL data records, therefore we must filter them
        all_records = dreem_api.get_restricted_list(self.session, self.user_id)

        log.info(f"Total dreem records: {len(all_records)} for {self.study_site.name}")

        unknown_records = self.__unknown_records(all_records)

        log.info(f"Total unknown records: {len(unknown_records.keys())}")

        known, unknown = 0, 0

        for hash_id, item in unknown_records.items():
            # Pulls out the most relevant metadata for this recording
            recording = self.__recording_metadata(item)

            # There is be a 1-2-1 mapping between IDs and serials via CSV lookup.
            device_serial = dreem_api.serial_by_device(recording.device_id)

            # Serial may not exist in lookup, e.g., if Dreem send a device replacement.
            if not device_serial:
                log.debug(f"Record NOT created for unknown device\n   {recording}")
                unknown += 1
                continue  # Skip record

            _patient_id = (
                # NOTE: PatientID is encoded in email so there is a 1-2-1 mapping.
                dreem_api.patient_id_by_user(recording.user_id)
                or self.__patient_id_from_ucam(
                    device_serial, recording.start, recording.end
                )
                or self.__patient_id_from_inventory(
                    device_serial, recording.start, recording.end
                )
            )

            if not (patient_id := utils.format_id_patient(_patient_id)):
                log.error(
                    f"Record NOT created: Error formatting PatientID ({_patient_id}) for\n{recording}\n"
                )
                unknown += 1
                continue

            device_id = self.__device_id_from_ucam(
                patient_id, recording.start, recording.end
            ) or inventory.device_id_by_serial(device_serial)

            if not patient_id or not device_id:
                log.error(f"Metadata cannot be determined for {recording}")
                log.error(f"Patient ({patient_id}) or Device ID ({device_id}) missing.")
                unknown += 1
                continue  # Skip record
            known += 1

            record = Record(
                hash=hash_id,
                manufacturer_ref=recording.id,
                device_type=self.device_type.name,
                patient_id=patient_id,
                device_id=device_id,
                start_wear=recording.start,
                end_wear=recording.end,
            )

            create_record(record)

            # Store metadata from memory to file
            utils.write_json(record.metadata_path(), item)

        log.debug(f"{known} records created and {unknown} NOT this session.")

    def __unknown_records(self, records: List[Dict]) -> Dict[str, Dict]:
        """
        Only add records that are not known in the DB, i.e., ID and filename.
        """
        results = {}
        known_records = set(all_hashes())
        for record in records:
            record_hash = uid_to_hash(record["id"], self.device_type)
            if record_hash not in known_records:
                results[record_hash] = record
        return results

    def __recording_metadata(self, recording: dict) -> DreemRecording:
        """
        Maps data from Dreem response to class to simplify access/log.
        """
        id = recording["id"]
        device_id = recording["device"]
        user_id = recording["user"]
        # When the recording took place
        start = datetime.fromtimestamp(recording["report"]["start_time"])
        end = datetime.fromtimestamp(recording["report"]["stop_time"])

        return DreemRecording(*(id, device_id, user_id, start, end))

    def __device_id_from_ucam(
        self, patient_id: str, start: datetime, end: datetime
    ) -> Optional[str]:
        """
        Determine DeviceID in UCAM in two ways:

            1. If only one device is used then use Patient ID
            2. Else use wear period to perform lookup.
        """
        if patient_id and (ucam_entry := ucam.get_record(patient_id)):
            devices = [
                d for d in ucam_entry.devices if self.device_type.name in d.device_id
            ]

            # Best-case: only one device was worn and UCAM knows it
            if len(devices) == 1:
                return devices[0].device_id
            # Edge-case: multiple dreem headbands used, e.g., if one broke.
            elif len(devices) > 1:
                # Determine usage based on weartime as it exists in UCAM
                device = ucam.record_by_wear_period_in_list(devices, start, end)
                return device.device_id if device else None
        return None

    def __patient_id_from_ucam(
        self, device_serial: str, start: datetime, end: datetime
    ) -> Optional[str]:
        """
        Determine PatientID by wear period of device in UCAM.

        Note: uses inventory API to determine DeviceID to make association.
        """
        # NOTE/TODO: given this is a 1-1 mapping, why not use a local CSV?
        device_id = inventory.device_id_by_serial(device_serial)
        record = ucam.record_by_wear_period(device_id, start, end)
        # TODO: inventory has small rate limit.
        time.sleep(4)
        return record.patient_id if record else None

    def __patient_id_from_inventory(
        self, device_serial: str, start: datetime, end: datetime
    ) -> Optional[str]:
        """
        Determine PatientID by wear period in inventory.
        """
        device_id = inventory.device_id_by_serial(device_serial)
        record = inventory.record_by_device_id(device_id, start, end)
        time.sleep(4)
        return record.get("patient_id", None) if record else None

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

        is_downloaded_success = dreem_api.download_file(
            self.session, record.download_folder(), record.manufacturer_ref
        )

        if is_downloaded_success:
            # Useful metadata for performing pre-processing.
            downloaded_file = Path(
                record.download_folder() / f"{record.manufacturer_ref}.h5"
            )
            record.meta["filesize"] = downloaded_file.stat().st_size

            record.is_downloaded = is_downloaded_success
            update_record(record)
            log.debug(f"Download SUCCESS for:\n   {record}")
        else:
            log.debug(f"Download FAILED for:\n   {record}")

import time  # temporary ...
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests

from data_transfer import utils
from data_transfer.config import config
from data_transfer.db import all_filenames, create_record, read_record, update_record
from data_transfer.lib import dreem as dreem_api
from data_transfer.schemas.record import Record
from data_transfer.services import inventory, ucam


class Dreem:
    def __init__(self, study_site: str):
        """
        Use study_site name to build auth as there are multiple sites/credentials.
        """
        self.study_site = study_site
        self.user_id, self.session = self.authenticate()

    def authenticate(self) -> Tuple[str, requests.Session]:
        """
        Authenticate once when object created to share session between requests
        """
        credentials = config.dreem[self.study_site]
        token, user_id = dreem_api.get_token(credentials)
        session = dreem_api.get_session(token)
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

        # Only add records that are not known in the DB based on stored filename
        # i.e. (ID and filename in dreem)
        unknown_records = [
            r for r in all_records if r["id"] not in set(all_filenames())
        ]

        for item in unknown_records:
            # Pull out most relevant metadata from the Response item:
            dreem_device_id = item["device"]
            dreem_user_id = item["user"]
            dreem_id = item["id"]
            # When the recording took place
            dreem_start = datetime.fromtimestamp(item["report"]["start_time"])
            dreem_end = datetime.fromtimestamp(item["report"]["stop_time"])

            # There is be a 1-2-1 mapping between IDs and serials via CSV lookup.
            device_serial = dreem_api.serial_by_device(dreem_device_id)

            # Serial may not exist in lookup, e.g., if Dreem send a device replacement.
            if not device_serial:
                print(f"Unknown Device: {dreem_device_id} with Record ID {dreem_id}")
                # Move onto next record: skips logic below to simplify error handling
                continue

            # Records are created in each loop, so reset before use.
            record = None
            # Used to filter UCAM devices and assign to type to record
            dtype = utils.DeviceType.DRM.name

            patient_id = (
                # NOTE: PatientID is encoded in email so there is a 1-2-1 mapping.
                dreem_api.patient_id_by_user(dreem_user_id)
                or self.__patient_id_from_ucam(device_serial, dreem_start, dreem_end)
                or self.__patient_id_from_inventory(
                    device_serial, dreem_start, dreem_end
                )
            )

            # Reformat to mirror UCAM/DMP.
            patient_id = patient_id.replace("-", "") if patient_id else patient_id

            if patient_id and (ucam_entry := ucam.get_record(patient_id)):
                dreem_devices = [d for d in ucam_entry.devices if dtype in d.device_id]

                # Best-case: only one device was worn and UCAM knows it
                if len(dreem_devices) == 1:
                    record = Record(**dreem_devices[0])
                # Edge-case: multiple dreem headbands used, e.g., if one broke.
                elif len(dreem_devices) > 1:
                    # Determine usage based on weartime
                    _record = ucam.record_by_wear_period_in_list(
                        dreem_devices, dreem_start, dreem_end
                    )
                    _record = Record(**asdict(_record))
                # Edge-case: device not logged with patient in UCAM
                else:
                    print(
                        f"""Record not in UCAM.
                        Device ID: {dreem_device_id},
                        Dreem ID: {dreem_id},
                        User ID: {dreem_user_id}"""
                    )
                    continue
            else:
                print(f"Metadata cannot be determined for: {dreem_device_id}")
                continue

            record.filename = dreem_id
            record.device_type = dtype

            create_record(record)
            print(f"Record Created: {record}")

            path = Path(config.storage_vol / f"{record.filename}-meta.json")
            # Store metadata from memory to file
            utils.write_json(path, item)

            print(f"Metadata saved to: {path}")

    def __patient_id_from_ucam(
        self, device_serial: str, dreem_start: datetime, dreem_end: datetime
    ) -> Optional[str]:
        """
        Determine PatientID by wear period of device in UCAM.
        """
        # NOTE/TODO: given this is a 1-1 mapping, why not use a local CSV?
        device_id = inventory.device_id_by_serial(device_serial)
        record = ucam.record_by_wear_period(device_id, dreem_start, dreem_end)
        # TODO: inventory has small rate limit.
        time.sleep(2.5)
        return record.patient_id if record else None

    def __patient_id_from_inventory(
        self, device_serial: str, dreem_start: datetime, dreem_end: datetime
    ) -> Optional[str]:
        """
        Determine PatientID by wear period in inventory.
        """
        device_id = inventory.device_id_by_serial(device_serial)
        record = inventory.patient_id_by_device_id(device_id, dreem_start, dreem_end)
        time.sleep(2.5)
        return record.get("patient_id", None) if record else None

    def download_file(self, mongo_id: str) -> None:
        """
        Downloads files and store them to {config.storage_vol}

        Tracking: {db.record.is_downloaded} indicates success

        NOTE/TODO: is run as a task.
        """
        record = read_record(mongo_id)
        is_downloaded_success = dreem_api.download_file(self.session, record.filename)
        if is_downloaded_success:
            record.is_downloaded = is_downloaded_success
            update_record(record)
        # TODO: otherwise re-start task to try again

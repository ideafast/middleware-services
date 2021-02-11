import json
import time  # temporary ...
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Tuple

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
            # ??
            device_serial = dreem_api.serial_by_device(item["device"])

            # Serial may not exist in lookup, e.g., if Dreem send a device replacement.
            if not device_serial:
                print(f"Unknown Device: {item['device']} with Record ID {item['id']}")
                # Move onto next record: skips logic below to simplify error handling
                continue

            # reset on each loop
            record = None
            # When the recording took place
            dreem_start = datetime.fromtimestamp(item["report"]["start_time"])
            dreem_end = datetime.fromtimestamp(item["report"]["stop_time"])

            # 1. Determine PatientID with associated email.
            # NOTE: PatientID is encoded in email so there is a 1-2-1 mapping.
            patient_id = dreem_api.patient_id_by_user(item["user"])

            # NOTE: a personal email may be used or (historically) a shared email.
            if not patient_id:
                # 2. Determine PatientID by wear period of this unique device
                # NOTE: devices are unique therefore
                device_id = inventory.device_id_by_serial(device_serial)

                record = ucam.record_by_wear_period(device_id, dreem_start, dreem_end)
                # TODO: we might instead
                patient_id = record.patient_id if record else patient_id
                time.sleep(2.5)
                # 3. Determine PatientID by wear period in inventory.
                if not patient_id:
                    # NOTE: potential alternative could be to perform lookup in UCAM based on device histories
                    # e.g., since we know DeviceID above
                    history_record = inventory.patient_id_by_device_id(
                        device_id, dreem_start, dreem_end
                    )
                    patient_id = (
                        history_record["patient_id"] if history_record else None
                    )
                    time.sleep(2.5)

            patient_id = patient_id.replace("-", "") if patient_id else patient_id

            if patient_id and (ucam_entry := ucam.get_record(patient_id)):
                dreem_devices = [
                    d for d in ucam_entry.devices if device_type in d.device_id
                ]

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
                # Edge-case: UCAM record does not exist
                # e.g. clinician may have forgotten to add Dreem to UCAM
                #  NOTE: could remove this and let the ELSE below resolve it?
                elif len(dreem_devices) == 0:
                    # TODO: this is rare condition, so notify us?
                    # Why do this over inventory? More reliable ...
                    device_id = inventory.device_id_by_serial(device_serial)
                    devices = [d for d in ucam_entry.devices]
                    _record = Record(
                        patient_id=patient_id,
                        device_id=device_id,
                        # TODO: is this assumption too great?
                        start_wear=dreem_start,
                        end_wear=dreem_end,
                    )
            # We cannot determine Patient ID from Dreem UUID, or the Device ID from wear period
            else:
                # TODO: log relevant data
                pass

            record.filename = item["id"]
            record.device_type = utils.DeviceType.DRM.name

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
        print(f"Downloading ... {record}")
        # TODO: decorate or/and override this method via ENV such that local (empty)
        # file is written to emulate procedure?
        is_downloaded_success = dreem_api.download_file(self.session, record.filename)
        if is_downloaded_success:
            record.is_downloaded = is_downloaded_success
            update_record(record)
        # TODO: otherwise re-start task to try again

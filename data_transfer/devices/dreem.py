from pathlib import Path
from typing import Tuple

import requests

from data_transfer import utils
from data_transfer.config import config
from data_transfer.db import all_filenames, create_record, read_record, update_record
from data_transfer.lib import dreem as dreem_api
from data_transfer.services import inventory, ucam
from data_transfer.schemas.record import Record
from data_transfer.services import inventory

import time # temporary ...

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
        # all_records = dreem_api.get_restricted_list(self.session, self.user_id)

        # utils.write_json("./newcastle-yo.json", all_records)
        all_records = utils.read_json("./kiel.json")

        # Only add records that are not known in the DB based on stored filename
        # i.e. (ID and filename in dreem)
        unknown_records = [
            r for r in all_records if r["id"] not in set(all_filenames())
        ]

        unknown_records = unknown_records[0:1]

        for item in unknown_records:
            device_serial = dreem_api.serial_by_device(item['device'])

            # This may not exist in our CSV/mocked endpoint
            # e.g., if Dreem send a device replacement. 
            if not device_serial:
                print (f"Unknown Device: {item['device']} with Record ID {item['id']}")
                # Move onto next record: skips logic below to simplify error handling
                continue

            patient_id = dreem_api.patient_id_by_user(item['user'])

            # As this is reassigned below we must reset it here.
            device_id = None
            #
            start_wear = None
            end_wear = None

            # # Note: this start_time and duration
            unix_start = item['report']['start_time']
            dreem_start = datetime.fromtimestamp(unix_start)
            dreem_end = datetime.fromtimestamp(unix_start + item['report']['duration'])


            record = Record(
                # NOTE: id is a unique uuid used to GET raw data from Dreem
                filename=item['id'],
                device_type=utils.DeviceType.DRM.name,
                device_id=device_id,
                patient_id=patient_id,
                start_wear=start_wear,
                end_wear=end_wear
            )

            if patient_id and (ucam_entry := ucam.get_record(patient_id)):
                dreem_devices = [d for d in ucam_entry.devices if 'DRM' in d.id]

                # Best-case: only one device was worn and UCAM knows it
                if len(dreem_devices) == 1:
                    print ("single", device_id, ucam_entry.patient.id)
                    _record = dreem_devices[0]
                    device_id = _record.id
                    start_wear = _record.start_wear
                    end_wear = _record.end_wear
                # Edge-case: multiple dreem headbands used, e.g., if one broke.
                elif len(dreem_devices) > 1:
                    # Determine usage based on weartime
                    _record = [d for d in dreem_devices if d.id == device_id]
                    # What if the device ID differs from the one the patient used?
                    # NOTE: unclear why this might happen ... user-input error?
                    # TODO: rather than do this, we could just do wear period?
                    if len(_record) == 1:
                        _record = _record[0]
                        device_id = _record.id
                        start_wear = _record.start_wear
                        end_wear = _record.end_wear
                    continue
                # Worst-case: UCAM record exists for this user, but not this device.
                # e.g. the clinician may have forgotten to add Dreem to UCAM
                elif len(dreem_devices) == 0:
                    # Why do this over inventory? More reliable ...
                    device_id = inventory.device_id_by_serial(device_serial)
                    devices = [d for d in ucam_entry.devices]
                    start_wear = min([d.start_wear for d in devices])
                    end_wear = max([d.end_wear for d in devices])
            # Data was recorded but user not in UCAM, so use inventory instead
            # This is primarily for historical data and extreme edge-cases.
            else:
                continue
                # # NOTE: determine Patient ID by Inventory History: 
                # # DESIRED: weartime (via dreem unix start, end) and Patient ID.
                # device_id = inventory.device_id_by_serial(device_serial)
                
                # # Note: this start_time and duration
                # unix_start = item['report']['start_time']
                # __start_wear = datetime.fromtimestamp(unix_start)
                # __end_wear = datetime.fromtimestamp(unix_start + item['report']['duration'])

                # # print ("bfinal", device_id, item['id'], start_wear, end_wear)
                # # TODO: this method should have same name as above ...
                # history_record = inventory.patient_id_by_device_id(device_id, __start_wear, __end_wear)

                # print (history_record)

                # if history_record:
                #     checkin = history_record['checkin'] or datetime.now().strftime(utils.FORMATS['inventory'])

                #     start_wear = utils.format_weartime(history_record['checkout'], 'inventory')
                #     end_wear = utils.format_weartime(checkin, 'inventory')
                #     patient_id = history_record['patient_id']
                #     # if patient_id:
                #     #     print ("in here?")
                #     #     ucam_record = ucam.get_record(patient_id)
                #     #     rec = [d for d in ucam_record.devices if d.id == device_id]
                #     #     start_wear, end_wear = rec[0].start_wear, rec[0].end_wear
            time.sleep(5)
            continue

            print(patient_id, device_id, start_wear, end_wear)
            if not end_wear:
                end_wear = start_wear

            if None in [patient_id, device_id, start_wear, end_wear]:
                # TODO: email us as these are required attributes
                continue

            # Even though these may not exist, we want to store them with None entries
            # As we will likely have edge-cases that require manual looking up initially.
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
        print (f"Downloading ... {record}")
        # TODO: decorate or/and override this method via ENV such that local (empty)
        # file is written to emulate procedure?
        is_downloaded_success = dreem_api.download_file(self.session, record.filename)
        if is_downloaded_success:
            record.is_downloaded = is_downloaded_success
            update_record(record)
        # TODO: otherwise re-start task to try again

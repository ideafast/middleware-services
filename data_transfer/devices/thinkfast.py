"""
for most devices this file does the following:
> authenticate with the partner's API
> download metadata
> store metadata
> check if device ID is in UCAM
> download a file

unused methods which Jay used for Dreem:
def __unknown_records

"""
# import json
import logging

# import time
from dataclasses import dataclass
from datetime import datetime

# from pathlib import Path
# from typing import Dict, List, Optional, Tuple
from typing import Dict, List

from data_transfer import utils

# from data_transfer.config import config
from data_transfer.db import all_hashes, create_record

# from data_transfer.db import all_hashes, create_record, read_record, update_record
from data_transfer.lib import thinkfast as thinkfast_api
from data_transfer.schemas.record import Record

# from data_transfer.services import inventory, ucam
from data_transfer.utils import StudySite, uid_to_hash

# import requests


# from data_transfer.utils import StudySite, uid_to_hash, write_json

log = logging.getLogger(__name__)


@dataclass
class ThinkFastRecording:
    """
    Stores most relevant metadata for readable lookup.
    """

    id: str
    device_id: str
    user_id: str
    start: datetime
    end: datetime


@dataclass
class Participant:
    """
    Stores key participant data.
    """

    id_ideafast: str
    id_connect: str
    guid: str


class ThinkFast:
    def __init__(self, study_site: StudySite):
        """
        Use study_site name to build auth as there are multiple sites/credentials.
        """
        self.study_site = study_site
        self.device_type = utils.DeviceType.TFA

    def __unknown_records(self, records: list) -> Dict:
        """
        Only add records that are not known in the DB, i.e., ID and filename.
        """
        results = {}
        known_records = all_hashes()
        for record in records:
            record_hash = uid_to_hash(record.manufacturer_ref, self.device_type)
            if record_hash not in known_records:
                results[record_hash] = record
        return results

    def format_record(self, raw_rec: Dict, participant: Participant) -> Record:
        """
        takes a single record from the api return
        and extracts the parameters used to create our 'record'
        """

        new_record = Record(
            hash=uid_to_hash(raw_rec["id"], self.device_type),
            manufacturer_ref=raw_rec["id"],
            device_type="TFA",
            patient_id=participant.id_ideafast,
            device_id="TFAP6RJG3",
            start_wear=raw_rec["startTime"],
            end_wear=raw_rec["itemGroups"][0]["endTime"],
            is_downloaded=True,
        )

        if raw_rec["itemGroups"][0]["items"][0]["measureCode"] == "SWMTE":
            new_record.meta = {"tfa_type": "CANTAB", "full_data": raw_rec}
        else:
            new_record.meta = {
                "tfa_type": "ThinkFAST",
                "full_data": raw_rec["itemGroups"][0]["items"],
            }
        return new_record

    def download_participants_data(self) -> None:
        """
        get all participant data on the thinkfast platform and return unknown records
        """
        participants: List = thinkfast_api.get_participants()
        # print the number of participants
        remaining = len(participants)
        log.debug(f"Number of our participants found in CamCog's database: {remaining}")

        # loop through our list of participants retreiving their test data
        for participant in participants:
            raw_records = thinkfast_api.get_participants_records(participant.guid)
            if len(raw_records) != 1:
                log.debug(
                    "Wow, raw_rec length is not 1, it is: " + str(len(raw_records))
                )
            # setup to process and store these records
            all_recs = []
            # create a formatted record
            # print("length of raw_records[0]: " + str(len(raw_records[0])))
            # LOOP THROUGH RAW_RECORDS[0] making an entry for each
            for record in raw_records[0]:
                try:
                    newRec = self.format_record(record, participant)
                    if newRec:
                        all_recs.append(newRec)
                except Exception:
                    log.debug("failed to create this record")
            # do a diff with our DB
            unknown_records = self.__unknown_records(all_recs)
            log.debug(
                "Participant "
                + participant.guid
                + " has "
                + str(len(raw_records[0]))
                + " total TFA records. Writing "
                + str(len(unknown_records))
                + " new records to the DB"
            )
            # push the new records into the DB
            for record in unknown_records.values():
                create_record(record)
                # create path
                if record.meta["tfa_type"] == "CANTAB":
                    path = (
                        record.download_folder()
                        / f"{record.manufacturer_ref}-CANTAB.json"
                    )
                elif record.meta["tfa_type"] == "ThinkFAST":
                    path = (
                        record.download_folder()
                        / f"{record.manufacturer_ref}-ThinkFAST.json"
                    )
                else:
                    path = (
                        record.download_folder()
                        / f"{record.manufacturer_ref}-unknown.json"
                    )
                # write the record locally
                utils.write_json(path, record.meta["full_data"])
                # utils.write_json(path, json.loads(record.dumps['full_data'], default=str))

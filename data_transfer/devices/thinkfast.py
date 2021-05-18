"""
for most devices this file does the following:
> authenticate with the partner's API
> download metadata
> store metadata
> check if device ID is in UCAM
> download a file
"""
import logging
from dataclasses import dataclass
from typing import Dict, List

from data_transfer import utils
from data_transfer.db import all_hashes, create_record
from data_transfer.lib import thinkfast as thinkfast_api
from data_transfer.schemas.record import Record
from data_transfer.utils import StudySite, uid_to_hash

log = logging.getLogger(__name__)


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

    def __unknown_records(self, records: List[Record]) -> Dict[str, Record]:
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
        # remove the 'user' field which contains
        # clinician name and email and therefore may be a GDPR concern
        raw_rec.pop("users")

        is_cantab = raw_rec["itemGroups"][0]["items"][0]["measureCode"] == "SWMTE"
        tfa_type = "CANTAB" if is_cantab else "ThinkFAST"
        new_record.meta = {"tfa_type": tfa_type, "full_data": raw_rec}

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
                continue
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
                f"Participant {participant.guid} has {len(raw_records[0])}"
                f"total TFA records. Writing {(len(unknown_records))} new records to the DB"
            )
            # push the new records into the DB
            for record in unknown_records.values():
                data = record.meta.pop("full_data")
                create_record(record)
                # create path
                path = (
                    record.download_folder()
                    / f"{record.manufacturer_ref}-{record.meta['tfa_type']}.json"
                )
                # write the record locally
                utils.write_json(path, data)
                # utils.write_json(path, json.loads(record.dumps['full_data'], default=str))

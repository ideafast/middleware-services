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
import json
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
from data_transfer.lib import thinkfast as thinkfast_api
from data_transfer.schemas.record import Record
from data_transfer.services import inventory, ucam
from data_transfer.utils import StudySite, uid_to_hash, write_json

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

    def __unknown_records(self, records: List[Dict]) -> Dict[str, Dict]:
        """
        Only add records that are not known in the DB, i.e., ID and filename.
        """
        results = {}
        known_records = all_hashes()
        for record in records:
            record_hash = uid_to_hash(record, self.device_type)
            if record_hash not in known_records:
                results[record_hash] = record
        return results

    def format_record(self, raw_rec, participant) -> Record:
        print("formatting record")
        text = json.dumps(raw_rec, sort_keys=True, indent=4)
        print(text)
        # TO DO - OBVIOUSLY THIS NEEDS FIXING!!!!
        new_record = Record(
            hash="hash_id",
            manufacturer_ref=raw_rec["id"],
            device_type="TFA",
            patient_id=participant.id_ideafast,
            device_id="TFAP6RJG3",
            start_wear=datetime.now(),
            end_wear=datetime.now(),
        )
        return new_record

    def download_participants_data(self) -> None:
        """
        get a list of all participants on the thinkfast platform
        """
        participants: List = thinkfast_api.get_participants()
        # print the number of participants
        remaining = len(participants)
        log.debug(
            f"Number of our participants found in CamCog's database: " + str(remaining)
        )

        # loop through our list of participants retreiving their test data
        for participant in participants:
            raw_records = thinkfast_api.get_participants_records(participant.guid)
            print(f"total records for this participant: " + str(len(raw_records)))

            for raw_rec in raw_records:
                # loop thought and create a formatted record
                new_rec = self.format_record(raw_rec, participant)
                return
                # check if this already exists in the DB
                # if not, create a record
                # create_record(new_rec)

            return
            # record = Record(
            #     hash=hash_id,
            #     manufacturer_ref=recording.id,
            #     device_type=self.device_type.name,
            #     patient_id=patient_id,
            #     device_id=device_id,
            #     start_wear=recording.start,
            #     end_wear=recording.end,
            # )

            """
            # create record and store to json
            # print(records)
            #return
            # print number of participants remaining
            remaining = remaining - 1
            print(str(remaining) + " participants to go")
            # setup for API call
            self.parameters["offset"] = 0
            result = []
            new_results = []
            deviceId = "TFAP6RJG3"  # hard coded as they all share the same device ID
            # set the filter to use the next participant's information
            log.debug(f"getting data for subject with GUID: " + rec.guid)
            filter = json.dumps({"subject": rec.guid})
            self.parameters["filter"] = filter
            # make api call(s) to retreive data for this participant
            startTime = (
                2000000000000  # random high start time which we will reduce in the loop
            )
            endTime = 1000000000000  # random low time which we will incrase in the loop

            # make the api calls until total records are retreived

            # do a diff to only keep unknown records
            unknown_records = self.__unknown_records(all_records)

            # CHANGE THIS NEXT LOOP TO COMPARE EACH RECORD AGAINST THE MONGO DB - PASS NEW RECORDS TO A NEW_RECORDS ARRAY
            # loop through the results looking for the earliest start time

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
                            utils.write_json(record.metadata_path(), x)

                write_json("./test.json", response.json()['records'])
                break
                for record in response.json()['records']:
                    # if isinstance(x["startTime"], int): #protection added as I occasionnally hit a 'type = none' bug
                    #     if x["startTime"] < startTime:
                    #         startTime = x["startTime"]
                    # for y in x["itemGroups"]:
                    #     if isinstance(y["endTime"], int):
                    #         if y["endTime"] > endTime:
                    #             endTime = y["endTime"]

                    # make the hash
                    uid_to_hash()
                # increment offset
                self.parameters['offset'] += 100
                # check if all records retreived for this subject/guid
                if self.parameters['offset'] > response.json()['total']:
                    # check we have something to write by ensuring start and end time got updated
                    if startTime != 2000000000000 and endTime != 1000000000000:
                        # write the json records to disk
                            #first, prep startTime & endTime
                        newStart = str(time.strftime('%Y%m%d', time.localtime(startTime/1000)))
                        newEnd = str(time.strftime('%Y%m%d', time.localtime(endTime/1000)))
                        pName = rec.ideafast_id.replace(" ", "_")
                        dirName = "./camcogData/" + pName + "-" + deviceId + "-" + newStart + "-" + newEnd
                        fileName = dirName + "/" + pName + "-" + deviceId + "-" + newStart + "-" + newEnd + ".json"

                        try:
                            os.mkdir(dirName)
                        except OSError:
                            print ("creation of the directory %s failed" % dirName)
                        else:
                            print ("succesfully created the directory %s " % dirName)
                        with open(fileName, "wb") as outfile:
                            json.dump(result, outfile)
                        zip_and_rm(dirName)

                    break

            """

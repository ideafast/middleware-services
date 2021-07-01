import csv
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from data_transfer.config import config
from data_transfer.utils import format_id_patient

log = logging.getLogger(__name__)


@dataclass
class Participant:
    id_ideafast: str
    id_connect: str
    guid: str


def get_participants_records(user_id: str) -> List[dict]:
    headers_dict = {"accept": "application/json", "content-type": "application/json"}
    parameters: Dict[str, Any] = {
        "offset": 0,
        "limit": 100,
        "filter": json.dumps({"subject": user_id}),
    }
    results = []
    while True:
        try:
            response = requests.get(
                f"{config.thinkfast_api_url}/visit",
                params=parameters,
                headers=headers_dict,
                auth=(config.thinkfast_username, config.thinkfast_password),
            )
            response.raise_for_status()
            # store the response
            data = response.json()
            results.append(data["records"])
            log.debug(f"total records for this participant are: {data['total']}")
            parameters["offset"] += 100
            if parameters["offset"] > data["total"]:
                break
        except requests.HTTPError:
            log.error("GET Exception to:", exc_info=True)
            break
    return results


def id_in_whitelist(input_ID: str) -> Optional[str]:
    """
    correct known incorrect participant IDs
    """
    # known_incorrect_ids: Dict[str, str] = {}

    # load the csv containing the incorrect IDs and corrections
    with open(config.tfa_id_corrections, mode="r") as infile:
        reader = csv.reader(infile)
        # skip first line
        next(reader)
        known_incorrect_ids = {rows[0]: rows[1] for rows in reader}

    if input_ID in known_incorrect_ids:
        output_ID = known_incorrect_ids[input_ID]
        log.warning(
            f"CORRECTED AN ERROR USING THE known_incorrect_ids DICT: "
            f"INPUT {input_ID}, OUTPUT: {output_ID}"
        )
    else:
        output_ID = None
    return output_ID


def get_participant_id(subjectItems: dict) -> Optional[str]:
    # the ID can be placed in any of the list items. Iterate untill found.
    ideaId = ""

    for item in subjectItems:
        ideaId = format_id_patient(item["text"]) or id_in_whitelist(item["text"])
        if ideaId:
            break

    return ideaId


def get_participants() -> List[Participant]:
    # will store our participant records
    headers_dict = {"accept": "application/json", "content-type": "application/json"}
    parameters: Dict[str, Any] = {
        "offset": "0",
        "limit": "100",
        "includes": "subjectIds,site,subjectItems",
    }
    participants = []

    while True:
        # make API call
        try:
            response = requests.get(
                f"{config.thinkfast_api_url}/subject",
                headers=headers_dict,
                params=parameters,
                auth=(config.thinkfast_username, config.thinkfast_password),
            )
        except requests.HTTPError:
            log.error("GET Exception to:", exc_info=True)
            break
        # push participant identifiers into participants array
        for rec in response.json()["records"]:
            # get the participant's ID
            newID = get_participant_id(rec["subjectItems"])
            if newID:
                participants.append(Participant(newID, rec["subjectIds"][0], rec["id"]))
            else:
                log.error(f"Could not associate patient: {rec}")
        # increment offset by the retreival limit
        parameters["offset"] = str(int(parameters["offset"]) + 100)
        # got all the data or do we need to make more API calls?
        if int(parameters["offset"]) > int(response.json()["total"]):
            break
    return participants

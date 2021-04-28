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
    known_incorrect_ids: Dict[str, str] = {}
    if input_ID in known_incorrect_ids:
        output_ID = known_incorrect_ids[input_ID]
        log.warning(
            f"CORRECTED AN ERROR USING THE ODDITIES DICT: INPUT {input_ID}, OUTPUT: {output_ID}"
        )
    else:
        output_ID = input_ID
    return output_ID


def get_participant_id(subjectItems: Dict[int, Any]) -> Optional[str]:
    # find the ideaFast id in the json...
    # this is a bit tricky as it's not always in the same place.
    ideaId = ""

    # The line below is a horribly shakey solution!
    if len(subjectItems[2]["text"]) == 7:
        ideaId = subjectItems[2]["text"]
    else:
        ideaId = subjectItems[1]["text"]
    # validate ID
    newID = format_id_patient(ideaId)
    if newID is None:
        log.debug(f"INVALID ID FOUND WITHIN THE THINKFAST RECORDS. ID = {ideaId}")
        # check dictionary of oddities and if we have a hit do the replacement
        newID = id_in_whitelist(newID)
    return newID


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
            participants.append(Participant(newID, rec["subjectIds"][0], rec["id"]))
        # increment offset by the retreival limit
        parameters["offset"] = str(int(parameters["offset"]) + 100)
        # got all the data or do we need to make more API calls?
        if int(parameters["offset"]) > int(response.json()["total"]):
            break
    return participants

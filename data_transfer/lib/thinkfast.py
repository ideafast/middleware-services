# This file should assist downloading data from thinkfast/CamCog's
# platform per study-site

import json
import logging
from dataclasses import dataclass
from typing import Dict, List

import requests

from data_transfer.config import config
from data_transfer.utils import format_id_patient

log = logging.getLogger(__name__)


@dataclass
class Participant:
    id_ideafast: str
    id_connect: str
    guid: str


def get_session(token: str) -> requests.Session:
    """
    Builds a requests session object with the required header
    """
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


def get_participants_records(user_id: str) -> List[dict]:
    headers_dict = {"accept": "application/json", "content-type": "application/json"}
    parameters = {"offset": 0, "limit": 100}
    filter = json.dumps({"subject": user_id})
    parameters["filter"] = int(filter)
    # sort = json.dumps([{"property":"id", "direction":"ASC"}])
    # parameters['sort'] = sort
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
            results.append(response.json()["records"])
            log.debug(
                "total records for this participant are: "
                + str(response.json()["total"])
            )
            parameters["offset"] += 100
            if parameters["offset"] > response.json()["total"]:
                break
        except requests.HTTPError:
            log.error("GET Exception to:", exc_info=True)
    return results


def get_participants() -> List[Participant]:
    # will store our participant records
    headers_dict = {"accept": "application/json", "content-type": "application/json"}
    parameters = {
        "offset": "0",
        "limit": "100",
        "includes": "subjectIds,site,subjectItems",
    }
    participants = []
    known_incorrect_ids: Dict[str, str] = {}

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
            # find the ideaFast id in the json...
            # this is a bit tricky as it's not always in the same place.
            ideaId = ""
            # The line below is a horribly shakey solution!
            if len(rec["subjectItems"][2]["text"]) == 7:
                ideaId = rec["subjectItems"][2]["text"]
            else:
                ideaId = rec["subjectItems"][1]["text"]
            # validate ID
            newID = format_id_patient(ideaId)
            if newID is None:
                log.debug(
                    f"INVALID ID FOUND WITHIN THE THINKFAST RECORDS. ID = {ideaId}"
                )
                # check dictionary of oddities and if we have a hit do the replacement
                if ideaId in known_incorrect_ids:
                    print(
                        f"CORRECTED AN ERROR USING THE ODDITIES DICT: {known_incorrect_ids[ideaId]}"
                    )
                    newID = known_incorrect_ids[ideaId]
                else:
                    continue
            participants.append(Participant(newID, rec["subjectIds"][0], rec["id"]))
        # increment offset by the retreival limit
        parameters["offset"] = str(int(parameters["offset"]) + 100)
        # got all the data or do we need to make more API calls?
        if parameters["offset"] > response.json()["total"]:
            break
    return participants

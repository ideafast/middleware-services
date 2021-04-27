# This file should assist downloading data from thinkfast/CamCog's
# platform per study-site

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from data_transfer.config import config
from data_transfer.utils import format_id_patient, read_csv_from_cache

log = logging.getLogger(__name__)


@dataclass
class Participant:
    id_ideafast: str
    id_connect: str
    guid: str


def get_token(creds: dict) -> Tuple[str, str]:
    """
    Generates a JWT token with the credentials for API access
    """
    url = f"{config.dreem_login_url}/token/"
    try:
        res = requests.post(url, auth=creds)
        res.raise_for_status()
        resp = res.json()
        return (resp["token"], resp["user_id"])
    except requests.HTTPError:
        log.error(f"GET Exception to: {url}\n", exc_info=True)
        # We do not want to rest of the pipeline to try and proceed
        raise


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
        except requests.HTTPError:
            log.error("GET Exception to:", exc_info=True)
    return participants


def download_file(
    session: requests.Session, download_path: Path, record_id: str
) -> bool:
    """
    GET specified file based on known record
    """
    url = f"{config.dreem_api_url}/dreem/algorythm/record/{record_id}/h5/"
    try:
        response = session.get(url)
        response.raise_for_status()

        result: dict = response.json()

        log.debug(f"Response from {url} was:\n    {result}")

        file_url = result.get("data_url", None)
        # NOTE: file_url may be empty if a file is unavailable:
        # (1): file is on dreem headband but not uploaded
        # (2): file is being processed by dreem's algorithms
        if not file_url:
            return False
        return __download_file(file_url, download_path, record_id)
    except requests.HTTPError:
        log.error(f"GET Exception to {url} ", exc_info=True)
        return False


def serial_by_device(uuid: str) -> Optional[str]:
    """
    Lookup Device ID by dreem headband serial
    """
    serial = __key_by_value(config.dreem_devices, uuid)
    return serial


def patient_id_by_user(uuid: str) -> Optional[str]:
    """
    Lookup Patient ID by dreem email hash.
    """
    email = __key_by_value(config.dreem_users, uuid)
    if email:
        # Initially, gmail accounts were used for dreem based on SamsungA40 ID.
        # We want to skip this record and determine PatientID elsewhere.
        if "gmail" in email:
            return None
        email = email.replace("ideafast.", "")
        email = email.split("@")[0]
        # Create consistency in Patient ID format
        if email[1] != "-":
            email = f"{email[0]}-{email[1:]}"
    # TODO: what if personal email used (e.g., in CVS)?
    return email


def __key_by_value(filename: Path, needle: str) -> Optional[str]:
    """
    Helper method to find key in CSV by value (needle)
    """
    data = read_csv_from_cache(filename)
    for item in data:
        if needle == item["hash"]:
            return str(item["value"])
    return None


def __download_file(url: str, download_path: Path, record_id: str) -> bool:
    """
    Builds the target filename and starts downloading the file to disk

    Args:
        url: AWS URL to download file.
        download_path: path to download folder.
        record_id: what to name the record.
    """
    try:

        file_path = download_path / f"{record_id}.h5"

        with requests.get(url, stream=True) as response:
            log.debug(response.headers)

            response.raise_for_status()

            with open(file_path, "wb") as output_file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        output_file.write(chunk)
        return True
    except Exception:
        log.error("Exception:", exc_info=True)
        return False

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

import requests

from data_transfer.config import config
from data_transfer.utils import DeviceType, read_csv_from_cache, uid_to_hash

log = logging.getLogger(__name__)


def get_token(creds: dict) -> str:
    """
    Generates a AWS Cognito IdToken for API access
    # NOTE: generally expires in 60 minutes
    # TODO: establish token refreshing depending on \
        frequency/length of DAG
    """
    res = requests.post(
        f"{config.byteflies_aws_auth_url}",
        headers={
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1",
        },
        json={
            "ClientId": f"{creds['client_id']}",
            "AuthFlow": "USER_PASSWORD_AUTH",
            "AuthParameters": {
                "USERNAME": f"{creds['username']}",
                "PASSWORD": f"{creds['password']}",
            },
        },
    )
    #  TODO: catch/log exception
    res.raise_for_status()
    resp = res.json()
    return str(resp["AuthenticationResult"]["IdToken"])


def get_session(token: str) -> requests.Session:
    """
    Builds a requests session object with the required header
    """
    session = requests.Session()
    session.headers.update({"Authorization": f"{token}"})
    return session


def get_list(
    session: requests.Session, studysite_id: str, from_date: str, to_date: str
) -> List[dict]:
    """
    GET a list of records (metadata) across study sites, or 'groups' in ByteFlies API
    """

    @dataclass
    class __metadata_copy:
        """Generator for deepcopying a BTF json object"""

        jsondump: str

        def get(self, signal_id: str, algorithm_id: str = "") -> Any:
            copy = json.loads(self.jsondump)
            # injecting data to copy with duplicates all based on one recording
            copy["IDEAFAST"] = {
                "hash": uid_to_hash(
                    f"{copy['id']}/{signal_id}/{algorithm_id}", DeviceType.BTF
                ),
                "signal_id": signal_id,
                "algorithm_id": algorithm_id,
            }
            return copy

    results: List[dict] = []

    recordings: dict = __get_recordings_by_group(
        session, studysite_id, from_date, to_date
    )

    # query each recording to retrieve total number of files to download
    # this will be done again in download file to get a temporary download link
    for recording in recordings:
        recording_details: dict = __get_recording_by_id(
            session, studysite_id, recording["id"]
        )

        template = __metadata_copy(json.dumps(recording_details))

        for signal in recording_details["signals"]:
            results.append(template.get(signal["id"]))

            for algorithm in signal["algorithms"]:
                results.append(template.get(signal["id"], algorithm["id"]))

    return results


def download_file(
    session: requests.Session,
    download_folder: Path,
    studysite_id: str,
    recording_id: str,
    signal_id: str,
    algorithm_id: str = "",
) -> bool:
    """
    Download all files associated with one ByteFlies recording.
    """
    details: dict = __get_recording_by_id(session, studysite_id, recording_id)
    signal: dict = next((s for s in details["signals"] if s["id"] == signal_id), None)
    url, filename = (
        (signal["rawData"], signal_id)
        if not algorithm_id
        else (
            __get_algorithm_uri_by_id(
                session, studysite_id, recording_id, algorithm_id
            ),
            algorithm_id,
        )
    )

    # TODO: for now, assumes that this method never throws ...
    __download_file(download_folder, url, filename)
    return True


def serial_by_device(uuid: str) -> Optional[str]:
    """
    Lookup Device ID by ByteFlies dot.id
    """
    serial = __key_by_value(config.byteflies_devices, uuid)
    return serial


def __key_by_value(filename: Path, needle: str) -> Optional[str]:
    """
    Helper method to find key in CSV by value (needle)
    """
    data = read_csv_from_cache(filename)
    for item in data:
        if needle == item["Serial"]:
            return str(item["Asset Tag"])
    return None


def __get_response(session: requests.Session, url: str) -> Any:
    """
    Wrapper method to execute a GET request. Gives a second
    break to avoid 429 / 502 TooManyRequests (as advised)
    """
    # ByteFlies DEV: when too many requests, it throws 429 or 502
    #    If once per second, should not be a problem
    time.sleep(1)
    try:
        response = session.get(url)
        response.raise_for_status()

        result: dict = response.json()

        log.debug(f"Response from {url} was:\n    {result}")

        return result
    except requests.HTTPError:
        log.error(f"GET Exception to {url} ", exc_info=True)
        return False


def __get_groups(session: requests.Session) -> List[str]:
    """
    Returns the list of groupIds associated with a User Account.
    NOTE: groupIds are hardcoded, so this method is here for posterity
    """
    groups = __get_response(session, f"{config.byteflies_api_url}/groups/")
    group_ids = [g["groupId"] for g in groups]
    return group_ids


def __get_recordings_by_group(
    session: requests.Session, studysite_id: str, begin_date: str, end_date: str
) -> Any:
    """Returns the list of Recordings associated to a Group"""
    return __get_response(
        session,
        f"{config.byteflies_api_url}/groups/{studysite_id}"
        f"/recordings?begin={begin_date}&end={end_date}",
    )


def __get_recording_by_id(
    session: requests.Session, studysite_id: str, recording_id: str
) -> Any:
    """Returns the details of a particular Recording"""
    return __get_response(
        session,
        f"{config.byteflies_api_url}/groups/{studysite_id}/recordings/{recording_id}/",
    )


def __get_algorithm_uri_by_id(
    session: requests.Session, studysite_id: str, recording_id: str, algorithm_id: str
) -> str:
    """Returns the details of a particular Recording"""
    payload = __get_response(
        session,
        f"{config.byteflies_api_url}/groups/{studysite_id}"
        f"/recordings/{recording_id}/algorithms/{algorithm_id}",
    )
    return str(payload["uri"])


def __download_file(download_folder: Path, url: str, filename: str) -> bool:
    """
    Builds the target filename and starts downloading the file to disk
    No session parameter as this queries a non-BTF url with authentication
    embedded in the url
    """
    try:

        path = download_folder / f"{filename}.csv"

        with requests.get(url, stream=True) as response:
            log.debug(f"Headers from {url} was:\n    {response.headers}")

            response.raise_for_status()

            with open(path, "wb") as output_file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        output_file.write(chunk)
        return True
    except Exception:
        log.error("Exception:", exc_info=True)
        return False

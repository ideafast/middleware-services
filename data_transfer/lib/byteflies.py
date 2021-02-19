import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Tuple

import requests

from data_transfer.config import config
from data_transfer.utils import DeviceType, uid_to_hash


@dataclass
class BytefliesFileDownload:
    """Use as CLI arguments for Dreem's library."""

    directory: Path = config.storage_vol
    ftype: str = "csv"


# Define location and filetype to download
args = BytefliesFileDownload()


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


def get_list(session: requests.Session, from_date: str, to_date: str) -> List[dict]:
    """
    GET a list of records (metadata) across study sites, or 'groups' in ByteFlies API
    """

    @dataclass
    class __metadata_copy:
        """Generator for deepcopying a BTF json object"""

        jsondump: str

        def get(self, signal_id: str, algorithm_id: str = "") -> Any:
            copy = json.loads(self.jsondump)
            copy["IDEAFAST"] = {
                "hash": uid_to_hash(
                    f"{copy['id']}/{signal_id}/{algorithm_id}", DeviceType.BTF
                ),
                "signal_id": signal_id,
                "algorithm_id": algorithm_id,
            }
            return copy

    groups = __get_groups(session)
    results: List[dict] = []

    for group in groups:
        recordings: dict = __get_recordings_by_group(session, group, from_date, to_date)

        # query each recording to retrieve total number of files to download
        # this will be done again in download file to get a temporary download link
        for recording in recordings:
            recording_details: dict = __get_recording_by_id(
                session, group, recording["id"]
            )

            template = __metadata_copy(json.dumps(recording_details))

            for signal in recording_details["signals"]:
                results.append(template.get(signal["id"]))

                for algorithm in signal["algorithms"]:
                    results.append(template.get(signal["id"], algorithm["id"]))

    return results


def download_file(
    session: requests.Session, record_id: str, meta: dict
) -> Tuple[bool, Any, List[str]]:
    """
    Download all files associated with one ByteFlies recording.
    Also returns the contents for the -meta.json file, as well as
    a list of the downloaded filenames for packaging in future steps
    """

    # NOTE: Download folder is always /PATIENT_ID/DEVICE_ID
    # WEARTIME are calculated once prepped for upload

    recording_details: dict = __get_recording_by_id(
        session, meta["group_id"], record_id
    )

    download_list: dict = {}  # { record_id : download_url }

    for signal in recording_details["signals"]:
        download_list.update({signal["id"]: signal["rawData"]})

        for algorithm in signal["algorithms"]:
            url = __get_algorithm_uri_by_id(
                session, meta["group_id"], record_id, algorithm["id"]
            )
            download_list.update({algorithm["id"]: url})

    for download_id in download_list:
        __download_file(download_list[download_id], download_id)

    return (True, recording_details, list(download_list.keys()))


def __get_response(session: requests.Session, url: str) -> Any:
    """
    Wrapper method to execute a GET request. Gives a second
    break to avoid 429 / 502 TooManyRequests (as advised)
    """
    response = session.get(url)
    # TODO: manage ByteFlies API requests through other means than time.sleep
    time.sleep(1)
    if code := response.status_code != 200:
        # when too many requests, we expect 429 or 502
        if code != 429 or code != 502:
            # TODO: catch/log exception
            response.raise_for_status()
        else:
            # wait and retry soon-ish
            pass

    return response.json()


def __get_groups(session: requests.Session) -> List[str]:
    """Returns the list of groupIds associated with a User Account"""
    groups = __get_response(session, f"{config.byteflies_api_url}/groups/")
    group_ids = [g["groupId"] for g in groups]
    return group_ids


def __get_recordings_by_group(
    session: requests.Session, group_id: str, begin_date: str, end_date: str
) -> Any:
    """Returns the list of Recordings associated to a Group"""
    return __get_response(
        session,
        f"{config.byteflies_api_url}/groups/{group_id}/recordings?begin={begin_date}&end={end_date}",
    )


def __get_recording_by_id(
    session: requests.Session, group_id: str, recording_id: str
) -> Any:
    """Returns the details of a particular Recording"""
    return __get_response(
        session,
        f"{config.byteflies_api_url}/groups/{group_id}/recordings/{recording_id}/",
    )


def __get_algorithm_uri_by_id(
    session: requests.Session, group_id: str, recording_id: str, algorithm_id: str
) -> str:
    """Returns the details of a particular Recording"""
    payload = __get_response(
        session,
        f"{config.byteflies_api_url}/groups/{group_id}"
        f"/recordings/{recording_id}/algorithms/{algorithm_id}",
    )
    return str(payload["uri"])


def __download_file(url: str, record_id: str) -> None:
    """
    Builds the target filename and starts downloading the file to disk
    """
    file_path = Path(config.storage_vol) / f"{record_id}.{args.ftype}"
    response = requests.get(url, stream=True)

    with open(file_path, "wb") as output_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                output_file.write(chunk)

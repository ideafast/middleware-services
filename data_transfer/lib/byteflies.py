from dataclasses import dataclass
from pathlib import Path
<<<<<<< HEAD
from typing import Any, List, Tuple
=======
from typing import Any, List
>>>>>>> 3453462... byteflies records created per BTF recording

import requests

from data_transfer.config import config


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
    groups = __get_groups(session)
    results: List[dict] = []

    for group in groups:
        recordings: dict = __get_recordings_by_group(session, group, from_date, to_date)
        results.extend(recordings)

    return results


def download_file(
    session: requests.Session, record_id: str, meta: dict
) -> Tuple[bool, Any, List[str]]:
    """
    Download all files associated with one ByteFlies recording.
    Also returns the contents for the -meta.json file, as well as
    a list of the downloaded filenames for packaging in future steps
    """

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
    """Wrapper method to execute a GET request"""
    response = session.get(url)
    # TODO: catch/log exception
    response.raise_for_status()
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


<<<<<<< HEAD
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


=======
>>>>>>> 3453462... byteflies records created per BTF recording
def __download_file(url: str, record_id: str) -> None:
    """
    Builds the target filename and starts downloading the file to disk
    """
<<<<<<< HEAD
    file_path = Path(config.storage_vol) / f"{record_id}.{args.ftype}"
    response = requests.get(url, stream=True)

    with open(file_path, "wb") as output_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                output_file.write(chunk)
=======
    pass
>>>>>>> 3453462... byteflies records created per BTF recording

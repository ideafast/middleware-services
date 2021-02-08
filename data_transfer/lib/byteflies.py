from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional

import requests

from data_transfer.config import config
from data_transfer.utils import read_csv_from_cache


@dataclass
class BytefliesFileDownload:
    """Use as CLI arguments for Dreem's library."""

    directory: Path = config.storage_vol
    # TODO: do we want H5, H5 + EDF, or raw/H5/EDF
    # EDF is a cleaned/reduced H5 file while raw is primarly
    # for internal dreem use.

    #  TODO: adapt for Byteflies
    ftype: str = "h5"


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


def get_list(session: requests.Session) -> List[dict]:
    """
    GET all records (metadata) across study sites ('groups' in ByteFlies API)
    NOTE: undocumented, but we can query with start and end dates. Actually,
    we have to - as the server throws an error when the result is too large (i.e. 4 months)
    """
    today = datetime.today().replace(hour=23, minute=59)
    last_week = today - timedelta(days=8)  # add one day overlap of data if ran weekly
    begin = str(int(last_week.timestamp()))
    end = str(int(today.timestamp()))

    groups = __get_groups(session)
    for group in groups:
        recordings = __get_recordings_by_group(session, group, begin, end)
        print(recordings)
        break  # skip after one group for testing

    return []


def download_file(session: requests.Session, record_id: str) -> bool:
    """
    GET specified file based on known record
    """
    file_type = args.ftype
    url = __build_url(file_type, record_id)

    response = session.get(url)
    # TODO: catch/log exception
    response.raise_for_status()
    result: dict = response.json()

    # Used to lookup the download URL
    key = "url" if file_type == "raw" else "data_url"
    file_url = result[key]

    # NOTE: file_url may be empty if a file is unavailable:
    # (1): file is on dreem headband but not uploaded
    # (2): file is being processed by dreem's algorithms
    if not file_url:
        return False
    # TODO: for now, assumes that this method never throws ...
    __download_file(file_url, record_id)
    return True


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


def __get_response(session: requests.Session, url: str) -> Any:
    """Wrapper method to execute a GET request"""
    response = session.get(url)
    # TODO: catch/log exception
    response.raise_for_status()
    return response.json()


def __get_groups(session: requests.Session) -> List[str]:
    """Returns the list of Groups associated with a User Account"""
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
    """Returns he details of a particular Recording"""
    return __get_response(
        session,
        f"{config.byteflies_api_url}/groups/{group_id}/recordings/{recording_id}/",
    )


def __key_by_value(filename: Path, needle: str) -> Optional[str]:
    """
    Helper method to find key in CSV by value (needle)
    """
    data = read_csv_from_cache(filename)
    for item in data:
        if needle == item["hash"]:
            return str(item["value"])
    return None


def __download_file(url: str, record_id: str) -> None:
    """
    Builds the target filename and starts downloading the file to disk
    """
    # NOTE: can be simplified once we agree on specific file type
    ext = "tar.gz" if args.ftype == "raw" else args.ftype
    file_path = Path(config.storage_vol) / f"{record_id}.{ext}"
    response = requests.get(url, stream=True)

    with open(file_path, "wb") as output_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                output_file.write(chunk)


def __build_url(file_type: str, record_id: str) -> str:
    """
    Build URL based on file info. This varied by filetype, e.g., raw/EDF/H5.
    """
    #  TODO: can be simplified once we determine if we will download only H5 data.
    if file_type == "raw":
        url = f"{config.dreem_api_url}/dreem/dataupload/data/{record_id}"
    else:
        url = f"{config.dreem_api_url}/dreem/algorythm/record/{record_id}/{file_type}/"
    return url

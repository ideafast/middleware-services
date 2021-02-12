import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

import requests

from data_transfer.config import config


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


def get_list(session: requests.Session, from_date: str, to_date: str) -> List[dict]:
    """
    GET all records (metadata) across study sites, or 'groups' in ByteFlies API
    """
    groups = __get_groups(session)
    results: List[dict] = []

    for group in groups:
        recordings = __get_recordings_by_group(session, group, from_date, to_date)
        # each recording requires an API request to detail download links
        # NOTE/TODO: download links are valid for 10 minutes only.
        for recording in recordings:
            recording_details: dict = __get_recording_by_id(
                session, group, recording["id"]
            )

            template = json.loads(json.dumps(recording_details))
            del template["signals"]

            for signal in recording_details["signals"]:

                for algorithm in signal["algorithms"]:
                    record = json.loads(json.dumps(template))
                    record["algorithm"] = algorithm
                    record[
                        "id"
                    ] = f"{record['id']}_signal_{signal['id']}_algorithm_{algorithm['id']}"
                    record["download_url"] = __get_algorithm_by_id(
                        session, group, recording["id"], algorithm["id"]
                    )
                    del record["uri"]
                    results.append(record)

                record = json.loads(json.dumps(template))
                record["signal"] = signal
                record["id"] = f"{record['id']}_signal_{signal['id']}"
                record["download_url"] = signal["rawData"]
                del record["rawData"]
                results.append(record)

    return results


def download_file(session: requests.Session, record_id: str) -> bool:
    """
    GET specified file based on known record
    TODO: retrieve all BTF signals if present.
    """
    return True


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


def __get_algorithm_by_id(
    session: requests.Session, group_id: str, recording_id: str, algorithm_id: str
) -> Any:
    """Returns the details of a particular Recording"""
    return __get_response(
        session,
        f"{config.byteflies_api_url}/groups/{group_id} \
        /recordings/{recording_id}/algorithms/{algorithm_id}",
    )


def __download_file(url: str, record_id: str) -> None:
    """
    Builds the target filename and starts downloading the file to disk
    """
    pass

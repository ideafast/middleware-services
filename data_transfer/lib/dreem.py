# NOTE: this was provided as a CLI library to download
# data from dreem's platform per study-site, but has
# been modified to suit our needs as a library.
# In addition, some methods exist for convience and will be advanced
# for the CVS, e.g. serial_by_device_uuid might to hit a live
# endpoint rather than pull from a CSV file.

import logging as log
from pathlib import Path
from typing import List, Optional, Tuple

import requests

from data_transfer.config import config
from data_transfer.utils import read_csv_from_cache


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
        # attempt to skip this one record
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


def get_restricted_list(session: requests.Session, user_id: str) -> List[dict]:
    """
    GET all records (metadata) associated with a restricted account (e.g. study site)
    """
    url = f"{config.dreem_api_url}/dreem/algorythm/restricted_list/{user_id}/record/"
    results = []

    while url:
        try:
            response = session.get(url)
            response.raise_for_status()
            result: dict = response.json()
            url = result["next"]
            results.extend(result["results"])
        except requests.HTTPError:
            # attempt to skip this one record
            log.error(f"GET Exception to ({url}):", exc_info=True)
            url = result["next"]
    return results


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

        log.debug(result)

        data_url = result.get("data_url", None)
        # NOTE: file_url may be empty if a file is unavailable:
        # (1): file is on dreem headband but not uploaded
        # (2): file is being processed by dreem's algorithms
        if not url:
            return False
        return __download_file(data_url, download_path, record_id)
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
        url: AWS URL to download file
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

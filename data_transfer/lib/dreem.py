# NOTE: this was provided as a CLI library to download
# data from dreem's platform per study-site, but has
# been modified to suit our needs as a library.
# In addition, some methods exist for convience and will be advanced
# for the CVS, e.g. serial_by_device_uuid might to hit a live
# endpoint rather than pull from a CSV file.

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import requests

from data_transfer.config import config
from data_transfer.utils import read_csv_from_cache


@dataclass
class DreemFileDownload:
    """Use as CLI arguments for Dreem's library."""

    directory: Path = config.storage_vol
    # TODO: do we want H5, H5 + EDF, or raw/H5/EDF
    # EDF is a cleaned/reduced H5 file while raw is primarly
    # for internal dreem use.
    ftype: str = "h5"


# Define location and filetype to download
args = DreemFileDownload()


def get_token(creds: dict) -> Tuple[str, str]:
    """
    Generates a JWT token with the credentials for API access
    """
    res = requests.post(f"{config.dreem_login_url}/token/", auth=creds)
    #  TODO: catch/log exception
    res.raise_for_status()
    resp = res.json()
    return (resp["token"], resp["user_id"])


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
        response = session.get(url)
        # TODO: catch/log exception
        response.raise_for_status()
        result: dict = response.json()
        url = result["next"]
        results.extend(result["results"])
    return results


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

# NOTE: some methods exist for convience and will be advanced
# for the CVS, e.g. serial_by_device_uuid might to hit a live 
# endpoint rather than pull from a CSV file.

from data_transfer.config import config
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from functools import lru_cache  # note: @cache exists in py >= 3.9
import csv
import boto3


@dataclass
class VttFileDownload:
    """Use as CLI arguments for Dreem's library."""
    # TODO: how does this relate to VTT?
    directory: Path = config.storage_vol
    # TODO: Check VTT's data file type and format and choose appopriately
    ftype: str = "zip"


# Define location and filetype to download
args = VttFileDownload()

def get_bucket(creds: dict): # TODO: add typing from https://pypi.org/project/mypy-boto3-s3/
    """
    Builds a S3 session bucket object to interface with the S3 bucket
    # NOTE: https://boto3.amazonaws.com/v1/documentation/api/1.9.42/reference/services/s3.html#bucket
    """
    session = boto3.session.Session(
        aws_access_key_id=creds['aws_ak'], 
        aws_secret_access_key=creds['aws_ask'],
    )
    
    s3 = session.resource('s3')
    bucket = s3.Bucket(creds['bucket_name'])    
    
    return bucket


def get_list(bucket) -> [dict]: # TODO: add typing
    """
    GET all records (metadata) from the AWS S3 bucket 
    """
    # using boto3 Resource instead of Client for a readable
    # object oriented approach. Not 100% coverage of AWS API functionality
    
    # returns a list of s3.ObjectSummary() objects containing keys
    # contains metadata, such as .last_modified
    
    # objects = bucket.objects.all()
    # object_paths = [obj.key for obj in summary]
    

    # ignore users.txt files - will deduct from folders
    split_paths = [p.split('/') for p in object_paths if p.find('users.txt') == -1]

    # generally follows [dump_date, raw/files, patienthash, patienthash.file (.nfo or .zip)]
    # transform list to set to list to remove duplicates due to each object having a full path
    patients = dict()
    for path in split_paths:
        if path[2] in patients:
            patients[path[2]].add()
        patients.add(path[2])

    patients = list(set(p[2] for p in split_paths))
    patients = [dict(id=p) for p in patients]
    # dump_dates = set(d[0] for d in split_paths)

    return patients


# def download_file(session: requests.Session, record_id: str) -> bool:
#     """
#     GET specified file based on known record
#     # TODO: adapt for VTT approach
#     """
#     file_type = args.ftype
#     url = __build_url(file_type, record_id)

#     response = session.get(url)
#     # TODO: catch/log exception
#     response.raise_for_status()
#     response = response.json()
    
#     # Used to lookup the download URL
#     key = "url" if file_type == "raw" else "data_url"
#     file_url = response[key]
    
#     # NOTE: file_url may be empty if a file is unavailable:
#     # (1): file is on dreem headband but not uploaded
#     # (2): file is being processed by dreem's algorithms
#     if not file_url:
#         return False
#     # TODO: for now, assumes that this method never throws ...
#     __download_file(file_url, record_id)
#     return True


def serial_by_device(uuid: str) -> Optional[str]:
    """
    Lookup Device ID by dreem headband serial
    # TODO: adapt for VTT approach
    """
    serial = __key_by_value(config.dreem_devices, uuid)
    return serial


def patient_id_by_user(uuid: str) -> Optional[str]:
    """
    Lookup Patient ID by dreem email hash.
    # TODO: adapt for VTT approach
    """
    email = __key_by_value(config.dreem_users, uuid)
    if email:
        # Initially, gmail accounts were used for dreem based on SamsungA40 ID.
        # We want to skip this record and determine PatientID elsewhere.
        if 'gmail' in email:
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
    data = __load_csv(filename)
    for pair in data:
        key, value = pair
        if needle == value:
            return key
    return None


def __download_file(url: str, record_id: str) -> None:
    """
    Builds the target filename and starts downloading the file to disk
    # NOTE: this approach is specific for Dreem
    # TODO: adapt for VTT approach
    """
    # NOTE: can be simplified once we agree on specific file type
    ext = 'tar.gz' if args.ftype == 'raw' else args.ftype
    file_path = Path(config.storage_vol) / f"{record_id}.{ext}"
    response = requests.get(url, stream=True)

    with open(file_path, "wb") as output_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                output_file.write(chunk)


def __build_url(file_type: str, record_id: str) -> (str, str):
    """
    Build URL based on file info. This varied by filetype, e.g., raw/EDF/H5. 
    # TODO: adapt for VTT approach
    """
    # TODO: can be simplified once we determine if we will download only H5 data.
    if file_type == "raw":
        url = f"{config.dreem_api_url}/dreem/dataupload/data/{record_id}"
    else:
        url = f"{config.dreem_api_url}/dreem/algorythm/record/{record_id}/{file_type}/"
    return url
    

@lru_cache(maxsize=None)
def __load_csv(path: Path) -> [tuple]:
    """
    Load full CSV into memory for quick lookup
    """
    with open(path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        data = [(row[0], row[1]) for row in csv_reader]
    return data
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
    
    objects = bucket.objects.all()
    object_paths = [obj.key for obj in objects]

    # ignore users.txt files - will deduct from folders
    split_paths = [p.split('/') for p in object_paths if p.find('users.txt') == -1]

    # generally follows [dump_date, raw/files, patienthash, patienthash.file (.nfo or .zip)]
    patients = list(set([p[2] for p in split_paths]))
    
    result = []
    for patient in patients:
        # TODO: only process dump dates of interest (i.e. since last run)
        result.append(dict(id=patient, dumps=list(set([p[0] for p in split_paths if p[2] == patient]))))
        
    return result


def download_file(bucket, patient_hash: str, dump_date: str,) -> bool:  # TODO: add typing
    """
    GET specified file based on known record
    """
    ext = 'zip' if args.ftype == 'raw' else args.ftype
    file_path = Path(config.storage_vol) / f"{patient_hash}.{ext}"
    download_path = f"{dump_date}/raw/{patient_hash}/{patient_hash}.zip"
    
    bucket.download_file(download_path, str(file_path))
    return True


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
   

@lru_cache(maxsize=None)
def __load_csv(path: Path) -> [tuple]:
    """
    Load full CSV into memory for quick lookup
    """
    with open(path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        data = [(row[0], row[1]) for row in csv_reader]
    return data
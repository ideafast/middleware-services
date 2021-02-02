# NOTE: some methods exist for convience and will be advanced
# for the CVS, e.g. serial_by_device_uuid might to hit a live 
# endpoint rather than pull from a CSV file.

from data_transfer.config import config
from data_transfer.services import dmpy
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from functools import lru_cache  # note: @cache exists in py >= 3.9
import csv

import boto3
from mypy_boto3_s3.service_resource import Bucket


@dataclass
class VttsmaFileDownload:
    """Use as CLI arguments for Dreem's library."""
    # TODO: how does this relate to VTT?
    directory: Path = config.storage_vol
    # TODO: Check VTT's data file type and format and choose appopriately
    ftype: str = "zip"


# Define location and filetype to download
args = VttsmaFileDownload()

def get_bucket(creds: dict) -> Bucket:
    """
    Builds a S3 session bucket object to interface with the S3 bucket
    """
    session = boto3.session.Session(
        aws_access_key_id=creds['aws_ak'], 
        aws_secret_access_key=creds['aws_ask'],
    )
    
    s3 = session.resource('s3')
    bucket = s3.Bucket(creds['bucket_name'])    
    
    return bucket


def get_list(bucket: Bucket) -> [dict]:
    """
    GET all records (metadata) from the AWS S3 bucket 

    NOTE: S3 folder structure is symbolic. The 'key' (str) for each file object \
        represents the path. See also `download_metadata()` in devices > vttsma.py 
    """    
    objects = bucket.objects.all()
    object_paths = [obj.key for obj in objects]

    # ignore users.txt files - data already present in object key
    split_paths = [p.split('/') for p in object_paths if p.find('users.txt') == -1]

    # follows [dump_date, raw/files, patienthash, patienthash.nfo/.zip/.audio?)]
    # remove duplicates via a set()
    patients = list(set([p[2] for p in split_paths]))
    
    result = []
    for patient in patients:
        # TODO: only process dump dates of interest (i.e. since last run)
        result.append(dict(id=patient, dumps=list(set([p[0] for p in split_paths if p[2] == patient]))))
        
    return result


def download_files(bucket: Bucket, patient_hash: str, dump_date: str,) -> bool: 
    """
    GET all files associated with the known record.
    NOTE: S3 folder association is symbolic, so a need to pull down data through a nested loop.
    """
    ext = 'zip' if args.ftype == 'raw' else args.ftype
    folder_path = Path(config.storage_vol) / f"{patient_hash}"
    
    # 'raw' and 'files' are 2nd level top folders
    for prefix in ['raw','files']:
        sub_folder = folder_path/prefix
        sub_folder.mkdir(parents=True, exist_ok=True)
        
        # filter to limit returned results to just this patient
        for obj in bucket.objects.filter(Prefix=f"{dump_date}/{prefix}/{patient_hash}"):
            file_name = obj.key.rsplit('/',1)[1]
            bucket.download_file(obj.key, str(folder_path/prefix/file_name))

    # added method to dmpy service
    dmpy.zip_folder_and_rm_local(folder_path)

    return True
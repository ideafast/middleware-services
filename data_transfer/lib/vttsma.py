from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from mypy_boto3_s3.service_resource import Bucket

from data_transfer.config import config
from data_transfer.services import dmpy
from data_transfer.utils import format_weartime, normalise_day


@dataclass
class VttsmaRecording:
    full_path: str
    vtt_hash: str
    start: datetime
    end: datetime
    filename: str


def get_list(bucket: Bucket) -> List[VttsmaRecording]:
    """
    GET all records (metadata) from the AWS S3 bucket

    NOTE: S3 folder structure is symbolic. The 'key' (str) for each file object \
        represents the path. See also `download_metadata()` in devices > vttsma.py
    """

    def __split_selective(path: str) -> Optional[VttsmaRecording]:
        """
        Returns keys that follow [export_date, raw/files, hash_start_end, raw_files]
        as a dict result
        """
        split = path.split("/")

        # vtt_hash (split[2]) include symbols, and thus cannot be split based on '_'
        if len(split) != 4 or len(split[2]) != 61:
            return None

        return VttsmaRecording(
            path,
            # hash_date example: 43char-hash_YYYYMMDD_YYYYMMDD
            split[2][:-18],
            normalise_day(format_weartime(split[2][-17:-9], "vttsma")),
            normalise_day(format_weartime(split[2][-8:], "vttsma")),
            split[3],
        )

    objects = bucket.objects.all()
    return [d for obj in objects if (d := __split_selective(obj.key)) is not None]


def download_files(
    bucket: Bucket,
    patient_hash: str,
    export_date: str,
) -> bool:
    """
    GET all files associated with the known record.
    NOTE: S3 folder association is symbolic, so a need to pull down data through a nested loop.
    """
    folder_path = Path(config.storage_vol) / f"{patient_hash}"

    # 'raw' and 'files' are 2nd level top folders
    for prefix in ["raw", "files"]:
        sub_folder = folder_path / prefix
        sub_folder.mkdir(parents=True, exist_ok=True)

        # filter to limit returned results to just this patient
        for obj in bucket.objects.filter(
            Prefix=f"{export_date}/{prefix}/{patient_hash}"
        ):
            file_name = obj.key.rsplit("/", 1)[1]
            bucket.download_file(obj.key, str(folder_path / prefix / file_name))

    # added method to dmpy service
    dmpy.zip_folder_and_rm_local(folder_path)

    return True

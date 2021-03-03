import shutil
from pathlib import Path

from dmpy.client import Dmpy
from dmpy.core.payloads import FileUploadPayload

from data_transfer.config import config
from data_transfer.utils import wear_time_in_ms


def zip_folder(path: Path) -> Path:
    return Path(shutil.make_archive(str(path), "zip", path))


def zip_folder_and_rm_local(path: Path) -> Path:
    """Zips folder and removes the original immediately"""
    zip_path = zip_folder(path)
    shutil.rmtree(path)
    return zip_path


def upload(path: Path) -> bool:
    """
    Given a path to a zip folder to be uploaded
    """
    patient_id, device_id, _start, _end = path.stem.split("-")

    checksum = Dmpy.checksum(path)
    start = wear_time_in_ms(_start)
    end = wear_time_in_ms(_end)

    payload = FileUploadPayload(
        config.dmp_study_id, path, patient_id, device_id, start, end, checksum
    )

    is_uploaded = Dmpy().upload(payload)
    return is_uploaded


def rm_local_data(zip_path: Path) -> None:
    zip_path.unlink()
    shutil.rmtree(zip_path.with_suffix(""))

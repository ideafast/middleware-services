import logging
import shutil
from pathlib import Path

from dmpy.client import Dmpy
from dmpy.core.payloads import FileUploadPayload

from data_transfer.config import config
from data_transfer.utils import wear_time_in_ms

log = logging.getLogger(__name__)


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
    log.info(path)
    patient_id, device_id, start, end = path.stem.split("-")

    checksum = Dmpy.checksum(path)
    start_wear = wear_time_in_ms(start)
    end_wear = wear_time_in_ms(end)

    payload = FileUploadPayload(
        path, patient_id, device_id, start_wear, end_wear, checksum
    )

    log.info(payload)
    return Dmpy(config.env_file).upload(payload)


def rm_local_data(zip_path: Path) -> None:
    zip_path.unlink()
    shutil.rmtree(zip_path.with_suffix(""))

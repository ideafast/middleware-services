
from data_transfer.db import read_record, update_record
from data_transfer.devices.vtt import Vtt


def task_download_data(mongoid: str) -> str:
    """
    Download a datafile for the VTT dump device.
    """
    Vtt().download_file(mongoid)
    return mongoid


def task_preprocess_data(mongoid: str) -> str:
    """
    Preprocessing tasks on dreem data.
    """
    record = read_record(mongoid)
    record.is_processed = True
    update_record(record)
    return mongoid
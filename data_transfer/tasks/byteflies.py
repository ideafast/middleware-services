from data_transfer.db import read_record, update_record
from data_transfer.devices.byteflies import Byteflies


def task_download_data(mongoid: str) -> str:
    """
    Download a datafile for a byteflies device.
    """
    Byteflies().download_file(mongoid)
    return mongoid


def task_preprocess_data(mongoid: str) -> str:
    """
    Preprocessing tasks on byteflies data.
    """
    record = read_record(mongoid)
    record.is_processed = True
    print(f"Pre-processed file for:\n   {record}")
    update_record(record)
    return mongoid

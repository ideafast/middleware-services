import logging
from collections import defaultdict
from typing import Dict, List

from bson import ObjectId
from pymongo import MongoClient

from data_transfer.config import config
from data_transfer.schemas.record import Record
from data_transfer.utils import DeviceType

client = MongoClient(config.database_uri)
_db = client.dtransfer

log = logging.getLogger(__name__)


def create_record(record: Record) -> ObjectId:
    result = _db.records.insert_one(record.dict())
    log.debug(f"Record Created:\n  {record}")
    return result.inserted_id


def read_record(mongo_id: str) -> Record:
    result = _db.records.find_one(({"_id": ObjectId(mongo_id)}))
    log.debug(f"Reading record:\n  {result}")
    return Record(**result)


def records_by_dmp_folder(dmp_folder: str) -> List[Record]:
    filters = {"dmp_folder": dmp_folder}
    return __filtered_records(filters)


def update_record(record: Record) -> None:
    _db.records.update_one(
        {"_id": ObjectId(record.id)}, {"$set": record.dict()}, upsert=False
    )


def all_hashes() -> List[str]:
    return [doc["hash"] for doc in _db.records.find()]


def records_not_downloaded(device_type: DeviceType) -> Dict[str, List]:
    filters = {"is_downloaded": False, "device_type": device_type.name}
    records = __filtered_records(filters)
    return __group_by_composite_key(records)


def records_not_uploaded(device_type: DeviceType) -> Dict[str, List]:
    filters = {"is_uploaded": False, "device_type": device_type.name}
    records = __filtered_records(filters)
    return __group_by_composite_key(records)


def records_processed_and_not_uploaded(device_type: DeviceType) -> Dict[str, List]:
    filters = {
        "is_uploaded": False,
        "is_processed": True,
        "is_downloaded": True,
        "device_type": device_type.name,
    }
    records = __filtered_records(filters)
    return __group_by_composite_key(records)


def __filtered_records(filters: dict) -> List[Record]:
    """Returns Records by dict of filters."""
    return [Record(**doc) for doc in _db.records.find(filters)]


def __group_by_composite_key(records: List[Record]) -> Dict[str, List]:
    """Groups records by a pre-determined key. Could be a componsent"""
    results = defaultdict(list)
    # Transform the result to:
    # {PatientID1-DeviceID1: [{Record1}, ... {Record2}], ... }
    for _record in records:
        key = f"{_record.patient_id}/{_record.device_id}"
        results[key].append(_record)
    return results


def min_max_data_wear_times(records: List[Record]) -> tuple:
    """
    Calculate the begin and end date of a folder being prepped for upload
    Returns (start, end) datetimes
    """
    earliest_start = min([doc.start_wear for doc in records])
    latest_end = max([doc.end_wear for doc in records])
    return (earliest_start, latest_end)

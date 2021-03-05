from typing import List

from bson import ObjectId
from pymongo import MongoClient

from data_transfer.config import config
from data_transfer.schemas.record import Record
from data_transfer.utils import DeviceType

client = MongoClient(config.database_uri)
_db = client.dtransfer


def create_record(record: Record) -> ObjectId:
    result = _db.records.insert_one(record.dict())
    return result.inserted_id


def read_record(mongo_id: str) -> Record:
    result = _db.records.find_one(({"_id": ObjectId(mongo_id)}))
    return Record(**result)


def record_by_filename(filename: str) -> Record:
    result = _db.records.find_one(({"filename": filename}))
    return Record(**result)


def update_record(record: Record) -> None:
    _db.records.update_one(
        {"_id": ObjectId(record.id)}, {"$set": record.dict()}, upsert=False
    )


def all_hashes() -> List[str]:
    return [doc["hash"] for doc in _db.records.find()]


def records_not_downloaded(device_type: DeviceType) -> List[Record]:
    docs = _db.records.find({"is_downloaded": False, "device_type": device_type.name})
    return [Record(**doc) for doc in docs]


def records_not_uploaded(device_type: DeviceType) -> List[Record]:
    docs = _db.records.find({"is_uploaded": False, "device_type": device_type.name})
    return [Record(**doc) for doc in docs]


def min_max_data_wear_times(records: List[Record]) -> tuple:
    """
    Calculate the begin and end date of a folder being prepped for upload
    Returns (start, end) datetimes
    """
    earliest_start = min([doc.start_wear for doc in records])
    latest_end = max([doc.end_wear for doc in records])
    return (earliest_start, latest_end)

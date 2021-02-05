from bson import ObjectId
from pymongo import MongoClient
from typing import List

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


def all_filenames() -> List[str]:
    return [doc["filename"] for doc in _db.records.find()]


def records_not_downloaded(device_type: DeviceType) -> List[Record]:
    docs = _db.records.find({"is_downloaded": False, "device_type": device_type.name})
    return [Record(**doc) for doc in docs]

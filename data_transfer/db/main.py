from bson import ObjectId 
from pymongo import MongoClient
from data_transfer.config import config
from data_transfer.schemas.record import Record


client = MongoClient(config.database_uri)
_db = client.dtransfer


def create_record(record: Record) -> ObjectId:
    result = _db.records.insert_one(record.dict())
    return result.inserted_id


def read_record(mongo_id: str) -> Record:
    result = _db.records.find_one(({"_id": ObjectId(mongo_id)}))
    return Record(**result)


def update_record(record: Record) -> Record:
    result = _db.records.update_one(
        {'_id': ObjectId(record.id)}, 
        {"$set": record.dict()}, 
        upsert=False
    )


def all_filenames() -> [str]:
    return [doc['filename'] for doc in _db.records.find()]


def records_not_downloaded() -> [Record]:
    attributes = {"is_downloaded": False}
    return __all_docs_by_attribute(attributes)


def records_not_processed() -> [Record]:
    attributes = {"is_downloaded": True, "is_processed": False}
    return __all_docs_by_attribute(attributes)


def records_not_prepared() -> [Record]:
    attributes = {"is_downloaded": True, "is_processed": True, "is_prepared": False}
    return __all_docs_by_attribute(attributes)


def records_not_uploaded() -> [Record]:
    attributes = {"is_downloaded": True, "is_processed": True, "is_prepared": True, "is_uploaded": False}
    return __all_docs_by_attribute(attributes)


def __all_docs_by_attribute(attributes: dict) -> [Record]:
    docs = _db.records.find(attributes)
    return [Record(**doc) for doc in docs]

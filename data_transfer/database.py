from bson import ObjectId 
from pymongo import MongoClient
from data_transfer.config import config
from data_transfer.schemas.record import Record


client = MongoClient(config.database_uri)
db = client.dtransfer


def create_record(record: Record) -> ObjectId:
    result = db.records.insert_one(record.dict())
    return result.inserted_id


def read_record(mongo_id: str) -> Record:
    result = db.records.find_one(({"_id": ObjectId(mongo_id)}))
    return Record(**result)


def update_record(record: Record) -> Record:
    result = db.records.update_one(
        {'_id': ObjectId(record.id)}, 
        {"$set": record.dict()}, 
        upsert=False
    )


def all_filenames() -> [str]:
    return [doc['filename'] for doc in db.records.find()]


def __all_docs_by_attribute(attribute: str, value: bool = False) -> [Record]:
    docs = db.records.find({attribute: value})
    return [Record(**doc) for doc in docs]


def records_not_downloaded() -> [Record]:
    return __all_docs_by_attribute("is_downloaded")


def records_not_processed() -> [Record]:
    return __all_docs_by_attribute("is_processed")


def records_not_prepared() -> [Record]:
    return __all_docs_by_attribute("is_prepared")


def records_not_uploaded() -> [Record]:
    return __all_docs_by_attribute("is_uploaded")
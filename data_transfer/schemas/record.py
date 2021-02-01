from typing import Optional, Any
from bson import ObjectId 
from pydantic import BaseModel, Field, validator
from datetime import datetime


class Record(BaseModel):
    """
    Stores metadata pipeline information for a raw data file
    """
    id: Optional[Any] = Field(alias='_id')
    filename: str
    device_id: str
    patient_id: str
    start_wear: datetime
    end_wear: datetime

    vttsma_dump_date: Optional[str]

    # Each stage of the pipeline
    is_downloaded: Optional[bool] = False
    is_processed: Optional[bool] = False
    is_prepared: Optional[bool] = False
    is_uploaded: Optional[bool] = False

    @validator("id")
    def validate_id(cls, id):
        """
        Skip validation and cast to ObjectID. 
        Skipping as this is created by DB.
        """
        return ObjectId(id)
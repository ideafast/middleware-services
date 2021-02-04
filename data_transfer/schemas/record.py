from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, validator


class Record(BaseModel):
    """
    Stores metadata pipeline information for a raw data file
    """

    id: Optional[Any] = Field(alias="_id")
    filename: str
    device_type: str
    device_id: str
    patient_id: str
    start_wear: datetime
    end_wear: datetime

    vttsma_export_date: Optional[str]

    # Each stage of the pipeline
    is_downloaded: Optional[bool] = False
    is_processed: Optional[bool] = False
    is_prepared: Optional[bool] = False
    is_uploaded: Optional[bool] = False

    @validator("id")
    def validate_id(self, id):
        """
        Skip validation and cast to ObjectID.
        Skipping as this is created by DB.
        """
        return ObjectId(id)

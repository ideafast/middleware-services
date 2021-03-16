from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, validator


class Record(BaseModel):
    """
    Stores metadata pipeline information for a raw data file
    """

    id: Optional[Any] = Field(alias="_id")

    # used to diff new downloads with history stored in MongoDB
    hash: str
    # e.g. Dreem/Byteflies recording id, or VTT patient folder name
    manufacturer_ref: str
    device_type: str
    device_id: str
    patient_id: str
    start_wear: datetime
    end_wear: datetime
    meta: dict  # meta data relevant to individual device pipelines
    # the DMP upload this record is linked to - known in the last stages
    dmp_folder: Optional[str]

    # Each stage of the pipeline
    is_downloaded: Optional[bool] = False
    is_processed: Optional[bool] = False
    is_prepared: Optional[bool] = False
    is_uploaded: Optional[bool] = False

    @validator("id")
    def validate_id(cls, id: str) -> ObjectId:
        """
        Skip validation and cast to ObjectID.
        Skipping as this is created by DB.
        """
        return ObjectId(id)

    def download_folder(self) -> str:
        """consistenly structure target folder for download"""
        return f"{self.device_type}/{self.patient_id}/{self.device_id}"

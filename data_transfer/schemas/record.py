from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, validator

from data_transfer.config import config


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

    # Relevant to individual device pipelines
    meta: dict = {}

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

    def metadata_path(self) -> Path:
        """Location of metadata for this record."""
        return self.download_folder() / f"{self.manufacturer_ref}-meta.json"

    def download_folder(self) -> Path:
        """Location of data for this record."""
        path = (
            config.storage_vol
            / f"{self.device_type}/{self.patient_id}/{self.device_id}"
        )
        path.mkdir(parents=True, exist_ok=True)
        return path

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
    is_downloaded: bool = False
    is_processed: bool = False
    is_prepared: bool = False
    is_uploaded: bool = False

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

    # ensure validators are run when changing values, not just construction
    class Config:
        validate_assignment = True

    @validator("is_processed")
    def after_downloaded(cls, v: bool, values: dict) -> bool:
        return cls.is_set_true_after(v, values, "is_downloaded")

    @validator("is_prepared", always=True)
    def after_processed(cls, v: bool, values: dict) -> bool:
        return cls.is_set_true_after(v, values, "is_processed")

    @validator("is_uploaded")
    def after_prepared(cls, v: bool, values: dict) -> bool:
        # NOTE: 'is_uploaded' is normally set after upload; somewhat 'too little to late'
        return cls.is_set_true_after(v, values, "is_prepared")

    @staticmethod
    def is_set_true_after(set_value: bool, values: dict, required_true: str) -> bool:
        # values: a dict containing the name-to-value mapping of any previously-validated fields
        # only validate if trying to set to true
        # then, previous step should also be true
        if set_value and not values[required_true]:
            step = required_true.split("_")[1]
            raise ValueError(f"NOT ALLOWED: this Record is not {step} yet.")
        return set_value

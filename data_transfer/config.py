import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseSettings

from data_transfer.utils import StudySite

load_dotenv(".dtransfer.env")


# TODO: would be docker volume
root_path = Path(__file__).parent.parent


class Settings(BaseSettings):
    database_uri: str

    # UCAM
    ucam_data: Path = root_path / "ucam_db.csv"

    # LOCAL
    storage_vol: Path = root_path / "data/input"
    upload_folder: Path = root_path / "data/uploading"

    # IDEAFAST
    inventory_api: str

    support_base_url: str
    support_token: str

    # BYTEFLIES
    byteflies_api_url: str
    byteflies_username: str
    byteflies_password: str
    byteflies_aws_client_id: str
    byteflies_aws_auth_url: str

    # NOTE: Is this the best place to store this?...
    byteflies_group_ids: dict = {
        StudySite.Kiel: "ba92eb10-74d8-11ea-9162-a946985733fd",
        StudySite.Rotterdam: "8c5ed850-b789-11ea-870a-c3400b84381c",
        StudySite.Newcastle: "2f5e6630-4c03-11ea-9f2d-0949ce20b25c",
        StudySite.Muenster: "aa3f7660-ba2a-11ea-bb28-b3fd87020c94",
    }

    byteflies_devices = root_path / "ideafast-byteflies-devices-full.csv"

    # VTTSMA
    vttsma_aws_accesskey: str
    vttsma_aws_secret_accesskey: str
    vttsma_aws_bucket_name: str
    vttsma_global_device_id: str

    # DREEM
    dreem_users: Path = root_path / "ideafast-users-full.csv"
    dreem_devices: Path = root_path / "ideafast-devices-full.csv"

    dreem_login_url: str
    dreem_api_url: str

    # Hardcoded as this data structure is not
    # supported unless JSON is stored in .env
    dreem: dict = {
        "kiel": (os.getenv("DREEM_KIEL_USERNAME"), os.getenv("DREEM_KIEL_PASSWORD")),
        "newcastle": (
            os.getenv("DREEM_NEWCASTLE_USERNAME"),
            os.getenv("DREEM_NEWCASTLE_PASSWORD"),
        ),
        "munster": (
            os.getenv("DREEM_MUNSTER_USERNAME"),
            os.getenv("DREEM_MUNSTER_PASSWORD"),
        ),
        "rotterdam": (
            os.getenv("DREEM_ROTTERDAM_USERNAME"),
            os.getenv("DREEM_ROTTERDAM_PASSWORD"),
        ),
    }


@lru_cache()
def settings() -> Settings:
    return Settings()


config = settings()

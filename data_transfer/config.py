import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv(".dtransfer.env")


# TODO: would be docker volume
root_path = Path(__file__).parent.parent


class Settings(BaseSettings):
    is_local: bool
    database_uri: str

    csvs_path = root_path / "local"
    data_path = root_path / "data"

    dreem_users: Path = csvs_path / "ideafast-users-full.csv"
    dreem_devices: Path = csvs_path / "ideafast-devices-full.csv"

    ucam_data: Path = csvs_path / "ucam_db.csv"

    storage_vol: Path = data_path / "input"
    upload_folder: Path = data_path / "uploading"

    inventory_api: str

    support_base_url: str
    support_token: str

    # NOTE: VTT does not differentiate between study sites
    vttsma_aws_accesskey: str
    vttsma_aws_secret_accesskey: str
    vttsma_aws_bucket_name: str
    vttsma_global_device_id: str

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
    _settings = Settings()
    # TODO: is temporary and should be in a ".dev.env" file?
    if _settings.is_local:
        _settings.inventory_api = "http://0.0.0.0:8000/inventory/"
        _settings.database_uri = "mongodb://localhost:27017/"
    return _settings


config = settings()

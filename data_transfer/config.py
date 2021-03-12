import os
from functools import lru_cache
from pathlib import Path

from dotenv import get_key, load_dotenv
from pydantic import BaseSettings


def get_env_value(key_to_get: str, env_file: str = ".dtransfer.prod.env") -> str:
    return get_key(env_file, key_to_get)


class GlobalConfig(BaseSettings):
    """Global configurations."""

    root_path = Path(__file__).parent.parent

    csvs_path = root_path / "local"
    data_path = root_path / "data"

    storage_vol: Path = data_path / "input"
    upload_folder: Path = data_path / "uploading"

    dreem_users: Path = csvs_path / "ideafast-users-full.csv"
    dreem_devices: Path = csvs_path / "ideafast-devices-full.csv"

    ucam_data: Path = csvs_path / "ucam_db.csv"


class Settings(GlobalConfig):
    is_dev: bool

    database_uri: str
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
        "kiel": (
            get_env_value("DREEM_KIEL_USERNAME"),
            get_env_value("DREEM_KIEL_PASSWORD"),
        ),
        "newcastle": (
            get_env_value("DREEM_NEWCASTLE_USERNAME"),
            get_env_value("DREEM_NEWCASTLE_PASSWORD"),
        ),
        "munster": (
            get_env_value("DREEM_MUNSTER_USERNAME"),
            get_env_value("DREEM_MUNSTER_PASSWORD"),
        ),
        "rotterdam": (
            get_env_value("DREEM_ROTTERDAM_USERNAME"),
            get_env_value("DREEM_ROTTERDAM_PASSWORD"),
        ),
    }


@lru_cache()
def settings() -> Settings:
    # Load production settings as shared with dev.
    load_dotenv(".dtransfer.prod.env")
    # Override specific prod values, e.g., DMP.
    if bool(os.getenv("IS_DEV")):
        load_dotenv(".dtransfer.dev.env", override=True)
    return Settings()


config = settings()

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import get_key, load_dotenv
from pydantic import BaseSettings

from data_transfer.utils import StudySite


def get_env_value(key_to_get: str, env_file: str = ".dtransfer.prod.env") -> str:
    """
    Load from general env then specific file if not found.

    Gets from OS.ENV as may be there when running locally and from envfile when
    running in docker.
    """
    return os.getenv(key_to_get) or get_key(env_file, key_to_get)


class GlobalConfig(BaseSettings):
    """Global configurations."""

    root_path = Path(__file__).parent.parent

    logger_path = root_path / "logging.ini"

    # Stores CSVs for mapping devices to patients.
    # See: local/README.md for more details
    csvs_path = root_path / "local"
    data_path = root_path / "data"

    storage_vol: Path = data_path / "input"
    upload_folder: Path = data_path / "uploading"

    byteflies_historical_start = "2020-07-01"

    dreem_users: Path = csvs_path / "dreem_users.csv"
    dreem_devices: Path = csvs_path / "dreem_devices.csv"

    ucam_data: Path = csvs_path / "ucam_db.csv"

    database_uri: str = "mongodb://user:password@localhost:27017"
    database_name: str = "pipeline_local"

    inventory_api: str = ""
    ucam_api: str = ""
    support_base_url: str = ""
    support_token: str = ""


class Settings(GlobalConfig):
    is_dev: bool

    # DATA MANAGEMENT PORTAL
    dmp_study_id: str
    dmp_url: str
    dmp_public_key: str
    dmp_signature: str

    # BYTEFLIES
    byteflies_api_url: str
    byteflies_username: str
    byteflies_password: str
    byteflies_aws_client_id: str
    byteflies_aws_auth_url: str

    byteflies_group_ids: dict = {
        StudySite.Kiel: "ba92eb10-74d8-11ea-9162-a946985733fd",
        StudySite.Rotterdam: "8c5ed850-b789-11ea-870a-c3400b84381c",
        StudySite.Newcastle: "2f5e6630-4c03-11ea-9f2d-0949ce20b25c",
        StudySite.Muenster: "aa3f7660-ba2a-11ea-bb28-b3fd87020c94",
    }

    # VTTSMA
    vttsma_aws_accesskey: str
    vttsma_aws_secret_accesskey: str
    vttsma_aws_bucket_name: str
    vttsma_global_device_id: str

    # DREEM
    dreem_login_url: str
    dreem_api_url: str

    # Hardcoded as this data structure is not
    # supported unless JSON is stored in .env
    dreem: dict = {
        StudySite.Kiel: (
            get_env_value("DREEM_KIEL_USERNAME"),
            get_env_value("DREEM_KIEL_PASSWORD"),
        ),
        StudySite.Newcastle: (
            get_env_value("DREEM_NEWCASTLE_USERNAME"),
            get_env_value("DREEM_NEWCASTLE_PASSWORD"),
        ),
        StudySite.Muenster: (
            get_env_value("DREEM_MUNSTER_USERNAME"),
            get_env_value("DREEM_MUNSTER_PASSWORD"),
        ),
        StudySite.Rotterdam: (
            get_env_value("DREEM_ROTTERDAM_USERNAME"),
            get_env_value("DREEM_ROTTERDAM_PASSWORD"),
        ),
    }


@lru_cache()
def settings() -> Any:
    """
    Only a few services provide development environments, e.g., DMPY.
    As such, live APIs are used for most local developement and
    specific production values overriden for development.
    """
    # Load production settings as many are shared with dev.
    load_dotenv(".dtransfer.prod.env")

    if get_env_value("IS_DEV"):
        # Override specific prod values, e.g., DMP.
        load_dotenv(".dtransfer.dev.env", override=True)

    if get_env_value("IS_TESTING"):
        return GlobalConfig()

    return Settings()


config = settings()

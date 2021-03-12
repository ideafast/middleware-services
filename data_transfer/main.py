import sys
from logging.config import fileConfig

from data_transfer.config import config
from data_transfer.dags import drm, sma
from data_transfer.utils import DeviceType

fileConfig("logging.ini")

if __name__ == "__main__":
    # Create this once upon setup
    if not config.csvs_path.exists():
        config.csvs_path.mkdir()
    if not config.data_path.exists():
        config.data_path.mkdir()
    if not config.storage_vol.exists():
        config.storage_vol.mkdir()
    if not config.upload_folder.exists():
        config.upload_folder.mkdir()

    device = sys.argv[1] or None
    study_site = sys.argv[2] or None

    if device == DeviceType.DRM.name:
        drm.dag(study_site)
    if device == DeviceType.SMA.name:
        sma.dag()

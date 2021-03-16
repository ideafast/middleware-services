import sys
from logging.config import fileConfig

from data_transfer.config import config
from data_transfer.dags import drm, sma
from data_transfer.utils import DeviceType

fileConfig("logging.ini")

if __name__ == "__main__":
    # Create this once upon setup
    config.csvs_path.mkdir(exist_ok=True)
    config.data_path.mkdir(exist_ok=True)
    config.storage_vol.mkdir(exist_ok=True)
    config.upload_folder.mkdir(exist_ok=True)

    device = sys.argv[1] or None
    study_site = sys.argv[2] or None

    if device == DeviceType.DRM.name:
        drm.dag(study_site)
    if device == DeviceType.SMA.name:
        sma.dag()

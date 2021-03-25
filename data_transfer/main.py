import sys
from logging.config import fileConfig

from data_transfer.config import config
from data_transfer.dags import btf, drm, sma
from data_transfer.utils import DeviceType, StudySite

fileConfig(config.logger_path)

if __name__ == "__main__":
    # Create this once upon setup
    config.csvs_path.mkdir(exist_ok=True)
    config.data_path.mkdir(exist_ok=True)
    config.storage_vol.mkdir(exist_ok=True)
    config.upload_folder.mkdir(exist_ok=True)

    device = DeviceType[sys.argv[1]] or None
    study_site = StudySite[sys.argv[2].capitalize()] or None
    timespan = int(sys.argv[3]) or 2  # default 2 days for testing

    if device == DeviceType.DRM:
        drm.dag(study_site)
    if device == DeviceType.SMA:
        sma.dag()
    if device == DeviceType.BTF:
        btf.dag(study_site, timespan)

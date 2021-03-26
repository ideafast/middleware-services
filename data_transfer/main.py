import sys
from datetime import datetime
from logging.config import fileConfig

from data_transfer.config import config
from data_transfer.dags import btf, drm, sma
from data_transfer.utils import DeviceType, StudySite

fileConfig(config.logger_path)


def historical_btf(study_site: StudySite) -> None:
    """Loops through set periods to retreive all historical data"""
    days_to_cover = (
        datetime.today() - datetime.fromisoformat(config.byteflies_historical_start)
    ).days
    tracker = 0
    while tracker < days_to_cover:
        btf.dag(study_site, 50, tracker)
        # ensure 1 day overlap for sanity
        tracker += 49


if __name__ == "__main__":
    # Create this once upon setup
    config.csvs_path.mkdir(exist_ok=True)
    config.data_path.mkdir(exist_ok=True)
    config.storage_vol.mkdir(exist_ok=True)
    config.upload_folder.mkdir(exist_ok=True)

    device = DeviceType[sys.argv[1]] or None
    study_site = StudySite[sys.argv[2].capitalize()] or None

    if device == DeviceType.DRM:
        drm.dag(study_site)
    if device == DeviceType.SMA:
        sma.dag()
    if device == DeviceType.BTF:
        # if 'days' == -1, trigger full history
        if len(sys.argv) >= 4 and int(sys.argv[3]) == -1:
            historical_btf(study_site)
        else:
            # passes timespan and reference if present
            btf.dag(study_site, *sys.argv[3:])

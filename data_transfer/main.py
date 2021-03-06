import sys
from logging.config import fileConfig

from data_transfer.config import config
from data_transfer.dags import btf, drm, sma, tfa
from data_transfer.utils import DeviceType, StudySite

fileConfig(config.logger_path)


if __name__ == "__main__":
    """
    Usages:
    >   python data_transfer/main.py [DeviceType] [StudySite]
    For BTF, additional args to query a period of data:
    >   python data_transfer/main.py [DeviceType] [StudySite] [days] [reference_day]
    >   [days] == -1 will trigger a historical query to the beginning of the IDEAFAST FS
    """

    # Create this once upon setup
    config.csvs_path.mkdir(exist_ok=True)
    config.data_path.mkdir(exist_ok=True)
    config.storage_vol.mkdir(exist_ok=True)
    config.upload_folder.mkdir(exist_ok=True)

    device = DeviceType[sys.argv[1]]
    study_site = StudySite[sys.argv[2].capitalize()]

    if device == DeviceType.DRM:
        drm.dag(study_site)
    if device == DeviceType.SMA:
        sma.dag()
    if device == DeviceType.TFA:
        tfa.dag(study_site)
    if device == DeviceType.BTF:
        btf_params = [int(x) for x in sys.argv[3:]]

        if len(btf_params) and btf_params[0] == -1:
            btf.historical_dag(study_site, *btf_params)
        else:
            # passes timespan and reference if present
            btf.dag(study_site, *btf_params)

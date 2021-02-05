from data_transfer.devices.dreem import Dreem


def batch_metadata(study_site: str) -> None:
    """
    Dreem's API offers a single request that returns all known data records per study site.

    This method stores the records we have not yet processed.

    NOTE/TODO: this cron batch should be run daily at lunchtime:
        i.e. when most patients have finished sleep.
    """
    dreem = Dreem(study_site)
    dreem.download_metadata()

from data_transfer.devices.byteflies import Byteflies


def batch_metadata(from_date: str, to_date: str) -> None:
    """
    Dreem's API offers a single request that returns all known data records per study site.

    This method stores the records we have not yet processed.

    NOTE/TODO: this cron batch should be run daily at lunchtime:
        i.e. when most patients have finished sleep.
    """
    byteflies = Byteflies()
    byteflies.download_metadata(from_date, to_date)

from data_transfer.devices.byteflies import Byteflies


def batch_metadata(byteflies: Byteflies, from_date: str, to_date: str) -> None:
    """
    This method stores the records we have not yet processed.
    """
    byteflies.download_metadata(from_date, to_date)

from data_transfer.devices.byteflies import Byteflies


def batch_metadata(byteflies: Byteflies, from_date: int, to_date: int) -> None:
    """
    This method stores the records we have not yet processed.
    """
    byteflies.download_metadata(from_date, to_date)

from data_transfer.devices.byteflies import Byteflies
from data_transfer.utils import StudySite


def batch_metadata(from_date: str, to_date: str, study_site: StudySite) -> None:
    """
    This method stores the records we have not yet processed.
    """
    byteflies = Byteflies()
    byteflies.download_metadata(from_date, to_date, study_site)

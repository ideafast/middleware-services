
from data_transfer.devices.vttsma import Vttsma
from data_transfer.schemas.record import Record


def batch_metadata() -> [Record]:
    """
    VTT exports the patient data weekly in an S3 bucket 

    This method stores the records we have not yet processed.

    NOTE/TODO: this cron batch should be run weekly to accomodate the weekly VTT S3 export
    """
    vttsma = Vttsma()
    vttsma.download_metadata()

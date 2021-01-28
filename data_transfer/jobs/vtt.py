
from data_transfer.devices.vtt import Vtt
from data_transfer.schemas.record import Record


def batch_metadata(study_site: str) -> [Record]:
    """
    VTT dumps the patient data weekly in an S3 bucket (Per study site??)

    This method stores the records we have not yet processed.

    NOTE/TODO: this cron batch should be run weekly to accomodate the weekly VTT S3 dump
    """
    vtt = Vtt(study_site)
    vtt.download_metadata()

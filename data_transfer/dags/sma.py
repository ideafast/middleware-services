import logging

from data_transfer.db import all_records_downloaded, records_not_uploaded
from data_transfer.devices.vttsma import Vttsma
from data_transfer.jobs import shared as shared_jobs
from data_transfer.jobs import vttsma as vttsma_jobs
from data_transfer.tasks import vttsma as vttsma_tasks
from data_transfer.utils import DeviceType

log = logging.getLogger(__name__)


def dag() -> None:
    """
    Directed acyclic graph (DAG) representing data_transfer pipeline as used for all devices
    Note that VTT does not distinguish between study sites

    NOTE/TODO: this method simulates the pipeline.
    """
    vttsma = Vttsma()

    vttsma_jobs.batch_metadata(vttsma)

    results = records_not_uploaded(DeviceType.SMA)

    # NOTE: group records by patients per device to process small batches.
    for patient_device, records in results.items():
        for record in records:
            # Each task should be idempotent. Returned values feeds subsequent task
            mongoid = vttsma_tasks.task_download_data(record.id)
            vttsma_tasks.task_preprocess_data(mongoid)

        # Only upload when all records are ready
        if all_records_downloaded(records):
            log.debug(f"All records for {patient_device} DOWNLOADED -> PREPARING ...")
            shared_jobs.prepare_data_folders(DeviceType.SMA)
            log.debug(f"All records for {patient_device} PREPARED   -> UPLOADING ...")
            shared_jobs.batch_upload_data(DeviceType.SMA)
        else:
            log.error(f"Some records for {patient_device} were not downloaded.")

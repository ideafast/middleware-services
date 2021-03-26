import logging
from datetime import datetime
from typing import Union

from data_transfer.db import all_records_downloaded, records_not_uploaded
from data_transfer.devices.byteflies import Byteflies
from data_transfer.jobs import byteflies as byteflies_jobs
from data_transfer.jobs import shared as shared_jobs
from data_transfer.tasks import byteflies as byteflies_tasks
from data_transfer.utils import DeviceType, StudySite, get_period_by_days

log = logging.getLogger(__name__)


def dag(
    study_site: StudySite, days: Union[int, str] = 50, from_today: Union[int, str] = 0
) -> None:
    """
    Directed acyclic graph (DAG) representing dreem data pipeline:

        batch_metadata
            ->task_download_data
            ->task_preprocess_data
            ->task_prepare_data
        ->batch_upload_data

    Parametersi
    ----------
    study_site : StudySite
    days : int, optional
        The amount of days in the past to query data for. This defaults to 50 days
        to ensure prior data which has been delayed in upload is picked up
    from_today : int, optional
        Initial reference (0 == today) to query backwards from. This allows
        traversing back in time for historical data


    NOTE/TODO: this method simulates the pipeline.
    """
    byteflies = Byteflies(study_site)

    data_period = get_period_by_days(int(from_today), int(days))

    log.debug(
        f"Dowloading records from {datetime.fromtimestamp(int(data_period[0]))}"
        f" to {datetime.fromtimestamp(int(data_period[1]))}"
    )

    byteflies_jobs.batch_metadata(byteflies, *data_period)

    results = records_not_uploaded(DeviceType.BTF)

    # NOTE: group records by patients per device to process small batches.
    for patient_device, records in results.items():
        for record in records:
            # Each task should be idempotent. Returned values feeds subsequent task
            mongoid = byteflies_tasks.task_download_data(byteflies, record.id)
            byteflies_tasks.task_preprocess_data(mongoid)

        # Only upload when all records are ready
        if all_records_downloaded(records):
            log.debug(f"All records for {patient_device} DOWNLOADED -> PREPARING ...")
            shared_jobs.prepare_data_folders(DeviceType.BTF)
            log.debug(f"All records for {patient_device} PREPARED   -> UPLOADING ...")
            shared_jobs.batch_upload_data(DeviceType.BTF)
        else:
            log.error(f"Some records for {patient_device} were not downloaded.")

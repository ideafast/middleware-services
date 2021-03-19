from data_transfer.db import records_not_uploaded
from data_transfer.devices.dreem import Dreem
from data_transfer.jobs import dreem as dreem_jobs
from data_transfer.jobs import shared as shared_jobs
from data_transfer.tasks import dreem as dreem_tasks
from data_transfer.utils import DeviceType, StudySite


def dag(study_site: StudySite) -> None:
    """
    Directed acyclic graph (DAG) representing dreem data pipeline:

        batch_metadata
            ->task_download_data
            ->task_preprocess_data
            ->task_prepare_data
        ->batch_upload_data

    NOTE/TODO: this method simulates the pipeline.
    """
    # NOTE: authenticate once as stay-alive time is long
    # TODO: refactor inside Dreem class to keep session alive.
    dreem = Dreem(study_site)

    dreem_jobs.batch_metadata(dreem)

    results = records_not_uploaded(DeviceType.DRM)

    # NOTE: group records by patients per device to process small batches.
    for _, records in results.items():
        for record in records:
            # Each task should be idempotent. Returned values feeds subsequent task
            mongoid = dreem_tasks.task_download_data(dreem, record.id)
            mongoid = dreem_tasks.task_preprocess_data(mongoid)

        shared_jobs.prepare_data_folders(DeviceType.DRM)
        shared_jobs.batch_upload_data(DeviceType.DRM)

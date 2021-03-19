from datetime import datetime

from data_transfer.db import records_not_downloaded
from data_transfer.jobs import byteflies as byteflies_jobs
from data_transfer.jobs import shared as shared_jobs
from data_transfer.tasks import byteflies as byteflies_tasks
from data_transfer.utils import DeviceType, StudySite, get_period_by_days


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

    # TODO: ensure that we get the End of Day as intended based on automation schedule
    # TODO: should we ensure overlap with previous run? How often do we run this DAG?
    # TODO: perhaps pull this one abstraction higher (into the init of this DAG?)
    data_period = get_period_by_days(datetime.today(), 2)  # NOTE: two days for testing
    byteflies_jobs.batch_metadata(*data_period, study_site)

    for record in records_not_downloaded(DeviceType.BTF):
        # Each task should be idempotent. Returned values feeds subsequent task
        mongoid = byteflies_tasks.task_download_data(record.id)
        byteflies_tasks.task_preprocess_data(mongoid)

    # Data is finalised and moved to a folder in /uploading/
    shared_jobs.prepare_data_folders(DeviceType.BTF)
    # All said folders FOR ALL DEVICES are uploaded once per day
    shared_jobs.batch_upload_data(DeviceType.BTF)

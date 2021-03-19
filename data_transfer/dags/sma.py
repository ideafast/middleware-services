from data_transfer.db import records_not_downloaded
from data_transfer.jobs import shared as shared_jobs
from data_transfer.jobs import vttsma as vttsma_jobs
from data_transfer.tasks import shared as shared_tasks
from data_transfer.tasks import vttsma as vttsma_tasks
from data_transfer.utils import DeviceType


def dag() -> None:
    """
    Directed acyclic graph (DAG) representing data_transfer pipeline as used for all devices
    Note that VTT does not distinguish between study sites

    NOTE/TODO: this method simulates the pipeline.
    """
    vttsma_jobs.batch_metadata()

    # NOTE: simulates initiation of tasks upon metadata download
    # TODO: in practice the tasks should be invoked within the batch job.
    for record in records_not_downloaded(DeviceType.SMA):
        # Each task should be idempotent. Returned values feeds subsequent task
        mongoid = vttsma_tasks.task_download_data(record.id)
        _mongoid = vttsma_tasks.task_preprocess_data(mongoid)
        # Data is finalised and moved to a folder in /uploading/
        shared_tasks.task_prepare_data(DeviceType.SMA, _mongoid)

    # All said folders FOR ALL DEVICES are uploaded once per day
    shared_jobs.batch_upload_data()

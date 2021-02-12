from logging.config import fileConfig

from data_transfer.db import records_not_downloaded
from data_transfer.jobs import byteflies as byteflies_jobs
from data_transfer.jobs import dreem as dreem_jobs
from data_transfer.jobs import shared as shared_jobs
from data_transfer.jobs import vttsma as vttsma_jobs
from data_transfer.tasks import byteflies as byteflies_tasks
from data_transfer.tasks import dreem as dreem_tasks
from data_transfer.tasks import shared as shared_tasks
from data_transfer.tasks import vttsma as vttsma_tasks
from data_transfer.utils import DeviceType, get_period_by_days

fileConfig("logging.ini")


def dreem_dag(study_site: str) -> None:
    """
    Directed acyclic graph (DAG) representing dreem data pipeline:

        batch_metadata
            ->task_download_data
            ->task_preprocess_data
            ->task_prepare_data
        ->batch_upload_data

    NOTE/TODO: this method simulates the pipeline.
    """
    dreem_jobs.batch_metadata(study_site)

    # NOTE: simulates initiation of tasks upon metadata download
    # TODO: in practice the tasks should be invoked within the batch job.
    for record in records_not_downloaded(DeviceType.DRM):
        # Each task should be idempotent. Returned values feeds subsequent task
        mongoid = dreem_tasks.task_download_data(study_site, record.id)
        mongoid = dreem_tasks.task_preprocess_data(mongoid)
        # Data is finalised and moved to a folder in /uploading/
        shared_tasks.task_prepare_data(DeviceType.DRM, mongoid)

    # All said folders FOR ALL DEVICES are uploaded once per day
    shared_jobs.batch_upload_data()


def vttsma_dag() -> None:
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
        mongoid = vttsma_tasks.task_preprocess_data(mongoid)
        # Data is finalised and moved to a folder in /uploading/
        shared_tasks.task_prepare_data(DeviceType.SMA, mongoid)

    # All said folders FOR ALL DEVICES are uploaded once per day
    shared_jobs.batch_upload_data()


def byteflies_dag() -> None:
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
    data_period = get_period_by_days(datetime.today(), 3)  # NOTE: one day for testing
    byteflies_jobs.batch_metadata(*data_period)

    for record in records_not_downloaded(DeviceType.BTF):
        # Each task should be idempotent. Returned values feeds subsequent task
        mongoid = byteflies_tasks.task_download_data(record.id)
        mongoid = byteflies_tasks.task_preprocess_data(mongoid)
        # Data is finalised and moved to a folder in /uploading/
        shared_tasks.task_prepare_data(DeviceType.BTF, mongoid)

        break  # NOTE: SKIP AFTER ONE FOR TESTING

    # All said folders FOR ALL DEVICES are uploaded once per day
    shared_jobs.batch_upload_data()


if __name__ == "__main__":
    # dreem_dag("munster")
    # vttsma_dag()
    byteflies_dag()

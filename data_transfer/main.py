from data_transfer.jobs import dreem as dreem_jobs, shared as shared_jobs
from data_transfer.tasks import dreem as dreem_tasks, shared as shared_tasks
from data_transfer.db import records_not_downloaded


def dreem_dag(study_site):
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
    for record in records_not_downloaded():
        # Each task should be idempotent. Returned values feeds subsequent task
        mongoid = dreem_tasks.task_download_data(study_site, record.id)
        mongoid = dreem_tasks.task_preprocess_data(mongoid)
        # Data is finalised and moved to a folder in /uploading/
        shared_tasks.task_prepare_data("DRM", mongoid)
    
    # All said folders FOR ALL DEVICES are uploaded once per day
    # shared_jobs.batch_upload_data()


if __name__ == "__main__":
    dreem_dag("newcastle")
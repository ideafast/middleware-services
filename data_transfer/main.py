from data_transfer.jobs import shared as shared_jobs, \
    dreem as dreem_jobs, \
    vtt as vtt_jobs
from data_transfer.tasks import shared as shared_tasks, \
    dreem as dreem_tasks, \
    vtt as vtt_tasks
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

def vtt_dag():
    """
    Directed acyclic graph (DAG) representing data_transfer pipeline as used for all devices
    Note that VTT does not distinguish between study sites

    NOTE/TODO: this method simulates the pipeline.
    """
    # TODO: adjust for VTT
    vtt_jobs.batch_metadata()

    # NOTE: simulates initiation of tasks upon metadata download
    # TODO: in practice the tasks should be invoked within the batch job.
    # for record in records_not_downloaded():
    #     # Each task should be idempotent. Returned values feeds subsequent task
    #     mongoid = vtt_tasks.task_download_data(study_site, record.id)
    #     mongoid = vtt_tasks.task_preprocess_data(mongoid)
    #     # Data is finalised and moved to a folder in /uploading/
    #     # shared_tasks.task_prepare_data("DRM", mongoid)
    
    # All said folders FOR ALL DEVICES are uploaded once per day
    # shared_jobs.batch_upload_data()

if __name__ == "__main__":
    # dreem_dag("munster")
    vtt_dag()
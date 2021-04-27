import logging

from data_transfer.db import all_records_downloaded, records_not_uploaded
from data_transfer.devices.thinkfast import ThinkFast
from data_transfer.jobs import shared as shared_jobs
from data_transfer.jobs import thinkfast as thinkfast_jobs
from data_transfer.tasks import thinkfast as thinkfast_tasks
from data_transfer.utils import DeviceType, StudySite

log = logging.getLogger(__name__)


def dag(study_site: StudySite) -> None:
    """
    Directed acyclic graph (DAG) representing thinkfast data pipeline:

        batch_metadata
            ->task_download_data
            ->task_preprocess_data
            ->task_prepare_data
        ->batch_upload_data

    NOTE/TODO: this method simulates the pipeline.
    """
    # NOTE: check stay alive time and how often reauthentication is required for thinkfast/camcog

    thinkfast = ThinkFast(study_site)

    # step 1. get all new records
    thinkfast.download_participants_data()
    results = records_not_uploaded(DeviceType.TFA)

    # step 2. preprocess data
    for _patient_device, records in results.items():
        for record in records:
            # Each task should be idempotent. Returned values feeds subsequent task
            thinkfast_tasks.task_preprocess_data(record.id)

        # step 3. prepare data for uploadingData by moving data to a folder in /uploading/
        shared_jobs.prepare_data_folders(DeviceType.TFA)
        # step 4. Upload the data to the dmp
        # shared_jobs.batch_upload_data(DeviceType.TFA)

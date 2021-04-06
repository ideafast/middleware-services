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

    thinkfast.download_participants_data()

    # knock out everything else until I get batch metadata running
    """
    results = records_not_uploaded(DeviceType.TFA) #changed from DRM

    # NOTE: group records by patients per device to process small batches.
    for patient_device, records in results.items():
        for record in records:
            # Each task should be idempotent. Returned values feeds subsequent task
            mongoid = thinkfast_tasks.task_download_data(thinkfast, record.id)
            thinkfast_tasks.task_preprocess_data(mongoid)
        # Only upload when all records are ready
        if all_records_downloaded(records):
            log.debug(f"All records for {patient_device} DOWNLOADED -> PREPARING ...")
            shared_jobs.prepare_data_folders(DeviceType.TFA) #changed from DRM
            log.debug(f"All records for {patient_device} PREPARED   -> UPLOADING ...")
            shared_jobs.batch_upload_data(DeviceType.TFA) #changed from DRM
        else:
            log.error(f"Some records for {patient_device} were not downloaded.")
    """

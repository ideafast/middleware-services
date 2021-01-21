# NOTE: emulating pipeline until task queue is added
# (1)batch_metadata->(2)task_download_data->(3)task_preprocess->(4)prepare_data->(5)batch_upload
# Completion of the metadata batch would initiate the data pipeline.

from data_transfer.config import config
from data_transfer.devices.dreem import Dreem
from data_transfer.db import records_not_downloaded, \
    records_not_processed, records_not_uploaded, records_not_prepared
from data_transfer.services import dmpy
from data_transfer.preprocessing.preparation import prepare_for_upload

from pathlib import Path


# TODO: abstract to batch job. 
dreem_example = Dreem('munster')


def stage_1_batch_metadata():
    # STAGE ONE (BATCH): GET NEW METADATA and store any new records into database
    dreem_example.download_metadata()


def stage_2_task_download_data(mongoid: str) -> str:
    # STAGE TWO (TASK): Download file for each record
    dreem_example.download_file(mongoid)


def stage_3_task_preprocess_data(mongoid: str):
    # STAGE THREE (TASK): PRE-PROCESSING: (1) perform analysis; (2) restructure data
    # TODO: this should call preprocessing library and notify staff/us if errors in data
    # NOTE: the code below is called so next steps can be run. This is not the final logic.
    from data_transfer.db import read_record, update_record
    record = read_record(mongoid)
    record.is_processed = True
    update_record(record)


def stage_4_task_prepare_data(mongoid: str) -> Path:
    # STAGE FOUR (TASK): PRE-PREPARATION
    # AIM: move raw/meta/processed data to one folder by wear period
    destination = prepare_for_upload(mongoid)
    return destination


def stage_5_batch_upload_data(prepared_data_path: Path) -> None:
    # STAGE FIVE (BATCH): DATA UPLOAD (VIA DMP)
    # (1) ZIP FOLDER; (2) UPLOAD; (3) RM LOCAL FOLDER IF SUCCESSFUL
    zip_path = dmpy.zip_folder(prepared_data_path)
    is_uploaded = dmpy.upload(zip_path)

    if is_uploaded:
        # TODO: update DB
        dmpy.rm_local_data(zip_path)


def main():
    pass
    # NOTE: below simulates pipeline for dreem
    # stage_1_batch_metadata()

    # for record in records_not_downloaded():
    #     stage_2_task_download_data(record.id)

    # for record in records_not_processed():
    #     stage_3_task_preprocess_data(record.id)

    # for record in records_not_prepared():
    #     stage_4_task_prepare_data(record.id)

    # for record in records_not_uploaded():
    #     stage_5_batch_upload_data(record.id)


if __name__ == "__main__":
    main()
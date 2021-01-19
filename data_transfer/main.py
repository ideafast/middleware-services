# NOTE: emulating pipeline until task queue is added
# (1)batch_metadata->(2)task_download_data->(3)task_preprocess->(4)prepare_data->(5)batch_upload
# Completion of the metadata batch would initiate the data pipeline.

from data_transfer.config import config
from data_transfer.devices.dreem import Dreem
from data_transfer.database import records_not_downloaded, \
    records_not_processed, records_not_uploaded
from data_transfer.lib import dmpy
from data_transfer.preprocessing.main import prepare_for_upload

from pathlib import Path


# TODO: abstract to batch job. 
dreem_example = Dreem('munster')


def stage_1_batch_metadata():
    # STAGE ONE (BATCH): GET NEW METADATA and store any new records into database
    dreem_example.download_metadata()


def stage_2_task_download_data(mongoid: str) -> str:
    # STAGE TWO (TASK): Download file for each record
    dreem_example.download_file(mongoid)


# TODO: should this be per data file, or per wear period?
def stage_3_task_preprocess_data(mongoid: str):
    # STAGE THREE (TASK): PRE-PROCESSING: (1) perform analysis; (2) restructure data
    # NOTE: this should be done for each raw datafile INDIVIDUALLY (hence taking an ID as param).
    # TODO: this should call preprocessing library and notify staff/us if errors in data
    pass


def stage_4_task_prepare_data(mongoid: str) -> Path:
    # STAGE FOUR (TASK): PRE-PREPARATION
    # AIM: move raw/meta/processed data to one folder by wear period
    prepare_for_upload(mongoid)


def stage_5_batch_upload_data(prepared_data_path: Path) -> None:
    # STAGE FIVE (BATCH): DATA UPLOAD (VIA DMP)
    # (1) ZIP FOLDER; (2) UPLOAD; (3) RM LOCAL FOLDER IF SUCCESSFUL
    path = Path(prepared_data_path)
    zip_path = dmpy.zip_folder(path)
    is_uploaded = dmpy.upload(zip_path)

    if is_uploaded:
        # TODO: update DB
        dmpy.rm_local_data(zip_path)


def main():
    stage_1_batch_metadata()
    
    # NOTE: loops below are used to simulate tasks
    
    # for record in records_not_downloaded():
    #     stage_2_task_download_data(record.id)

    # for _id in records_not_processed():
    #     stage_3_task_preprocess_data(_id)

    # stage_4_task_prepare_data("")

    # for _id in records_not_uploaded():
    #     stage_5_batch_upload_data(_id)


if __name__ == "__main__":
    main()
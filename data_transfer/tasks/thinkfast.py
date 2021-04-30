from data_transfer.db import read_record, update_record


def task_preprocess_data(mongoid: str) -> str:
    """
    Preprocessing tasks on thinkFAST and CANTAB data.
    """
    record = read_record(mongoid)
    if not record.is_processed:
        record.is_processed = True
        update_record(record)
    return mongoid

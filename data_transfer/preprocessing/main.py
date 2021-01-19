from data_transfer.database import records_not_prepared, update_record
from collections import defaultdict
from pathlib import Path


def prepare_for_upload(mongo_id: str):
    """
    Moves all meta/raw/preprocessed data from /input/ into folders in /processing/ format: 
        DEVICEID-PATIENTID-STARTWEAR-ENDWEAR 

    This simplifies zipping and uploading of data.
    """
    
    # A patient may wear multiple devices during one wear period,
    # e.g. if a dreem device had to be replaced as it was broken
    # Convert records_downloaded to the following structure:
    # {
    #     'PATIENT_ID_N': {
    #         'DEVICE_ID_1': [{}, {}]
    #         'DEVICE_ID_N': [{}, {}]
    #     }
    # }
    patients = defaultdict(lambda: defaultdict(list))

    for dic in records_not_prepared():
        patients[dic.patient_id][dic.device_id].append(dic)

    # Move all files for a wear period of un-uploaded records into a single folder
    # NOTE: this might seem redunant since our task queue should upload data nightly
    # but if it fails or if we have historial data then this approach is ideal. 

    # TODO: this would need changed to move data for one record rather than aggregate.
    # e.g. for all not_processed_records for a specific patient, are there any 
    # shared devices? If yes, then group by that (as below) and move to specific folder.

    for patient_id, devices in patients.items():
        for device_id, data in devices.items():

            # NOTE: wear period is the device checkin/checkout
            start_wear = min([i.start_wear for i in data])
            end_wear = max([i.end_wear for i in data])

            # DMP requires no dashes in these IDs
            patient_id = patient_id.replace("-", "")
            device_id = device_id.replace("-", "")

            # Follow DMP naming convention for upload folder: 
            upload_folder = f'{patient_id}-{device_id}-{start_wear}-{end_wear}'

            destination = Path(config.storage_output / upload_folder)
            data_input = Path(config.storage_vol)

            if not destination.exists():
                destination.mkdir()

            for device in data:
                # Move raw/meta/pre-processed data for upload to DMP.
                # TODO lookup filetype based on device type
                for extension in [".h5", "-meta.json"]:
                    # Not all data for each record may be downloaded yet,
                    # e.g. if there was an error downloading it above.
                    if device.is_processed and device.is_downloaded:
                        fname = f'{device.filename}{extension}'
                        old_path = data_input / fname
                        new_path = destination / fname
                        old_path.rename(new_path)
                        device.is_prepared = True
                        update_record(device)
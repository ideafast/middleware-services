# Mapping Devices to Patients

Ensure that you have the required `.csv` files in the `root/local` folder before running the pipeline. This currently includes

- `ucam_db.csv`: a placeholder mapping between device_ids, patient_ids and wear_times until the UCAM API is set up,
- `byteflies_devices.csv`: a placeholder export from the inventory, mapping BTF device serials with device_ids.
- `dreem_users.csv`: a mapping between DRM user emails and their DRM uid.
- `dreem_devices.csv`: a mapping between headband serials and DRM uid.
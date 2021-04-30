# Mapping Devices to Patients

Ensure that you have the required `.csv` files in the `root/local` folder before running the pipeline. This currently includes

- `dreem_users.csv`: a mapping between DRM user emails and their DRM uid.
- `dreem_devices.csv`: a mapping between headband serials and DRM uid.
- `oddities.csv`: a mapping between known aliases and oddities that allow the pipeline to pick up data and patient associations that go beyond the standard mapping of the pipeline.
# Data Transfer Protocols (DTP)

DTP consists of multiple ETL data workflows for a range of sensing devices as part of the IDEA-FAST project. This involves Extracting data from manufacture’s data portals, Transforming (pre-processing) the data to perform data quality  and assurance checks, and Loading data into an external data portal.

## Project Structure

| Path | Info |
| ---- | ---- |
| `/db`      | DB Connection and helper methods |
| `/devices` | Implementation specific for each device |
| `/jobs`    | Batch jobs to run per device or shared |
| `/lib`     | External device libraries |
| `/preprocessing` | Handles data quality, etc |
| `/schemas` | Simplifies interactions with DB |
| `/services`| Interacts with _external_ services |
| `/tasks`   | Tasks to run per device or shared |
| `/utils`   | Helper methods for across DTP |
| `config.py`| Static environmental variables |
| `main.py`  | Entry point to DTP |
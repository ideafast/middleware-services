# Data Transfer Protocols (DTP)

DTP consists of multiple ETL data workflows for a range of sensing devices as part of the IDEA-FAST project. This involves Extracting data from manufacture’s data portals, Transforming (pre-processing) the data to perform data quality  and assurance checks, and Loading data into an external data portal.

## Project Structure

| Path | Info |
| ---- | ---- |
| `/dags`    | Pipelines for each device. |
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

## MongoDB Authentication

Authentication is disabled in mongodb by default, and will need to be setup to access the db remotely. To do that:

1. Remove `command: [--auth]` from the `docker-compose.yml`.
2. Run `docker compose up -d` to see the changes.
3. Enter the docker container: `docker exec -it mongo bash`
4. Run `mongo` from the command line and create two users as follows:

```bash
use admin
db.createUser(
    {
        user: "root",
        pwd: "root",
        roles:["root"]
    }
);

use dtransfer
db.createUser(
    {
        user: "ideafast",
        pwd: "ideafast",
        roles:[
            {
                role: "readWrite",
                db: "dtransfer"
            }
        ]
    }
);
```
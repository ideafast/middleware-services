from pathlib import Path
from unittest.mock import patch

from pymongo.collection import Collection

from data_transfer.db import main as db
from data_transfer.devices import byteflies as devices
from data_transfer.lib import byteflies as lib
from data_transfer.tasks import byteflies as tasks
from data_transfer.utils import DeviceType


def test_get_list(mock_requests_session: dict) -> None:

    result = lib.get_list(
        mock_requests_session["session"], "studysite_1", "begindate", "enddate"
    )

    assert mock_requests_session["get_all"].call_count == 1
    assert mock_requests_session["get_one"].call_count == 4
    assert len(result) == 40


def test_download_file(mock_requests_session: dict, tmpdir: Path) -> None:
    # mock temp storage folder
    lib.config.storage_vol = tmpdir
    target_folder = "test_download_file"
    target_file_name = "random_id_13"
    target_file = tmpdir / target_folder / f"{target_file_name}.csv"

    result = lib.download_file(
        str(target_folder),
        mock_requests_session["session"],
        "studysite_1",
        "random_id_12",
        target_file_name,
        "",
    )

    assert mock_requests_session["get_file"].call_count == 1
    assert Path(target_file).is_file()
    assert result


def test_populated_db(populated_db: Collection) -> None:
    with patch.object(db, "_db", populated_db):

        result = len(db.all_hashes())

        assert result == 40


def test_download_task(
    populated_db: Collection, mock_requests_session: dict, tmpdir: Path
) -> None:
    # TODO: fix this test
    # TODO: overrule 1 second sleep.time in api calls
    # patching
    db._db = populated_db
    devices.byteflies_api.config.storage_vol = tmpdir

    with patch.object(db, "_db", populated_db), patch.object(
        tasks.Byteflies, "authenticate", return_value=mock_requests_session["session"]
    ):

        for record in db.records_not_downloaded(DeviceType.BTF):
            devices.Byteflies().download_file(record.id)
            tasks.task_preprocess_data(record.id)

        result = False

        # to debug, raise to read stdout
        assert result

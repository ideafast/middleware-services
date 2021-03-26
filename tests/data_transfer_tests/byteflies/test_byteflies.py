from pathlib import Path
from unittest.mock import Mock, patch

from pymongo.collection import Collection

from data_transfer.db import main as db
from data_transfer.lib import byteflies as lib


@patch.object(lib.time, "sleep")
def test_get_list(mock_time_sleep: Mock, mock_requests_session: dict) -> None:

    result = lib.get_list(
        mock_requests_session["session"], "studysite_1", "begindate", "enddate"
    )

    assert mock_time_sleep.call_count == 5
    assert mock_requests_session["get_all"].call_count == 1
    assert mock_requests_session["get_one"].call_count == 4
    assert len(result) == 40


def test_download_file(mock_requests_session: dict, tmpdir: Path) -> None:

    # patch storage_folder, and requests, as _download_file() does not use the byteflies session
    with patch.object(lib, "requests", mock_requests_session["session"]), patch.object(
        lib.config, "storage_vol", tmpdir
    ):

        result = lib.download_file(
            mock_requests_session["session"],
            tmpdir,
            "studysite_1",
            "random_id_12",
            "random_id_13",
            "",
        )

    assert result
    assert mock_requests_session["get_one"].call_count == 1
    assert mock_requests_session["get_file"].call_count == 1
    assert Path(tmpdir / "random_id_13.csv").is_file()


def test_populated_db(populated_db: Collection) -> None:
    with patch.object(db, "_db", populated_db):

        result = len(db.all_hashes())

        assert result == 40

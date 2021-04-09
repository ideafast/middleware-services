from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from pymongo.collection import Collection

from data_transfer.dags import btf as dags
from data_transfer.db import main as db
from data_transfer.lib import byteflies as lib


@patch.object(lib.time, "sleep", scope="function")
def test_get_list(mock_time_sleep: Mock, mock_requests_session: dict) -> None:

    with patch.object(lib, "requests", mock_requests_session["session"]):

        result = lib.get_list("studysite_1", 0, 1)

        assert mock_requests_session["get_all"].call_count == 1
        assert mock_requests_session["get_one"].call_count == 4
        assert len(result) == 40


def test_download_file(mock_requests_session: dict, tmpdir: Path) -> None:

    # patch storage_folder, and requests, as _download_file() does not use the byteflies session
    with patch.object(lib, "requests", mock_requests_session["session"]), patch.object(
        lib.config, "storage_vol", tmpdir
    ):

        result = lib.download_file(
            tmpdir, "studysite_1", "random_id_12", "random_id_13", "", 0
        )

    assert result
    assert mock_requests_session["get_one"].call_count == 1
    assert mock_requests_session["get_file"].call_count == 1
    assert Path(tmpdir / "random_id_13.csv").is_file()


def test_recording_by_id(mock_config: MagicMock) -> None:
    # TODO: involve Byteflies()__get_timestamp()
    lib.__get_recording_by_id.cache_clear()
    response = MagicMock()

    timestamps = [0, 0, 0, 1]

    with patch.object(lib, "__get_response", response):
        for time in timestamps:
            lib.__get_recording_by_id("studysite_1", "random_id_12", time)

        result = lib.__get_recording_by_id.cache_info()

        assert result[0] == 2  # two 'hits' on the cache
        assert result[1] == 2  # two 'misses' on the cache
        assert response.call_count == 2  # same as the misses


def test_populated_db(populated_db: Collection) -> None:
    with patch.object(db, "_db", populated_db):

        result = len(db.all_hashes())

        assert result == 40


@patch.object(dags, "records_not_uploaded", return_value={})
@patch.object(dags, "Byteflies")
@patch.object(dags, "StudySite")
@patch.object(dags.byteflies_jobs, "batch_metadata")
def test_historical_dag_coverage(
    mock_batch_metadata: Mock,
    mock_city: Mock,
    mock_Byteflies: Mock,
    mock_not_uploaded: Mock,
) -> None:
    dags.historical_dag(mock_city)
    timespans = [call.args[1:3] for call in mock_batch_metadata.call_args_list]

    result = all(
        [
            ts[0] < timespans[num + 1][1]
            for num, ts in enumerate(timespans)
            if num < len(timespans) - 1
        ]
    )

    assert result

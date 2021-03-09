import re
from pathlib import Path
from typing import IO

import mongomock
import pytest
import requests
import requests_mock
from pymongo.collection import Collection

from data_transfer import utils
from data_transfer.config import config
from data_transfer.devices import byteflies
from data_transfer.schemas.record import Record

folder = Path(__file__).parent


@pytest.fixture
def mock_requests_session() -> dict:
    byteflies_response = utils.read_json(Path(f"{folder}/data/byteflies_payload.json"))
    session = requests.Session()
    adapter = requests_mock.Adapter()

    config.byteflies_api_url = f"mock://{config.byteflies_api_url[len('https://'):]}"
    baseurl = f"{config.byteflies_api_url}/groups/studysite_1/recordings"

    # mocks __get_recordings_by_group
    get_all = adapter.register_uri(
        "GET", baseurl, json=byteflies_response, status_code=200
    )

    # mocks __get_recording_by_id
    def recording_callback(
        request: requests.Request, context: requests_mock.response._Context
    ) -> dict:
        context.status_code = 200
        target = request.url.rstrip("/").split("/")[-1]
        return next((r for r in byteflies_response if r["id"] == target), None)

    recording_matcher = re.compile(f"{baseurl}/random_id_")
    get_one = adapter.register_uri("GET", recording_matcher, json=recording_callback)

    # mocks __download_file
    def download_callback(
        request: requests.Request, context: requests_mock.response._Context
    ) -> IO:
        context.status_code = 200
        return open(Path(f"{folder}/data/mock_btf_file.csv"), "rb")

    download_matcher = re.compile("mock://mock_btf_file")
    get_file = adapter.register_uri(
        "GET", download_matcher, body=download_callback, status_code=200
    )

    # mocks __get_algorithm_uri_by_id
    algo_matcher = re.compile(f"{baseurl}/random_id_(.*)/algorithms/random_id_")
    get_algo = adapter.register_uri(
        "GET", algo_matcher, json={"uri": "mock://mock_btf_file.csv"}, status_code=200
    )

    session.mount("mock://", adapter)
    return {
        "session": session,
        "get_all": get_all,
        "get_one": get_one,
        "get_file": get_file,
        "get_algo": get_algo,
    }


@pytest.fixture
def populated_db() -> Collection:
    db = mongomock.MongoClient().db
    byteflies_itemised = utils.read_json(Path(f"{folder}/data/byteflies_itemised.json"))
    btf_class = byteflies.Byteflies()

    for item in byteflies_itemised:
        recording = btf_class.recording_metadata(item)
        record = Record(
            hash=item["IDEAFAST"]["hash"],
            manufacturer_ref=recording.recording_id,
            device_type=utils.DeviceType.BTF.name,
            device_id=recording.dot_id,
            patient_id=recording.patient_id,
            start_wear=recording.start,
            end_wear=recording.end,
            meta=dict(
                studysite_id=recording.group_id,
                recording_id=recording.recording_id,
                signal_id=recording.signal_id,
                algorithm_id=recording.algorithm_id,
            ),
        )

        db.records.insert_one(record.dict())

    return db

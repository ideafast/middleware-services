import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from data_transfer.config import config
from data_transfer.utils import DeviceType, StudySite, read_json

folder = Path(__file__).parent

study_site_mapping = {
    StudySite.Newcastle: "N",
    StudySite.Kiel: "K",
    StudySite.Muenster: "G",
    StudySite.Rotterdam: "E",
}


class SetEncoder(json.JSONEncoder):
    """Custom encoder to transform set() to list()"""

    def default(self, obj: Any) -> List[Any]:
        if isinstance(obj, set):
            return sorted(list(obj))
        return json.JSONEncoder.default(self, obj)


def write_json(filepath: Path, data: dict) -> None:
    with open(filepath, "w") as f:
        json.dump(data, f, cls=SetEncoder, sort_keys=True, indent=4)


if __name__ == "__main__":
    """
    Compare the upload of WP3 Pipeline to all other users to debug
    and test it's behaviour. Outputs the diff in root/dmp_tools_output/

    $ python contribution_diff.py [devicetype] [studysite]
    $ python contribution_diff.py BTF Kiel  (for example)
    """

    device_type = DeviceType[sys.argv[1]]
    device = device_type.name
    site = StudySite[sys.argv[2].capitalize()]
    study_site = study_site_mapping.get(site)

    we_are = config.dmp_tools_user_name

    us: Dict[str, set] = {}
    them: Dict[str, set] = {}

    dmp_response = read_json(Path(f"{folder}/src/all_records.json"))

    data = dmp_response["data"]["getStudy"]["files"]
    data_set_name = dmp_response["data"]["getStudy"]["name"]

    for item in data:
        d = json.loads(item["description"])

        key = d["participantId"]
        value = d["deviceId"]

        if key[0] != study_site or device not in value:
            continue

        if item["uploadedBy"] == we_are:
            us.setdefault(key, set()).add(value)
        else:
            them.setdefault(key, set()).add(value)

    result_us = {}
    for patient in us:
        if patient in them:
            #  in us but not in them:
            us_not_them = us[patient] - them[patient]
            if len(us_not_them) > 0:
                result_us[patient] = us_not_them
        else:
            result_us[patient] = us[patient]

    result_them = {}
    for patient in them:
        if patient in us:
            #  in them but not in us:
            them_not_us = them[patient] - us[patient]
            if len(them_not_us) > 0:
                result_them[patient] = them_not_us
        else:
            result_them[patient] = them[patient]

    print(f"focussing on studysite {study_site} and device {device}")
    print("\nour account uploaded these sets, where others did not: ")
    print(json.dumps(result_us, cls=SetEncoder, sort_keys=True, indent=4))
    print("\nother uploaded these sets, where we did not: ")
    print(json.dumps(result_them, cls=SetEncoder, sort_keys=True, indent=4))

    output = Path(f"./dmp_tools_output/diff/{device}_{site.name}_{data_set_name}")
    output.mkdir(parents=True, exist_ok=True)

    write_json(output / "us_not_them.json", result_us)
    write_json(output / "them_not_us.json", result_them)

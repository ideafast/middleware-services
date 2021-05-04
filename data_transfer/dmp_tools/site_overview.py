import csv
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any, DefaultDict, List

from data_transfer.utils import DeviceType, StudySite, read_json

folder = Path(__file__).parent

study_site_mapping = {
    StudySite.Newcastle: "N",
    StudySite.Kiel: "K",
    StudySite.Muenster: "G",
    StudySite.Rotterdam: "E",
}

csv_sub_cell = {
    "from": "",
    "to": "",
    "#": 0,
}
ideafast_patient = {d.name: csv_sub_cell.copy() for d in DeviceType}


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

    $ python site_overview.py [studysite]
    $ python contribution_diff.py BTF Kiel  (for example)
    """

    site = StudySite[sys.argv[1].capitalize()]
    study_site = study_site_mapping.get(site)

    result: DefaultDict[str, DefaultDict[str, DefaultDict[str, set]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(set))
    )

    dmp_response = read_json(Path(f"{folder}/src/all_records.json"))

    data = dmp_response["data"]["getStudy"]["files"]
    data_set_name = dmp_response["data"]["getStudy"]["name"]

    for item in data:
        d = json.loads(item["description"])

        key = d["participantId"]

        if key[0] != study_site:
            continue

        value = d["deviceId"]

        # get all days which include data (less granular overview...)
        start = date.fromtimestamp(int(d["startDate"]) / 1000)
        end = date.fromtimestamp(int(d["endDate"]) / 1000)
        delta = end - start

        days_covered = [start + timedelta(days=i) for i in range(delta.days + 1)]
        for day in days_covered:
            result[key][value[:3]][value].add(day.isoformat())

    # print(json.dumps(result,cls=SetEncoder,sort_keys=True, indent=4))

    filtered: dict = defaultdict(lambda: ideafast_patient.copy())
    for patient in result:
        for device_type in result[patient]:
            dates_all = set()
            for device in result[patient][device_type]:
                dates_all.update(result[patient][device_type][device])

            dates = sorted(dates_all)
            filtered[patient][device_type] = {
                "from": dates[0],
                "to": dates[-1],
                "#": len(result[patient][device_type]),
            }

    output = Path(f"./dmp_tools_output/overview/{site.name}_{data_set_name}")
    output.mkdir(parents=True, exist_ok=True)

    # to csv
    csv_file = open(output / f"DMP_overview_{site.name}_{date.today()}.csv", "w")
    csvwriter = csv.writer(csv_file)

    top_header = [""]
    headers = ["patient_id"]
    for key in ideafast_patient.keys():
        top_header.extend(["", key, ""])
        headers.extend(["from", "to", "#"])

    csvwriter.writerow(top_header)
    csvwriter.writerow(headers)
    for patient in filtered:
        row = [patient]
        for device in filtered[patient]:
            row.extend(filtered[patient][device].values())

        csvwriter.writerow(row)

    csv_file.close()

    print(json.dumps(filtered, cls=SetEncoder, sort_keys=True, indent=4))
    write_json(output / f"DMP_overview_{site.name}_{date.today()}.json", filtered)

import json
import os
from pathlib import Path


def json_loader(file_name):
    file = Path(os.path.join(f"./data/{file_name}.json"))

    with open(file) as json_file:
        data = json.loads(json_file.read())
        return data


def get_cost(data, from_town, to_town):
    town_obj = next((x for x in data if x['name'] == from_town))
    town_obj_to = next((x for x in town_obj['costs'] if x['name'] == to_town))

    return float(town_obj_to['cost'])

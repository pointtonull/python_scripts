from random import gauss, randrange, choice
from functools import partial
from datetime import datetime, timedelta
import json

import pandas as pd
import matplotlib.pyplot as plt


def plot_metric(data):
    df_data = pd.DataFrame.from_dict(data["observations"])
    grouped_data = df_data.groupby("name")
    plt.figure()
    for name, group in grouped_data:
        group.plot(x="timestamp", y="value", kind="line", label=name, ax=plt.gca())
    plt.legend()
    plt.show()

def walk(definition, states={}):
    if id(definition) in states:
        value = states[id(definition)]["value"]
    else:
        value = randomize(definition["init"])
        states[id(definition)] = {}
    step = randomize(definition["step"])
    value += step
    if r_min := definition.get("min"):
        value = max(value, r_min)
    if r_max := definition.get("max"):
        value = min(value, r_max)
    states[id(definition)]["value"] = value
    return value


METRICS = [
    {
        "name": "10+1",
        "unit": "°C",
        "value": partial(walk, {"init": 10, "step": 1}),
        "_interval_seconds": partial(gauss, 10, 1),
        "type": "float",
    },
    {
        "name": "R+1",
        "unit": "°C",
        "value": partial(walk, {"init": partial(gauss, 10, 2), "step": 1}),
        "_interval_seconds": partial(gauss, 10, 1),
        "type": "int",
    },
    {
        "name": "1+R",
        "unit": "°C",
        "value": partial(walk, {"step": partial(gauss, 0, 2), "init": 1}),
        "_interval_seconds": partial(gauss, 10, 1),
        "type": "float",
    },
    {
        "name": "R+1+Range",
        "unit": "°C",
        "value": partial(
            walk,
            {
                "init": partial(gauss, 10, 2),
                "step": 1,
                "min": 0,
                "max": 15,
            },
        ),
        "_interval_seconds": partial(gauss, 10, 1),
        "type": "int",
    },
    {
        "name": "R+R+Range",
        "unit": "°C",
        "value": partial(
            walk,
            {
                "init": partial(gauss, 10, 2),
                "step": partial(gauss, 0, 5),
                "min": 5,
                "max": 15,
            },
        ),
        "_interval_seconds": partial(gauss, 10, 1),
        "type": "float",
    },
]


def randomize(definition):
    if callable(definition):
        value = definition()
        return value
    elif isinstance(definition, dict):
        return {
            key: randomize(value)
            for key, value in definition.items()
        }
    elif isinstance(definition, list):
        return [randomize(value) for value in definition]
    else:
        return definition




# Example IRL path
# s3://commercial-lakehouse-tlm-ingress/3s/payload_telemetry/spire/obc/MOCK_SPIRE1/downlink/2024/01/31/1706870434_tlm.json
BASE_PATH = "s3a://commercial-lakehouse-tlm-ingress/3s/payload_telemetry"

# Entropy generator
SEED_WINDOWS_AMOUNT = partial(gauss, 10, 5)
SEED_WINDOW_REL_START = partial(randrange, 0, 59)
SEED_WINDOW_DURATION = partial(gauss, 20, 20)

SEED_OORT_METADATA = {
    "username": partial(choice, ["user_1", "user_2", "user_3", "user_4"]),
    "spire_id": partial(choice, ["testfm_1", "testfm_2", "testfm_3"]),
    "dropbox": partial(choice, ["downlink", "surplus"]),
}


def generate_random_observation(metric, ctime):
    observation = randomize(metric)
    observation["timestamp"] = ctime.timestamp()
    if metric.get("type") == "int":
        observation["value"] = int(observation["value"])
    return observation


def generate_random_data(spire_id, username, window_start, window_end):
    data = {
        "metadata": {
            "spire_id": spire_id,
            "user_id": username,
            "window_id": int(window_start.timestamp() % 7),
        },
        "_schema_version": 1,
        "observations": [],
    }
    # Generate random observations
    observations = data["observations"]
    for metric in METRICS:
        seed_interval_seconds = metric.pop("_interval_seconds", 1)
        # metric["value"] = randomize(metric["value"])
        ctime = window_start + timedelta(seconds=randomize(seed_interval_seconds) / 2)
        while ctime < window_end:
            observation = generate_random_observation(metric, ctime)
            interval_seconds = randomize(seed_interval_seconds)
            ctime += timedelta(seconds=interval_seconds)
        metric = choice(METRICS)
        observation = generate_random_observation(metric, ctime)
        data["observations"].append(observation)
        ctime = observation["timestamp"] + 1
    return data

if __name__ == "__main__":
    # Generate random files
    windows_amount = max(int(randomize(SEED_WINDOWS_AMOUNT)), 0)
    print(f"Generating {windows_amount=}")
    for _ in range(windows_amount):

        print("Generate window details")
        hour_ago = datetime.now() - timedelta(hours=1)
        window_rel_start = randomize(SEED_WINDOW_REL_START)
        window_start = hour_ago + timedelta(minutes=window_rel_start)
        window_duration = timedelta(minutes=randomize(SEED_WINDOW_DURATION))
        window_end = window_start + window_duration
        print(f"{window_start=}")
        print(f"{window_duration=}")

        print("Generate OORT metadata and path")
        oort_metadata = randomize(SEED_OORT_METADATA)
        oort_path = "/".join(oort_metadata.values())
        collection_time = window_start + window_duration
        collection_date_str = collection_time.strftime("%Y-%m-%d")
        file_path = f"{BASE_PATH}/{oort_path}/{collection_date_str}/{int(collection_time.timestamp())}_tlm.json"
        print(f"{file_path=}")

        print("Generate data")
        data = generate_random_data(
            oort_metadata["spire_id"],
            oort_metadata["username"],
            window_start,
            window_end,
        )
        payload = json.dumps(data, indent=4)
        plot_metric(data)

        break
        print("Write the data to the file")
        dbutils.fs.put(file_path, data, overwrite=False)

import json

import requests

with open("config.json") as f:
    config = json.load(f)


def textcomp_stream(prom: str):
    url = config["api_stream"]
    data = {"prompt": prom} | config["params"]
    with requests.post(url, json=data, stream=True) as response:
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                tok = json.loads(line.lstrip("data: "))["token"]
                yield tok


def abort():
    url = config["api_abort"]
    requests.post(url)

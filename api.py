import json

import requests


def completion_stream(prom: str, url: str, params: dict[str, str]):
    data = {"prompt": prom} | params
    with requests.post(url, json=data, stream=True) as response:
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                tok = json.loads(line.lstrip("data: "))["token"]
                yield tok


def abort(url):
    requests.post(url)

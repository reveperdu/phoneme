from __future__ import annotations
import json
from typing import TYPE_CHECKING


import requests

if TYPE_CHECKING:
    from window import State


def completion_stream_kcpp(prom: str, url: str, params: dict[str, str]):
    data = {"prompt": prom} | params
    with requests.post(url, json=data, stream=True) as response:
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                tok = json.loads(line.lstrip("data: "))["token"]
                yield tok


def completion_stream_lcpp(prom: str, url: str, params: dict[str, str], state: State|None=None):
    data = {"prompt": prom} | params | {"stream": True}
    with requests.post(url, json=data, stream=True) as response:
        response.encoding = "utf-8"
        for line in response.iter_lines(decode_unicode=True):
            if (state is not None) and (state.should_abort):
                state.should_abort = False
                response.close()
                break
            if line.startswith("data: "):
                tok = json.loads(line.lstrip("data: "))["content"]
                yield tok


def abort_api(url):
    requests.post(url)

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from window import State

DISCARD_REASONING = True


def completion_stream_kcpp(prom: str, url: str, params: dict[str, str]):
    data = {"prompt": prom} | params
    with requests.post(url, json=data, stream=True) as response:
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                tok = json.loads(line.removeprefix("data: "))["token"]
                yield tok


def completion_stream(
    type: str,
    context,
    url_stream: str,
    params: dict[str, str],
    state: State,
    mmdata: list[str] | None = None,
    url_abort: str = "",
):
    data = {}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if type == "lcpp_stream":
        if mmdata is not None:
            data["prompt"] = {"prompt_string": context, "multimodal_data": mmdata}
        else:
            data["prompt"] = context
    elif type == "oaicompat_stream":
        if "OAICOMPAT_APIKEY" in os.environ:
            apikey = os.environ["OAICOMPAT_APIKEY"]
        else:
            #echoed to avoid typo in the long hex-string of apikey
            print("no apikey specified in envvar, please input ")
            apikey = input("apikey: ")
            os.environ["OAICOMPAT_APIKEY"] = apikey
        headers["Authorization"] = "Bearer " + apikey
        data["messages"] = context
    data = data | params | {"stream": True}
    with requests.post(url_stream, json=data, stream=True, headers=headers) as response:
        response.encoding = "utf-8"
        for line in response.iter_lines(decode_unicode=True):
            if state.should_abort:
                state.should_abort = False
                if url_abort == "":
                    response.close()
                else:
                    requests.post(url_stream)
                break
            if line == "data: [DONE]":
                return
            if line.startswith("data: "):
                sse = json.loads(line.removeprefix("data: "))
                if type == "lcpp_stream":
                    tok = sse["content"]
                elif type == "oaicompat_stream":
                    # actually dpsk
                    delta = sse["choices"][0]["delta"]
                    if sse["choices"][0]["delta"]["content"] is not None:
                        tok = delta["content"]
                    elif "reasoning_content" in delta:
                        if DISCARD_REASONING:
                            tok = ""
                        else:
                            tok = delta["reasoning_content"]
                    else:
                        return
                yield tok

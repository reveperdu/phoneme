from __future__ import annotations

import json
import os

import requests

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
    should_abort: bool,
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
        apikey = os.environ["OAICOMPAT_APIKEY"]
        headers["Authorization"] = "Bearer " + apikey
        data["messages"] = context
    data = data | params | {"stream": True}
    with requests.post(url_stream, json=data, stream=True, headers=headers) as response:
        response.encoding = "utf-8"
        for line in response.iter_lines(decode_unicode=True):
            if should_abort:
                should_abort = False
                if url_abort == "":
                    response.close()
                else:
                    requests.post(url_stream)
                break
            print(line)  # debug
            if line.startswith("data: "):
                sse = json.loads(line.removeprefix("data: "))
                if type == "lcpp_stream":
                    tok = sse["content"]
                elif type == "oaicompat_stream":
                    # actually dpsk
                    delta = sse["choices"][0]["delta"]
                    if line == "data: [DONE]":
                        return
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

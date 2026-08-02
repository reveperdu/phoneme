from __future__ import annotations

from typing import TYPE_CHECKING

import api

if TYPE_CHECKING:
    from window import State


def kcpp2oaicompat(context: str) -> list[dict[str, str]]:
    # convert kcpp format to openai-compatible completion format
    context_lines = context.splitlines()
    role = "system"
    next_role = ""
    content = ""
    result = []
    new_round = False
    for line in context_lines:
        if line == "{{[SYSTEM]}}":
            # ignore system tag because it might not be present,
            # instead treat anything before first input/output as system
            pass
        elif line == "{{[INPUT]}}":
            new_round = True
            next_role = "user"
        elif line == "{{[OUTPUT]}}":
            new_round = True
            next_role = "assistant"
        else:
            content = content + line + "\n"
        if new_round:
            # remove trailing newline from textual chat but not needed for oaicompat
            content = content.removesuffix("\n")
            result.append({"role": role, "content": content})
            content = ""
            role = next_role
            new_round = False
    return result


def sendto_api_generic(context, config, state: State):
    api_params = {
        "type": config["api_type"],
        "url_stream": config["url_stream"],
        "url_abort": config["url_abort"],
        "params": config["params"],
        "should_abort": state.should_abort,
    }
    if config["api_type"] == "lcpp_stream":
        d = config["chat_template"]
        prom = context
        if config["no_think"]:
            s1, s2, s3 = prom.rpartition("\n{{[OUTPUT]}}\n")
            prom = s1 + s2 + config["nothink_tag"] + s3
        for k in d:
            prom = prom.replace(k, d[k])
        api_params["context"] = prom
        if len(state.images) > 0:
            api_params["mmdata"] = state.images
    elif config["api_type"] == "oaicompat_stream":
        msg = kcpp2oaicompat(context)
        api_params["context"] = msg
    else:
        raise RuntimeError("api type unspecified or currently unsupported")
    # current only covered streaming apis
    state.is_stream = True
    state.current_stream = api.completion_stream(**api_params)

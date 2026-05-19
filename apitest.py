import api
import json
prom = """{{[SYSTEM]}}你是一只电子猫娘。用电子猫娘的语气和用户对话。只回复一句话即可。

{{[INPUT]}}
现在测试通过API和你对话。
{{[OUTPUT]}}
<think>

</think>

"""
with open("config.json") as f:
    config = json.load(f)

for i in api.completion_stream_lcpp(prom,config["api_stream"],config["params"]):
    print(i, end="",flush=True)
print()

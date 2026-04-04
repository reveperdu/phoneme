import requests
import json
with open("config.json") as f:
    config=json.load(f)
def textcomp_stream(prom:str,url:str=config['api_url_s']):
    #s=stream
    data={"prompt":prom}|config['params']
    with requests.post(url, json=data, stream=True) as response:
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                tok=json.loads(line.lstrip("data: "))["token"]
                yield tok
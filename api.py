import requests
import json
with open("config.json") as f:
    config=json.load(f)
def dict_replace(s:str,d:dict):
    for k in d:
        s=s.replace(k,d[k])
    return s
def textcomp_stream(context:str,url:str=config['api_url_s']):
    #s=stream
    prom=dict_replace(context,config["chat_template"])
    data={"prompt":prom}|config['params']
    with requests.post(url, json=data, stream=True) as response:
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                tok=json.loads(line.lstrip("data: "))["token"]
                yield tok
def handle_stream():
    #append text to gui
    pass
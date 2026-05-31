import subprocess


def dict_replace(s: str, d: dict):
    for k in d:
        s = s.replace(k, d[k])
    return s
def make_subsdict(config):
    d={}
    t=config["chat_template"]
    d["{{[OUTPUT]}}"]=t["end"]+t["output"]
    d["{{[INPUT]}}"]=t["end"]+t["input"]
    d["{{[SYSTEM]}}"]=t["system"]
    return d
def tool_call_generic(call):
    print(call)
    user_input=input("run this command?(y/n)")
    if user_input!="y":
        return "denied by user."
    subp=subprocess.run(call, shell=True, capture_output=True, text=True)
    result=subp.stdout
    return result
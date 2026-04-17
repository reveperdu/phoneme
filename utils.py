def dict_replace(s: str, d: dict):
    for k in d:
        s = s.replace(k, d[k])
    return s

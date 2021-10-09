import json


def get_string_json(s, index):
    value = []
    s = s.replace("\'", "\"")
    s = s.replace('\0', '')
    try:
        for j in json.loads(s):
            value.append(j[index])
    except json.decoder.JSONDecodeError:
        pass
    return value

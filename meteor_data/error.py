# -*- coding: utf-8 -*-
import json


def gen_http_status(content: dict):
    print(content)
    with open("http_status.json", "w", encoding="utf-8") as fp:
        fp.write(json.dumps(content, ensure_ascii=False))
    raise Exception(content["msg"])

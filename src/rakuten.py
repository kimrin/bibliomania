import requests
from pprint import pprint
import regex
import json


def encode_rakuten(strings):
    return requests.utils.quote(strings.encode('utf-8'))


def rakuten(url="https://app.rakuten.co.jp/services/api/BooksTotal/Search/20170404?", args={}):
    arglist = []
    for k, v in args.items():
        arglist.append(f"{k}={encode_rakuten(v)}")

    r = requests.get(url + "&".join(arglist))
    js = r.json()
    # pprint(js)
    return js


def rakuten_foreign(url="https://app.rakuten.co.jp/services/api/BooksForeignBook/Search/20170404?", args={}):
    arglist = []
    for k, v in args.items():
        arglist.append(f"{k}={encode_rakuten(v)}")

    r = requests.get(url + "&".join(arglist))
    js = r.json()
    pprint(js)
    return js

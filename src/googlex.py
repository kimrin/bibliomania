import requests


def google_books(url="https://www.googleapis.com/books/v1/volumes?", args={}):
    arglist = []
    for k, v in args.items():
        arglist.append(f"{k}={requests.utils.quote(v.encode('utf-8'))}")

    r = requests.get(url + "&".join(arglist))
    js = r.json()
    # pprint(js)
    return js

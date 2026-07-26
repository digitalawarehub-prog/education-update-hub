import requests


def check_source(source):

    try:

        r = requests.get(

            source["url"],

            timeout=10

        )

        return r.status_code == 200

    except Exception:

        return False

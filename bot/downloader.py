import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.constants import (
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    USER_AGENT
)

from utils.logger import logger

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


def create_session():

    retry = Retry(
        total=MAX_RETRIES,
        connect=MAX_RETRIES,
        read=MAX_RETRIES,
        backoff_factor=2,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504
        ]
    )

    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()

    session.headers.update({

        "User-Agent": USER_AGENT,

        "Accept-Language": "en-IN,en;q=0.9"

    })

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


SESSION = create_session()


def download(url):

    try:

        response = SESSION.get(

            url,

            timeout=REQUEST_TIMEOUT,

            allow_redirects=True,

            verify=False

        )

        response.raise_for_status()

        return response.text

    except Exception as e:

        logger.error(f"Download Failed : {url}")

        logger.error(e)

        return None

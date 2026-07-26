import time


def retry(func, retries=3):

    for attempt in range(retries):

        try:

            return func()

        except Exception:

            time.sleep(2)

    return None

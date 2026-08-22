import re

def normalize(text):

    if not text:

        return ""

    text = re.sub(r"\s+", " ", str(text))

    return text.strip()

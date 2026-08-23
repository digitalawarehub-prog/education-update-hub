# Education Update Hub - production source configuration
SITE_NAME = "Education Update Hub"
SITE_URL = "https://educationupdatehub.in"
AUTHOR = "Education Update Hub"
DEFAULT_IMAGE = "https://educationupdatehub.in/images/default-job.jpg"

ADSENSE_ID = "ca-pub-4508009805424675"
GA4_ID = "G-XRESX2YP1"
ADSENSE_CLIENT = ADSENSE_ID
GA_MEASUREMENT_ID = GA4_ID
TWITTER_CARD = "summary_large_image"

WHATSAPP_CHANNEL = "https://whatsapp.com/channel/0029Vb8LjDk6hENiaVSP4Q2a"
TELEGRAM_CHANNEL = "https://t.me/YOUR_CHANNEL"

# Complete official source library. bot/sources.json is the single source of truth.
from pathlib import Path
import json
_SOURCE_FILE = Path(__file__).resolve().parent / "sources.json"
_FALLBACK_SOURCES = [
    {"id":"ssc","name":"SSC","url":"https://ssc.gov.in/","type":"html","adapter":"ssc","enabled":True},
    {"id":"upsc","name":"UPSC","url":"https://www.upsc.gov.in/recruitment","type":"html","adapter":"upsc","enabled":True},
    {"id":"ibps","name":"IBPS","url":"https://www.ibps.in/","type":"html","adapter":"ibps","enabled":True},
    {"id":"ukpsc","name":"UKPSC","url":"https://psc.uk.gov.in/candidate-corner/recruitment","type":"html","adapter":"uk","enabled":True},
    {"id":"uksssc","name":"UKSSSC","url":"https://sssc.uk.gov.in/recruitment-notification/","type":"html","adapter":"uk","enabled":True},
    {"id":"railway","name":"Railway","url":"https://www.rrbcdg.gov.in/","type":"html","adapter":"railway","enabled":True},
]
def _load_sources():
    try:
        data=json.loads(_SOURCE_FILE.read_text(encoding="utf-8"))
        if isinstance(data,list) and data:
            clean=[]
            for item in data:
                if isinstance(item,dict) and item.get("url") and item.get("name"):
                    item=dict(item); item.setdefault("type","html"); item.setdefault("adapter","generic"); item.setdefault("enabled",True); clean.append(item)
            if clean: return clean
    except Exception: pass
    return _FALLBACK_SOURCES
SOURCES = _load_sources()

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

# Legacy fallback only. Canonical source library is bot/sources.json and is loaded by SourceManager.
SOURCES = [
    {"name":"SSC", "url":"https://ssc.gov.in/", "type":"html", "adapter":"ssc", "enabled":True},
    {"name":"UPSC", "url":"https://www.upsc.gov.in/recruitment", "type":"html", "adapter":"upsc", "enabled":True},
    {"name":"IBPS", "url":"https://www.ibps.in/", "type":"html", "adapter":"ibps", "enabled":True},
    {"name":"UKPSC", "url":"https://psc.uk.gov.in/candidate-corner/recruitment", "type":"html", "adapter":"uk", "enabled":True},
    {"name":"UKSSSC", "url":"https://sssc.uk.gov.in/recruitment-notification/", "type":"html", "adapter":"uk", "enabled":True},
    {"name":"Railway", "url":"https://www.rrbcdg.gov.in/", "type":"html", "adapter":"railway", "enabled":True},
    {"name":"PSC", "url":"https://psc.uk.gov.in/", "type":"html", "adapter":"psc", "enabled":True},
]

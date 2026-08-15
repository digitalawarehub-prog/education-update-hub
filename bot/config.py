# ==========================================
# Website
# ==========================================

SITE_NAME = "Education Update Hub"
SITE_URL = "https://educationupdatehub.in"
AUTHOR = "Education Update Hub"
DEFAULT_IMAGE = "https://educationupdatehub.in/images/default-job.jpg"

# ==========================================
# Google
# ==========================================

ADSENSE_ID = "ca-pub-4508009805424675"
GA4_ID = "G-XRESX2YP1N"
ADSENSE_CLIENT = ADSENSE_ID
GA_MEASUREMENT_ID = GA4_ID
TWITTER_CARD = "summary_large_image"

# ==========================================
# Social
# ==========================================

WHATSAPP_CHANNEL = "https://whatsapp.com/channel/0029Vb8LjDk6hENiaVSP4Q2a"
TELEGRAM_CHANNEL = "https://t.me/YOUR_CHANNEL"

# ==========================================
# Production Sources
# ==========================================
# adapter = exact adapter used by scraper.py -> adapters.get_adapter()
# enabled = source participates in every automation run.
#
# IMPORTANT:
# - Railway and PSC are now ACTIVE.
# - UKPSC/UKSSSC use the dedicated UK adapter.
# - The PSC adapter itself checks the configured PSC commission sites.
# - URLs are source entry points; adapters may use their own recruitment URLs.

SOURCES = [
    {
        "name": "SSC",
        "url": "https://ssc.gov.in/",
        "type": "html",
        "adapter": "ssc",
        "enabled": True,
    },
    {
        "name": "UPSC",
        "url": "https://upsc.gov.in/",
        "type": "html",
        "adapter": "upsc",
        "enabled": True,
    },
    {
        "name": "IBPS",
        "url": "https://www.ibps.in/",
        "type": "html",
        "adapter": "ibps",
        "enabled": True,
    },
    {
        "name": "UKPSC",
        "url": "https://psc.uk.gov.in/recruitment",
        "type": "html",
        "adapter": "uk",
        "enabled": True,
    },
    {
        "name": "UKSSSC",
        "url": "https://sssc.uk.gov.in/recruitment-notification/",
        "type": "html",
        "adapter": "uk",
        "enabled": True,
    },
    {
        "name": "Railway",
        "url": "https://www.rrbcdg.gov.in/",
        "type": "html",
        "adapter": "railway",
        "enabled": True,
    },
    {
        "name": "PSC",
        "url": "https://psc.uk.gov.in/",
        "type": "html",
        "adapter": "psc",
        "enabled": True,
    },
]

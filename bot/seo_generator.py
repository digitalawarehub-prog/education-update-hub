from datetime import datetime
from html import escape

from config import *


def slugify(text):
    text = text.lower()
    text = text.replace("&", " and ")
    text = text.replace("/", "-")
    text = text.replace(" ", "-")

    while "--" in text:
        text = text.replace("--", "-")

    return text.strip("-")


def generate_seo(job):

    title = escape(job.get("title", "Government Job"))

    description = escape(
        job.get(
            "summary",
            f"{title} - Latest Government Recruitment, Eligibility, Salary, Vacancy, Important Dates and Apply Online."
        )
    )

    slug = slugify(title)

    url = job.get(
        "post_url",
        f"{SITE_URL}/generated/{slug}.html"
    )

    image = job.get(
        "image",
        DEFAULT_IMAGE
    )

    today = datetime.now().strftime("%Y-%m-%d")

    seo = f"""
<title>{title} | {SITE_NAME}</title>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1">

<meta name="description"
content="{description}">

<meta name="robots"
content="index,follow,max-image-preview:large">

<meta name="author"
content="{AUTHOR}">

<meta name="theme-color"
content="#0B57D0">

<link rel="canonical"
href="{url}">

<!-- Open Graph -->

<meta property="og:type"
content="article">

<meta property="og:title"
content="{title}">

<meta property="og:description"
content="{description}">

<meta property="og:url"
content="{url}">

<meta property="og:image"
content="{image}">

<meta property="og:site_name"
content="{SITE_NAME}">

<meta property="og:locale"
content="en_IN">

<!-- Twitter -->

<meta name="twitter:card"
content="{TWITTER_CARD}">

<meta name="twitter:title"
content="{title}">

<meta name="twitter:description"
content="{description}">

<meta name="twitter:image"
content="{image}">

<!-- Adsense -->

<meta name="google-adsense-account"
content="{ADSENSE_ID}">

<script async
src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_ID}"
crossorigin="anonymous"></script>

<!-- Google Analytics -->

<script async
src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}">
</script>

<script>

window.dataLayer = window.dataLayer || [];

function gtag(){{dataLayer.push(arguments);}};

gtag('js', new Date());

gtag('config', '{GA4_ID}');

</script>

<!-- JobPosting Schema -->

<script type="application/ld+json">

{{
"@context":"https://schema.org",

"@type":"JobPosting",

"title":"{title}",

"description":"{description}",

"datePosted":"{today}",

"validThrough":"{job.get('last_date', today)}",

"employmentType":"FULL_TIME",

"hiringOrganization":{{

"@type":"Organization",

"name":"{SITE_NAME}"

}},

"identifier":{{

"@type":"PropertyValue",

"name":"{SITE_NAME}",

"value":"{slug}"

}},

"applicantLocationRequirements":{{

"@type":"Country",

"name":"India"

}},

"url":"{url}"

}}

</script>
"""

    return seo

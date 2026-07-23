from settings import *

from datetime import datetime


def generate_seo(job):

    title = job["title"]

    description = f"{title} - Latest Notification, Eligibility, Vacancy, Salary, Apply Online, Important Dates."

    slug = (
        title.lower()
        .replace(" ", "-")
        .replace("/", "-")
    )

    url = f"{SITE_URL}/generated/{slug}.html"

    seo = f"""
<title>{title} | {SITE_NAME}</title>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1">

<meta name="description"
content="{description}">

<meta name="robots"
content="index,follow">

<meta name="author"
content="{AUTHOR}">

<link rel="canonical"
href="{url}">

<meta property="og:type"
content="article">

<meta property="og:title"
content="{title}">

<meta property="og:description"
content="{description}">

<meta property="og:url"
content="{url}">

<meta property="og:image"
content="{DEFAULT_IMAGE}">

<meta property="og:site_name"
content="{SITE_NAME}">

<meta name="twitter:card"
content="{TWITTER_CARD}">

<meta name="twitter:title"
content="{title}">

<meta name="twitter:description"
content="{description}">

<meta name="twitter:image"
content="{DEFAULT_IMAGE}">

<meta name="google-adsense-account"
content="{ADSENSE_ID}">

<script async
src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_ID}"
crossorigin="anonymous"></script>

<script async
src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}">
</script>

<script>

window.dataLayer=window.dataLayer||[];

function gtag(){{dataLayer.push(arguments);}};

gtag('js',new Date());

gtag('config','{GA4_ID}');

</script>

<script type="application/ld+json">

{{
"@context":"https://schema.org",

"@type":"NewsArticle",

"headline":"{title}",

"datePublished":"{datetime.utcnow().strftime('%Y-%m-%d')}",

"dateModified":"{datetime.utcnow().strftime('%Y-%m-%d')}",

"author":{{

"@type":"Organization",

"name":"{SITE_NAME}"

}},

"publisher":{{

"@type":"Organization",

"name":"{SITE_NAME}"

}}

}}

</script>
"""

    return seo

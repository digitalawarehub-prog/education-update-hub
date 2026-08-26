"""
Education Update Hub - Reader Friendly Content Cleaner

Purpose:
- Never publish raw PDF extraction text as-is.
- Remove numbering/bullets/page-navigation noise.
- Repair common PDF/HTML extraction spacing and mojibake.
- Extract only strongly-labelled, verifiable recruitment details.
- Build a short human-readable summary from verified fields.
"""

import html
import re
import unicodedata
from datetime import datetime

PLACEHOLDERS = {
    "not available", "not mentioned", "not provided", "check official notification",
    "check notification", "as per rules", "to be announced", "tba", "n/a", "na",
    "none", "null", "unknown", "-", "--", "—", "–"
}

NOISE_PHRASES = [
    "skip to main content", "select your language", "screen reader", "accessibility",
    "sitemap", "site map", "copyright", "privacy policy", "terms and conditions",
    "go to index", "table of contents", "contents",
    "previous page", "next page", "page |", "a- a a+", "a a a", "main content",
    "click here for", "back to top", "print this page", "share this page",
]

# Tokens which are commonly complete Hindi words. Do not join them to the next token
# while repairing PDF glyph-spacing.
HI_STOPWORDS = {
    "में", "के", "का", "की", "को", "से", "पर", "और", "या", "एक", "यह", "वह",
    "इस", "उस", "ने", "तो", "ही", "भी", "है", "हैं", "था", "थे", "थी", "हो",
    "तथा", "हेतु", "द्वारा", "लिए", "पद", "पदों", "तक", "दिए", "गए", "जाने",
    "वाले", "वाली", "वाला", "कर", "केवल", "सभी", "आदि", "सी"
}

# Common fragments produced when PDF fonts split a single Devanagari word.
HI_JOIN_PREFIXES = {
    "बॉ", "टनि", "रि", "इंस्टी", "डा", "लि", "वि", "ज्ञा", "अंति", "ति",
    "सहा", "तृती", "कैशि", "ऑनला", "पदना", "कार्या", "शैक्षि", "योग्", "आवा",
    "अधि", "प्रा", "परि", "प्रमा", "विज्ञा", "ट्यू", "एनबी", "सहा",
}
HI_JOIN_SUFFIXES = {
    "टनि", "कल", "सर्च", "ट्यूट", "यरेक्टर", "ए", "ज्ञा", "पन", "म", "थि",
    "यक", "यर", "इन", "लय", "र्या", "आरआई", "य", "ल", "ना", "न",
}


# Common PDF mojibake sequences seen in scraped government notices.
MOJIBAKE = {
    "â€“": "–", "â€”": "—", "â€¢": "•", "â€˜": "‘", "â€™": "’",
    "â€œ": "“", "â€": "”", "Â": "", "ï»¿": "", "�": "",
    "â€": "", "￾": "", "\u00ad": "",
}

LIST_MARKER_RE = re.compile(
    r"^\s*(?:(?:\(?[a-zA-Zक-ह]\)?|\(?[क-ह]\)?|\d{1,3})\s*[-.)।:]|[•●▪◦‣►▸➤◆◇■□*]+|[-–—]+)\s*"
)

PAGE_RE = re.compile(r"^\s*(?:page|पृष्ठ)\s*\d+(?:\s*(?:of|/|में से)\s*\d+)?\s*$", re.I)

DATE_RE = re.compile(
    r"\b(?:0?[1-9]|[12]\d|3[01])(?:[-/. ](?:0?[1-9]|1[0-2])[-/. ]20\d{2}|\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+20\d{2})\b",
    re.I,
)


def _fix_mojibake(text):
    text = str(text or "")
    for old, new in MOJIBAKE.items():
        text = text.replace(old, new)
    # Remove zero-width/invisible formatting characters but keep normal Unicode.
    text = text.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    return text


def _repair_devanagari_spacing_line(line):
    """Repair obvious glyph-level Devanagari spacing without merging normal words."""
    tokens = line.split()
    if len(tokens) < 2:
        return line

    out = []
    i = 0
    while i < len(tokens):
        cur = tokens[i]
        while i + 1 < len(tokens):
            nxt = tokens[i + 1]
            cur_plain = re.sub(r"[^\u0900-\u097F]", "", cur)
            nxt_plain = re.sub(r"[^\u0900-\u097F]", "", nxt)
            if not (cur_plain and nxt_plain):
                break
            should_join = (
                cur_plain not in HI_STOPWORDS and
                (cur_plain in HI_JOIN_PREFIXES and len(cur_plain) <= 5 or nxt_plain in HI_JOIN_SUFFIXES or (len(nxt_plain) <= 2 and len(cur_plain) <= 4))
                and nxt_plain not in HI_STOPWORDS
                and len(cur_plain) <= 8 and len(nxt_plain) <= 10
                and not re.match(r"^[0-9]", cur)
            )
            if not should_join:
                break
            cur = cur + nxt
            i += 1
        out.append(cur)
        i += 1
    result = " ".join(out)
    result = re.sub(r"\bलेखा\s+का\s+र\b", "लेखाकार", result)
    result = re.sub(r"\bसहाय\s+क\b", "सहायक", result)
    result = re.sub(r"\bकार्या\s+लय\b", "कार्यालय", result)
    result = re.sub(r"\bका\s+र्यालय\b", "कार्यालय", result)
    result = re.sub(r"\bविज्ञा\s+पन\b", "विज्ञापन", result)
    result = re.sub(r"\bबॉटनिकल\s+रि\s+सर्च\b", "बॉटनिकल रिसर्च", result)
    result = re.sub(r"\bएनबी\s+आरआई\b", "एनबीआरआई", result)
    return result


def clean_line(line):
    line = _fix_mojibake(html.unescape(str(line or "")))
    line = line.replace("\t", " ").replace("\r", " ")
    line = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", line)
    line = re.sub(r"\s+", " ", line).strip()
    if not line:
        return ""
    if PAGE_RE.match(line):
        return ""
    low = line.lower()
    if re.fullmatch(r"\s*(?:login|register|sign in|home|contact|about|privacy policy|sitemap|site map)\s*", low):
        return ""
    if any(p in low for p in NOISE_PHRASES):
        return ""
    # Remove page/index artifacts embedded in extracted PDF text.
    line = re.sub(r"\bGO\s+TO\s+INDEX\s+\d+\b", " ", line, flags=re.I)
    line = re.sub(r"\b(?:CONTENTS|INDEX)\s*\d+\b", " ", line, flags=re.I)
    line = re.sub(r"\s+", " ", line).strip()
    # Keep slash as a separator, not as part of a PDF-split Devanagari token.
    line = re.sub(r"(?<=[\u0900-\u097F])/(?=[\u0900-\u097F])", " / ", line)
    # Remove leading list numbering/bullets such as 1-, 1., (a), (क), •, etc.
    line = LIST_MARKER_RE.sub("", line).strip()
    # Remove decorative symbol runs. Keep useful punctuation, dates, currency and slashes.
    line = re.sub(r"^[~`^_=+|<>#@%]+\s*", "", line)
    line = re.sub(r"\s*[•●▪◦‣►▸➤◆◇■□]+\s*", " ", line)
    line = re.sub(r"\s*[|]{1,}\s*", " ", line)
    line = re.sub(r"\s+", " ", line).strip(" -–—|;,")
    return _repair_devanagari_spacing_line(line)


def clean_pdf_text(text, max_chars=9000):
    """Turn extracted PDF text into short readable paragraphs; never return raw dump."""
    if not text:
        return ""
    text = _fix_mojibake(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = []
    for raw in text.split("\n"):
        line = clean_line(raw)
        if not line:
            continue
        # Drop lines that are overwhelmingly decorative/numeric page artifacts.
        alnum = len(re.findall(r"[A-Za-z\u0900-\u0DFF0-9]", line))
        if len(line) > 2 and alnum / max(len(line), 1) < 0.35:
            continue
        lines.append(line)

    # De-duplicate consecutive repeated headers/footers.
    dedup = []
    for line in lines:
        if dedup and line == dedup[-1]:
            continue
        dedup.append(line)

    text = "\n".join(dedup)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Never allow a giant raw notification to become the post body.
    return text[:max_chars].strip()


def clean_value(value, max_len=500):
    if value is None:
        return ""
    text = clean_pdf_text(str(value), max_chars=max_len)
    text = re.sub(r"\s+", " ", text).strip(" -–—:;|,.")
    if not text or text.lower() in PLACEHOLDERS:
        return ""
    if any(p in text.lower() for p in NOISE_PHRASES):
        return ""
    return text[:max_len]


def _source_text(job):
    parts = []
    for key in (
        "notification_text", "notification_content", "content", "description",
        "summary", "text", "raw_text", "body", "title"
    ):
        value = job.get(key)
        if value:
            parts.append(str(value))
    return clean_pdf_text("\n".join(parts), max_chars=20000)


def _first_date(text):
    if not text:
        return ""
    m = re.search(
        r"(?:last\s*date(?:\s*to\s*apply)?|application\s+(?:last\s*)?date|closing\s*date|deadline|registration\s+(?:last\s*)?date|अंतिम\s*तिथि|अंतिम\s*तारीख|आवेदन\s*की\s*अंतिम\s*तिथि)\s*[:\-–]?\s*([^\n|;]{1,80})",
        text,
        re.I,
    )
    if m:
        d = DATE_RE.search(m.group(1))
        if d:
            return d.group(0)
    # Title often contains [Last Date: dd/mm/yyyy].
    d = DATE_RE.search(text)
    return d.group(0) if d else ""


def _label_value(text, labels, max_len=400):
    if not text:
        return ""
    label = "(?:" + "|".join(labels) + ")"
    # Strong labels only. Do not grab arbitrary sentences after the word "qualification".
    patterns = [
        rf"(?:{label})\s*[:\-–]\s*([^\n|;]{{3,{max_len}}})",
        rf"(?:{label})\s+(?:is|are|:)?\s*([^\n|;]{{3,{max_len}}})",
    ]
    for p in patterns:
        for m in re.finditer(p, text, re.I):
            value = clean_value(m.group(1), max_len)
            if not value:
                continue
            low = value.lower()
            if any(x in low for x in ("caste certificate", "verified with", "wrongful submission", "go to index")):
                continue
            return value
    return ""


def _vacancy(text):
    # Prefer explicit totals. Generic "36 posts" is deliberately not accepted because
    # PDF tables contain many row-level numbers and were causing false vacancy values.
    strong = [
        r"(?:total\s+(?:number\s+of\s+)?(?:vacancies|posts)|total\s+vacancies|total\s+posts|number\s+of\s+vacancies|no\.?\s+of\s+vacancies|no\.?\s+of\s+posts)\s*[:\-–]?\s*(\d{1,6}(?:\s*[-–]\s*\d{1,6})?)",
        r"(?:vacancies|posts)\s*[:\-–]\s*(\d{1,6}(?:\s*[-–]\s*\d{1,6})?)",
        r"(?:कुल\s+पद|कुल\s+रिक्तियां|रिक्त\s+पद)\s*[:\-–]?\s*(\d{1,6}(?:\s*[-–]\s*\d{1,6})?)",
    ]
    for p in strong:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1).strip()
    return ""


def extract_verified_details(job):
    """Return only strongly labelled, reasonably trustworthy fields."""
    text = _source_text(job)
    result = {}

    # Prefer existing structured values only when they are clean and short.
    for out_key, keys, limit in [
        ("vacancy", ("vacancy", "vacancies", "total_vacancies", "total_posts", "posts"), 120),
        ("qualification", ("qualification", "educational_qualification", "eligibility", "education"), 300),
        ("salary", ("salary", "pay_scale", "pay", "remuneration", "salary_details", "emoluments"), 240),
        ("last_date", ("last_date", "deadline", "application_last_date", "last_date_to_apply", "closing_date"), 100),
        ("age_limit", ("age_limit",), 220),
        ("application_fee", ("application_fee", "fee", "application_fee_details"), 240),
        ("selection_process", ("selection_process",), 260),
        ("exam_date", ("exam_date",), 100),
        ("application_start", ("application_start", "application_start_date"), 100),
    ]:
        value = ""
        for key in keys:
            value = clean_value(job.get(key), limit)
            if value:
                break
        if value:
            result[out_key] = value

    if "vacancy" not in result:
        v = _vacancy(text)
        if v:
            result["vacancy"] = v

    if "qualification" not in result:
        q = _label_value(text, [
            r"educational\s+qualification", r"essential\s+qualification",
            r"minimum\s+qualification", r"qualification", r"eligibility",
            r"शैक्षणिक\s+योग्यता", r"आवश्यक\s+योग्यता", r"योग्यता", r"पात्रता"
        ], 300)
        if q:
            result["qualification"] = q

    if "salary" not in result:
        s = _label_value(text, [
            r"pay\s+scale", r"pay\s+level", r"salary", r"remuneration", r"emoluments",
            r"वेतनमान", r"वेतन", r"मानदेय", r"पारिश्रमिक"
        ], 240)
        if s:
            result["salary"] = s

    if "last_date" not in result:
        d = _first_date(text)
        if d:
            result["last_date"] = d

    # Date fields are normalized to dates only; do not render full source sentences.
    for key in ("exam_date", "application_start", "last_date"):
        if key in result:
            d = DATE_RE.search(result[key])
            result[key] = d.group(0) if d else ""
            if not result[key]:
                result.pop(key, None)

    return result


def clean_title(title):
    text = clean_line(str(title or ""))
    # Remove scraper-added date/registration suffixes from title; dates are shown separately.
    text = re.sub(r"\s*\[\s*(?:last\s*date|अंतिम\s*तिथि|अंतिम\s*तारीख)[^\]]*\]\s*$", "", text, flags=re.I)
    text = re.sub(r"\s*\((?:last\s*date|अंतिम\s*तिथि)[^)]*\)\s*$", "", text, flags=re.I)
    text = re.sub(r"\s+(?:registration|application)\s+(?:from|started\s+from)\s+\d{1,2}[-/][A-Za-z]{3,9}[-/]20\d{2}\s*$", "", text, flags=re.I)
    text = re.sub(r"\s+(?:registration|application)\s+(?:from|started\s+from)\s+\d{1,2}[-/]\d{1,2}[-/]20\d{2}\s*$", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" -–—|,:;")
    return text


def build_reader_summary(job, details=None):
    details = details or extract_verified_details(job)
    title = clean_title(job.get("title")) or "सरकारी अपडेट"
    date = details.get("last_date", "")
    parts = [f"{title} के बारे में जरूरी जानकारी आसान भाषा में दी गई है।"]
    if details.get("vacancy"):
        parts.append(f"इस भर्ती में {details['vacancy']} पदों की जानकारी उपलब्ध है।")
    if details.get("qualification"):
        parts.append(f"शैक्षणिक योग्यता: {details['qualification']}।")
    if details.get("salary"):
        parts.append(f"वेतन/मानदेय: {details['salary']}।")
    if date:
        parts.append(f"आवेदन की अंतिम तिथि {date} है।")
    parts.append("आवेदन करने से पहले आधिकारिक अधिसूचना में दी गई पूरी शर्तें जरूर पढ़ें।")
    return " ".join(parts)


def normalize_job(job):
    if not isinstance(job, dict):
        return job
    details = extract_verified_details(job)
    title = clean_title(job.get("title"))
    if title:
        job["title"] = title
    # Replace unsafe/garbled detail fields with verified values only.
    for key in ("vacancy", "qualification", "salary", "last_date", "age_limit", "application_fee", "selection_process", "exam_date", "application_start"):
        if key in details:
            job[key] = details[key]
        elif key in job:
            # A raw field is not shown if it contains PDF/navigation noise.
            cleaned = clean_value(job.get(key), 300)
            job[key] = cleaned
    # Never keep a giant raw PDF dump as the public content.
    raw = job.get("notification_text") or job.get("notification_content") or job.get("content") or ""
    cleaned_raw = clean_pdf_text(raw, max_chars=9000)
    if cleaned_raw:
        job["notification_text_clean"] = cleaned_raw
    job["reader_summary"] = build_reader_summary(job, details)
    # Downstream homepage/search modules should never receive raw scraper prose.
    if job.get("description") and not job.get("source_description"):
        job["source_description"] = str(job.get("description"))[:5000]
    job["description"] = job["reader_summary"]
    job["summary"] = job["reader_summary"]
    job["content"] = job["reader_summary"]
    job["content_cleaned"] = True
    # Preserve the source PDF URL, but do not make a non-PDF page look like a notification.
    pdf = str(job.get("notification_pdf") or "").strip()
    if pdf and not re.sub(r"\?.*$", "", pdf).lower().endswith(".pdf"):
        job["notification_pdf"] = ""
    # Never use the source page itself as an Apply button.
    if str(job.get("apply_link") or "").strip().rstrip("/") == str(job.get("url") or "").strip().rstrip("/"):
        job["apply_link"] = ""
    return job


def normalize_jobs(jobs):
    out = []
    for job in jobs or []:
        try:
            out.append(normalize_job(job))
        except Exception:
            out.append(job)
    return out

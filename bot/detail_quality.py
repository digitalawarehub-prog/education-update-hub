"""
Shared detail-quality and sanitization helpers.

The publisher receives data from HTML, PDF text extraction and OCR. OCR can
produce plausible-looking fragments such as "(As on 01" or "c. At the time of
Main". These helpers prevent such fragments from reaching the public HTML.
"""
import re

PLACEHOLDERS = {
    "", "not mentioned", "not available", "check official notification",
    "check notification", "official notification", "as per rules",
    "see official notification", "available", "none", "null", "n/a", "na",
    "उपलब्ध नहीं", "आधिकारिक अधिसूचना देखें", "आधिकारिक अधिसूचना में देखें",
}

GARBAGE_PATTERNS = (
    r"^\(?\s*as\s+on\b",
    r"^\(?\s*as\s+at\b",
    r"^\(?\s*c\.?\s*at\s+the\s+time\b",
    r"^\(?\s*at\s+the\s+time\s+of\b",
    r"^\(?\s*at\s+the\s+time\b",
    r"^\s*[\W_]*rs\.?\s*\d{1,2}\s*$",
    r"^\s*(?:a|an|the|of|and|or|i|ii|iii|iv)\s*$",
    r"^\s*[.:;\-–—]+\s*$",
)

def clean_detail(value):
    value = str(value or "")
    value = value.replace("\u00a0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"^[|:;,\-–—\s]+", "", value)
    value = re.sub(r"[|;]+\s*$", "", value)
    return value.strip()

def is_bad_detail(value, field=None):
    value = clean_detail(value)
    if not value:
        return True
    low = value.casefold()
    if low in PLACEHOLDERS:
        return True
    if any(re.search(p, low, re.I) for p in GARBAGE_PATTERNS):
        return True

    if len(value) > 900 and field in {"qualification", "salary", "age_limit",
                                       "application_fee", "selection_process"}:
        return True

    if field == "vacancy":
        nums = re.findall(r"(?<![\d/.-])\d{1,6}(?![\d/.-])", value)
        if not nums or re.search(r"\b(?:as\s+on|registration\s+opens|important\s+timeline)\b", low):
            return True

    if field == "qualification":
        if len(value) < 5:
            return True
        if re.search(r"\b(?:registration\s+opens|registration\s+closes|important\s+timeline|apply\s+online\s+now|create\s+an\s+account)\b", low):
            return True
        if re.fullmatch(r"[\W_]*[a-z]\b[\W_]*", low):
            return True

    if field == "salary":
        if len(value) < 3:
            return True
        if re.fullmatch(r"(?:rs\.?|₹|inr)\s*\d{1,2}", low):
            return True
        if not re.search(r"(?:₹|rs\.?|inr|level\s*[-–]?\s*\d|\d[\d,]{2,}\s*[-–]\s*\d)", value, re.I):
            return True

    if field == "age_limit":
        # A bare eligibility-date fragment is not an age limit.
        if re.search(r"^\s*\(?\s*as\s+on\b", low) and not re.search(r"\b(?:years?|वर्ष)\b", low):
            return True
        if not re.search(r"\d", value):
            return True

    if field == "application_fee":
        if len(value) > 300:
            return True
        if re.search(r"https?://|www\.|facebook|twitter|instagram", low):
            return True
        if not re.search(r"\d", value) and not re.search(r"\b(?:free|no\s*fee|nil|निः?शुल्क|शुल्क\s*नहीं)\b", value, re.I):
            return True

    if field in {"exam_date", "application_start_date", "last_date"}:
        # Date fields must contain an actual calendar date, not a nearby
        # schedule sentence or OCR fragment.
        if not re.search(
            r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|"
            r"\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+20\d{2}\b",
            low, re.I
        ):
            return True

    if field in {"qualification", "selection_process"} and re.search(r"https?://|www\.", low):
        return True

    if field == "selection_process":
        # Common navigation/instruction text accidentally captured from
        # government listing pages is not a selection method.
        navigation_phrases = (
            "के संबंध में जानकारी",
            "परीक्षा कार्यक्रम",
            "प्रवेश पत्र",
            "आयोग की वेबसाइट",
            "वेबसाइट पर उपलब्ध",
            "information regarding",
            "exam programme",
            "download admit card",
            "visit the website",
            "for more information",
        )
        if any(p in low for p in navigation_phrases):
            return True

    return False

def sanitize_detail(value, field=None, fallback=""):
    value = clean_detail(value)
    if is_bad_detail(value, field):
        return fallback
    return value

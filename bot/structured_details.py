"""Conservative structured field extraction from recruitment notifications."""
import re

BAD = {
    "", "not mentioned", "not available", "check official notification", "check notification",
    "as per rules", "n/a", "na", "none", "null", "-", "=", "."
}
CONNECTORS = {"and","or","of","for","with","to","the","a","an","के","की","का","में","से","हेतु","तथा","और","या"}


def _norm(v):
    s = str(v or "").replace("\xa0", " ").replace("\u200b", "")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^[\s=.:;,|/\\\-–—•·]+", "", s)
    return s.strip(" -:;,|./")


def _valid(v, field=""):
    s = _norm(v)
    if s.casefold() in BAD:
        return ""
    low = s.casefold()
    bad = ("go to index", "previous button", "support_agent", "slips, etc", "page no",
           "step-1", "login / register", "technical support", "copyright", "all rights reserved",
           "the page you requested", "candidates are warned", "stipulated dates before registering")
    if any(x in low for x in bad):
        return ""
    if len(s) > 500:
        return ""
    if field == "qualification":
        # OCR from PDF tables often interleaves salary/age columns into the
        # qualification sentence. Publishing that is worse than hiding it.
        if any(x in low for x in ("per month", "per annum", "rs.", "₹", "maximum:", "fixed for", "monthly")):
            return ""
        if "|" in s or "registered office" in low or "corporate office" in low or len(re.findall(r"\b20\d{2}\b", s)) >= 1:
            return ""
        if re.fullmatch(r"(?:educational|qualification|eligibility)\s*:?\s*[A-Za-z]", low):
            return ""
    words = re.findall(r"[A-Za-z]+|[\u0900-\u097F]+", low)
    if words and words[-1] in CONNECTORS:
        return ""
    if field == "vacancy" and not re.search(r"\b[0-9]{1,6}\b", s):
        return ""
    if len(re.findall(r"[A-Za-z0-9\u0900-\u097F]", s)) < 2:
        return ""
    return s


def source_text(job):
    vals = []
    for k in ("notification_text_clean", "notification_text", "notification_content", "content", "raw_text", "description", "text", "body", "title"):
        if job.get(k):
            vals.append(str(job[k]))
    return re.sub(r"\s+", " ", " ".join(vals))


def _label_capture(text, labels, stops, max_len=300):
    """Capture text after an exact label and stop at the next section heading."""
    label = "(?:" + "|".join(labels) + ")"
    stop = "(?:" + "|".join(stops) + ")"
    m = re.search(rf"(?:^|[|.!?;])\s*{label}\s*[:\-–]\s*(.+?)(?=\s+(?:{stop})\s*[:\-–]|\s+(?:{stop})\b|$)", text, re.I | re.S)
    if not m:
        m = re.search(rf"\b{label}\s*[:\-–]\s*(.+?)(?=\s+(?:{stop})\s*[:\-–]|\s+(?:{stop})\b|$)", text, re.I | re.S)
    if not m:
        return ""
    value = _norm(m.group(1))
    if len(value) > max_len:
        value = value[:max_len]
    return value


def _currency_near(text, labels, window=180):
    label = "(?:" + "|".join(labels) + ")"
    m = re.search(rf"\b{label}\b[^.{{}}]{{0,{window}}}?((?:₹|Rs\.?|INR|रु\.?)\s*[0-9][0-9,]*(?:\s*[-–]\s*(?:₹|Rs\.?|INR|रु\.?)?\s*[0-9][0-9,]*)?(?:\s*(?:per\s+month|per\s+annum|p\.a\.|monthly))?)", text, re.I | re.S)
    return _valid(m.group(1), "salary") if m else ""


def _essential_qualification(text):
    """Prefer an explicit Essential Qualification block over OCR table headers."""
    matches = list(re.finditer(r"\bessential\s+qualifications?\s*[:\-–]\s*", text, re.I))
    if not matches:
        return ""
    stops = r"desirable\s+qualifications?|nature\s+of\s+work|general\s+instructions|age\s+limit|selection\s+process|selection\s+criteria|pay\s+scale|application\s+fee|important\s+dates"
    for m in matches:
        tail = text[m.end():]
        sm = re.search(rf"\s+(?:{stops})\b\s*[:\-–]?", tail, re.I)
        candidate = tail[:sm.start()] if sm else tail[:700]
        candidate = _norm(candidate)
        # A useful qualification normally starts with an education/degree term.
        if re.search(r"\b(?:bachelor|master|graduate|post[- ]?graduate|diploma|degree|10th|12th|matric|mbbs|b\.\s*tech|m\.\s*tech|ph\.\s*d|class\s*x|class\s*xii)\b", candidate, re.I):
            # Strip an OCR/table prefix if one slipped before the real sentence.
            qm = re.search(r"\b(?:Bachelor|Master|Graduate|Post[- ]?Graduate|Diploma|Degree|MBBS|Ph\.?D\.?|10th|12th|Matric|Class\s+X|Class\s+XII)\b", candidate, re.I)
            if qm and qm.start() > 0:
                candidate = candidate[qm.start():]
            return _valid(candidate[:420], "qualification")
    return ""


def extract_details(job):
    text = source_text(job)
    out = {}

    # Trust already-clean fields first.
    for field in ("vacancy", "qualification", "salary", "age_limit", "application_fee", "selection_process", "exam_date", "application_start_date", "last_date"):
        v = _valid(job.get(field), field)
        if v:
            out[field] = v

    if not out.get("vacancy"):
        # Only accept explicit totals or an explicit number immediately before posts/vacancies.
        patterns = [
            r"\b(?:total\s+(?:number\s+of\s+)?(?:posts?|vacancies)|total\s+vacancies|total\s+posts?)\s*[:\-–]?\s*([0-9]{1,6})\b",
            r"\b([0-9]{1,6})\s+(?:posts?|vacancies)\b",
            r"\b(?:01|02|03|04|05|06|07|08|09|10)\s*\(?(?:one|two|three|four|five|six|seven|eight|nine|ten)\)?\s+(?:post|posts)\b",
        ]
        for p in patterns:
            m = re.search(p, text, re.I)
            if m:
                candidate = m.group(1) if m.lastindex else m.group(0)
                candidate = _valid(candidate, "vacancy")
                if candidate:
                    out["vacancy"] = candidate
                    break

    if not out.get("qualification"):
        q = _essential_qualification(text)
        if not q:
            m = re.search(r"\b(?:qualification|eligibility)\s*[:\-–]\s*([^.;]{12,260})", text, re.I)
            q = _valid(m.group(1), "qualification") if m else ""
        if q:
            out["qualification"] = q

    if not out.get("salary"):
        salary = _currency_near(text, ["pay scale", "salary", "remuneration", "consolidated pay", "emoluments", "वेतनमान", "वेतन", "मानदेय"])
        if not salary:
            m = re.search(r"((?:₹|Rs\.?|INR|रु\.?)\s*[0-9][0-9,]*(?:\s*[-–]\s*(?:₹|Rs\.?|INR|रु\.?)?\s*[0-9][0-9,]+)?\s*(?:per\s+month|per\s+annum|p\.?a\.?|monthly))", text, re.I)
            salary = _valid(m.group(1), "salary") if m else ""
        if not salary:
            m = re.search(r"\b(Level\s*[-–]?\s*[0-9]+(?:\s*\([^.;]{0,100}\))?)", text, re.I)
            salary = _valid(m.group(1), "salary") if m else ""
        if salary:
            out["salary"] = salary

    if not out.get("age_limit"):
        age = _label_capture(text,
            ["age limit", "age criteria", "upper age limit", "lower age limit", "आयु सीमा", "उम्र सीमा"],
            ["application fee", "selection process", "selection criteria", "essential qualification", "educational qualification", "pay scale", "salary", "important dates", "general instructions"], 300)
        if not age:
            m = re.search(r"\b(?:minimum|maximum|upper|lower)\s+age\s*[:\-–]?\s*([^.;]{3,160})", text, re.I)
            age = m.group(1) if m else ""
        age = _valid(age, "age_limit")
        if age:
            out["age_limit"] = age

    if not out.get("application_fee"):
        fee = _label_capture(text,
            ["application fee", "application fees", "fee details", "application fee details", "आवेदन शुल्क", "परीक्षा शुल्क"],
            ["selection process", "important dates", "last date", "age limit", "general instructions", "eligibility"], 220)
        if fee:
            # Keep a compact fee statement; reject paragraph-sized captures.
            m = re.search(r"((?:₹|Rs\.?|INR|रु\.?)\s*[0-9][0-9,]*(?:\s*/\s*(?:₹|Rs\.?|INR|रु\.?)?\s*[0-9][0-9,]*)?(?:[^.;]{0,80})?)", fee, re.I)
            fee = m.group(1) if m else fee if len(fee) <= 100 else ""
        if not fee:
            fee = _currency_near(text, ["application fee", "application fees", "fee", "आवेदन शुल्क"], 120)
        fee = _valid(fee, "application_fee")
        if fee:
            out["application_fee"] = fee

    if not out.get("selection_process"):
        sel = _label_capture(text,
            ["selection process", "selection criteria", "method of selection", "चयन प्रक्रिया", "चयन का तरीका"],
            ["important dates", "exam date", "application fee", "age limit", "general instructions", "how to apply"], 350)
        sel = _valid(sel, "selection_process")
        if sel:
            out["selection_process"] = sel

    date = r"(\d{1,2}[/-]\d{1,2}[/-](?:20)?\d{2}|\d{1,2}\s+[A-Za-z]+\s+20\d{2}|[A-Za-z]+\s+\d{1,2},?\s+20\d{2})"
    if not out.get("application_start_date"):
        m = re.search(rf"(?:application|registration|online application)\s+(?:starts?|begin(?:s)?|opens?|commences?)\s*[:\-–]?\s*{date}", text, re.I)
        if not m:
            m = re.search(rf"(?:आवेदन|पंजीकरण)\s*(?:प्रारंभ|आरंभ)\s*(?:तिथि|दिनांक)?\s*[:\-–]?\s*{date}", text, re.I)
        if m:
            out["application_start_date"] = _valid(m.group(1))

    if not out.get("last_date"):
        m = re.search(rf"(?:last\s+date(?:\s+to\s+apply)?|application\s+(?:last\s+)?date|deadline|closing\s+date|registration\s+(?:last\s+)?date)\s*[:\-–]?\s*{date}", text, re.I)
        if not m:
            m = re.search(rf"(?:apply|application)\s+(?:till|by|before)\s*[:\-–]?\s*{date}", text, re.I)
        if not m:
            m = re.search(rf"(?:अंतिम\s*तिथि|अंतिम\s*तारीख|आवेदन\s*की\s*अंतिम\s*तिथि)\s*[:\-–]?\s*{date}", text, re.I)
        if m:
            out["last_date"] = _valid(m.group(1))

    if not out.get("exam_date"):
        m = re.search(rf"(?:exam|examination|test)\s+date\s*[:\-–]?\s*{date}", text, re.I)
        if not m:
            m = re.search(rf"(?:परीक्षा\s*तिथि|परीक्षा\s*दिनांक)\s*[:\-–]?\s*{date}", text, re.I)
        if m:
            out["exam_date"] = _valid(m.group(1))

    return {k: v for k, v in out.items() if _valid(v, k)}

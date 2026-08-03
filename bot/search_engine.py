"""
=========================================================
Education Update Hub
Search V5 Pro
Part 1
Core Search Engine
=========================================================
"""

import json
import logging
import re
from pathlib import Path
from difflib import SequenceMatcher

logger = logging.getLogger("SearchV5")

ROOT_DIR = Path(__file__).resolve().parent.parent

SEARCH_INDEX = ROOT_DIR / "search-index.json"

MAX_RESULTS = 20

MIN_QUERY = 2


# ==========================================================
# Safe Text
# ==========================================================

def safe(value):

    if value is None:
        return ""

    return str(value).strip()


# ==========================================================
# Normalize
# ==========================================================

def normalize(text):

    text = safe(text).lower()

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ==========================================================
# Similarity
# ==========================================================

def similarity(a, b):

    return SequenceMatcher(
        None,
        normalize(a),
        normalize(b)
    ).ratio()


# ==========================================================
# Load Search Index
# ==========================================================

def load_index():

    if not SEARCH_INDEX.exists():

        logger.warning(
            "search-index.json not found."
        )

        return []

    with open(
        SEARCH_INDEX,
        "r",
        encoding="utf-8"
    ) as file:

        try:

            return json.load(file)

        except Exception:

            logger.exception(
                "Invalid Search Index"
            )

            return []


# ==========================================================
# Tokenize
# ==========================================================

def tokenize(query):

    query = normalize(query)

    return [

        token

        for token in query.split()

        if token

    ]


logger.info(
    "Search V5 Part 1 Loaded Successfully"
)
# ==========================================================
# Search Score
# ==========================================================

def calculate_score(job, query):

    score = 0

    query = normalize(query)

    title = normalize(job.get("title"))

    category = normalize(job.get("category"))

    department = normalize(job.get("department"))

    state = normalize(job.get("state"))

    description = normalize(job.get("description"))

    # Exact Title Match
    if query == title:
        score += 100

    # Starts With
    elif title.startswith(query):
        score += 80

    # Title Contains
    elif query in title:
        score += 60

    # Category
    if query in category:
        score += 30

    # Department
    if query in department:
        score += 25

    # State
    if query in state:
        score += 20

    # Description
    if query in description:
        score += 10

    # Similarity Bonus
    similarity_score = similarity(
        query,
        title
    )

    score += int(
        similarity_score * 40
    )

    return score


# ==========================================================
# Search Jobs
# ==========================================================

def search(query):

    query = normalize(query)

    if len(query) < MIN_QUERY:
        return []

    jobs = load_index()

    results = []

    for job in jobs:

        score = calculate_score(
            job,
            query
        )

        if score <= 0:
            continue

        item = job.copy()

        item["score"] = score

        results.append(item)

    results.sort(

        key=lambda x: x["score"],

        reverse=True

    )

    return results[:MAX_RESULTS]


# ==========================================================
# Search By Category
# ==========================================================

def search_category(category):

    category = normalize(category)

    jobs = load_index()

    return [

        job

        for job in jobs

        if category in normalize(

            job.get("category")

        )

    ]


# ==========================================================
# Search By Department
# ==========================================================

def search_department(department):

    department = normalize(department)

    jobs = load_index()

    return [

        job

        for job in jobs

        if department in normalize(

            job.get("department")

        )

    ]


# ==========================================================
# Search By State
# ==========================================================

def search_state(state):

    state = normalize(state)

    jobs = load_index()

    return [

        job

        for job in jobs

        if state in normalize(

            job.get("state")

        )

    ]


logger.info(
    "Search V5 Part 2 Loaded Successfully"
)
# ==========================================================
# Search V5 Pro
# Part 3
# Did You Mean + Suggestions + Trending
# ==========================================================

MAX_SUGGESTIONS = 8

# ==========================================================
# Get All Titles
# ==========================================================

def all_titles():

    jobs = load_index()

    return [

        safe(job.get("title"))

        for job in jobs

        if safe(job.get("title"))

    ]


# ==========================================================
# Did You Mean
# ==========================================================

def did_you_mean(query):

    query = normalize(query)

    best_match = ""

    best_score = 0

    for title in all_titles():

        score = similarity(
            query,
            title
        )

        if score > best_score:

            best_score = score

            best_match = title

    if best_score >= 0.60:

        return best_match

    return ""


# ==========================================================
# Search Suggestions
# ==========================================================

def suggestions(query):

    query = normalize(query)

    jobs = load_index()

    results = []

    seen = set()

    for job in jobs:

        title = safe(
            job.get("title")
        )

        if not title:

            continue

        if query not in normalize(title):

            continue

        if title in seen:

            continue

        seen.add(title)

        results.append(title)

        if len(results) >= MAX_SUGGESTIONS:

            break

    return results


# ==========================================================
# Trending Searches
# ==========================================================

def trending():

    jobs = load_index()

    seen = set()

    top = []

    for job in jobs:

        category = safe(
            job.get("category")
        )

        if not category:

            continue

        if category in seen:

            continue

        seen.add(category)

        top.append(category)

    return top[:10]


# ==========================================================
# Related Searches
# ==========================================================

def related(query):

    query = normalize(query)

    jobs = load_index()

    related_titles = []

    seen = set()

    for job in jobs:

        title = safe(
            job.get("title")
        )

        if similarity(query, title) < 0.40:

            continue

        if title in seen:

            continue

        seen.add(title)

        related_titles.append(title)

        if len(related_titles) >= 10:

            break

    return related_titles


logger.info(
    "Search V5 Part 3 Loaded Successfully"
)
# ==========================================================
# Search V5 Pro
# Part 4
# Spell Correction + Synonyms + Smart Matching
# ==========================================================

SPELL_MAP = {

    "ctett": "ctet",
    "utett": "utet",
    "upse": "upsc",
    "upssc": "upsc",
    "ibsp": "ibps",
    "railwey": "railway",
    "railwai": "railway",
    "bank": "banking",
    "teacherjob": "teacher",
    "govt": "government",
    "gov": "government",
    "admitcard": "admit card",
    "answerkey": "answer key",
    "scholarships": "scholarship",
    "results": "result"

}


# ==========================================================
# Synonyms
# ==========================================================

SYNONYMS = {

    "teacher": [
        "tet",
        "ctet",
        "utet",
        "lecturer",
        "assistant professor",
        "principal"
    ],

    "banking": [
        "bank",
        "ibps",
        "sbi",
        "pnb",
        "bob"
    ],

    "railway": [
        "rrb",
        "rail",
        "ntpc",
        "alp",
        "technician"
    ],

    "defence": [
        "army",
        "air force",
        "navy",
        "agniveer",
        "bsf",
        "crpf"
    ],

    "upsc": [
        "ias",
        "ifs",
        "ips",
        "civil services"
    ],

    "ssc": [
        "cgl",
        "chsl",
        "gd",
        "mts"
    ]

}


# ==========================================================
# Correct Query
# ==========================================================

def correct_query(query):

    query = normalize(query)

    words = []

    for word in query.split():

        words.append(

            SPELL_MAP.get(

                word,

                word

            )

        )

    return " ".join(words)


# ==========================================================
# Expand Query
# ==========================================================

def expand_query(query):

    query = correct_query(query)

    expanded = set()

    expanded.add(query)

    for word in query.split():

        expanded.add(word)

        if word in SYNONYMS:

            for item in SYNONYMS[word]:

                expanded.add(item)

    return list(expanded)


# ==========================================================
# Smart Search
# ==========================================================

def smart_search(query):

    queries = expand_query(query)

    merged = {}

    for q in queries:

        results = search(q)

        for job in results:

            slug = safe(

                job.get("slug")

            )

            if slug not in merged:

                merged[slug] = job

    final = list(

        merged.values()

    )

    final.sort(

        key=lambda x: x.get(

            "score",

            0

        ),

        reverse=True

    )

    return final[:MAX_RESULTS]


logger.info(
    "Search V5 Part 4 Loaded Successfully"
)

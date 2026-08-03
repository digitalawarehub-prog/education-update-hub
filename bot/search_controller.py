"""
=========================================================
Education Update Hub
Search Controller V5
Part 1
=========================================================
"""

import logging
import time
from collections import deque
from pathlib import Path

from search_engine import (
    search,
    smart_search,
    did_you_mean,
    suggestions,
    trending
)

logger = logging.getLogger("SearchController")

ROOT_DIR = Path(__file__).resolve().parent.parent

MAX_RECENT = 10

MAX_HISTORY = 100

CACHE_EXPIRE = 300

SEARCH_DELAY = 0.20


# ==========================================================
# Search Cache
# ==========================================================

SEARCH_CACHE = {}

CACHE_TIME = {}

# ==========================================================
# Recent Search
# ==========================================================

RECENT_SEARCHES = deque(
    maxlen=MAX_RECENT
)

# ==========================================================
# Search Analytics
# ==========================================================

SEARCH_HISTORY = deque(
    maxlen=MAX_HISTORY
)

# ==========================================================
# Session
# ==========================================================

SESSION = {

    "query": "",

    "results": [],

    "did_you_mean": "",

    "suggestions": [],

    "time": 0

}

# ==========================================================
# Cache Helpers
# ==========================================================

def cache_valid(query):

    if query not in CACHE_TIME:

        return False

    return (

        time.time()

        - CACHE_TIME[query]

    ) < CACHE_EXPIRE


def cache_get(query):

    return SEARCH_CACHE.get(query)


def cache_set(query, data):

    SEARCH_CACHE[query] = data

    CACHE_TIME[query] = time.time()


logger.info(
    "Search Controller V5 Part 1 Loaded"
)
# ==========================================================
# Search Controller
# ==========================================================

class SearchController:

    def __init__(self):

        self.last_query = ""

        self.last_results = []

        self.last_time = 0

    # ======================================================
    # Search
    # ======================================================

    def search(self, query):

        query = query.strip()

        if not query:

            return []

        # Cache
        if cache_valid(query):

            logger.info(
                "Cache Hit : %s",
                query
            )

            return cache_get(query)

        start = time.time()

        results = smart_search(query)

        duration = round(

            time.time() - start,

            3

        )

        SESSION["query"] = query

        SESSION["results"] = results

        SESSION["time"] = duration

        self.last_query = query

        self.last_results = results

        self.last_time = duration

        cache_set(

            query,

            results

        )

        SEARCH_HISTORY.append(

            query

        )

        if query not in RECENT_SEARCHES:

            RECENT_SEARCHES.appendleft(

                query

            )

        logger.info(

            "Search : %s (%d Results)",

            query,

            len(results)

        )

        return results

    # ======================================================
    # Suggestions
    # ======================================================

    def suggestions(self, query):

        return suggestions(query)

    # ======================================================
    # Did You Mean
    # ======================================================

    def did_you_mean(self, query):

        return did_you_mean(query)

    # ======================================================
    # Trending
    # ======================================================

    def trending(self):

        return trending()
# ==========================================================
# Search Controller V5
# Part 3
# Live Search + Debounce + Statistics
# ==========================================================

    # ======================================================
    # Live Search
    # ======================================================

    def live_search(self, query):

        query = query.strip()

        if len(query) < 2:

            return []

        return self.search(query)

    # ======================================================
    # Debounce
    # ======================================================

    def debounce(self):

        now = time.time()

        if (

            now - self.last_time

            < SEARCH_DELAY

        ):

            return False

        self.last_time = now

        return True

    # ======================================================
    # Result Count
    # ======================================================

    def result_count(self):

        return len(

            self.last_results

        )

    # ======================================================
    # Search Time
    # ======================================================

    def search_time(self):

        return SESSION.get(

            "time",

            0

        )

    # ======================================================
    # Recent Searches
    # ======================================================

    def recent(self):

        return list(

            RECENT_SEARCHES

        )

    # ======================================================
    # History
    # ======================================================

    def history(self):

        return list(

            SEARCH_HISTORY

        )

    # ======================================================
    # Clear Cache
    # ======================================================

    def clear_cache(self):

        SEARCH_CACHE.clear()

        CACHE_TIME.clear()

        logger.info(

            "Search Cache Cleared"

        )

    # ======================================================
    # Clear Recent
    # ======================================================

    def clear_recent(self):

        RECENT_SEARCHES.clear()

    # ======================================================
    # Search Statistics
    # ======================================================

    def statistics(self):

        return {

            "cache": len(

                SEARCH_CACHE

            ),

            "recent": len(

                RECENT_SEARCHES

            ),

            "history": len(

                SEARCH_HISTORY

            ),

            "last_query":

                self.last_query,

            "last_results":

                len(

                    self.last_results

                ),

            "last_time":

                self.last_time

        }


logger.info(
    "Search Controller V5 Part 3 Loaded"
)
# ==========================================================
# Search Controller V5
# Part 4
# AI Ranking + Featured + Best Match
# ==========================================================

    # ======================================================
    # Best Match
    # ======================================================

    def best_match(self, query):

        results = self.search(query)

        if not results:

            return None

        return results[0]

    # ======================================================
    # Featured Result
    # ======================================================

    def featured(self, query):

        result = self.best_match(query)

        if not result:

            return None

        result["featured"] = True

        return result

    # ======================================================
    # AI Rank
    # ======================================================

    def ai_rank(self, results):

        ranked = []

        for index, job in enumerate(results):

            item = job.copy()

            item["rank"] = index + 1

            item["score"] = max(

                100 - (index * 2),

                1

            )

            ranked.append(item)

        return ranked

    # ======================================================
    # Auto Complete
    # ======================================================

    def autocomplete(self, query):

        items = suggestions(query)

        return items[:8]

    # ======================================================
    # Did You Mean
    # ======================================================

    def suggest(self, query):

        value = did_you_mean(query)

        if value:

            SESSION["did_you_mean"] = value

        return value

    # ======================================================
    # Featured + Ranked Search
    # ======================================================

    def smart_results(self, query):

        results = self.search(query)

        if not results:

            return []

        return self.ai_rank(results)

    # ======================================================
    # Search Summary
    # ======================================================

    def summary(self, query):

        results = self.search(query)

        return {

            "query": query,

            "count": len(results),

            "featured": self.featured(query),

            "did_you_mean": self.suggest(query),

            "time": SESSION.get(

                "time",

                0

            )

        }


logger.info(
    "Search Controller V5 Part 4 Loaded"
)
# ==========================================================
# Search Controller V5
# Part 5
# Trending + Analytics + Performance
# ==========================================================

from collections import Counter


# ==========================================================
# Search Analytics
# ==========================================================

SEARCH_COUNTER = Counter()

ZERO_RESULT_COUNTER = Counter()


    # ======================================================
    # Record Search
    # ======================================================

    def record_search(self, query):

        query = query.strip().lower()

        if not query:

            return

        SEARCH_COUNTER[query] += 1

    # ======================================================
    # Record Zero Result
    # ======================================================

    def record_zero_result(self, query):

        query = query.strip().lower()

        if not query:

            return

        ZERO_RESULT_COUNTER[query] += 1

    # ======================================================
    # Top Searches
    # ======================================================

    def top_searches(self, limit=10):

        return SEARCH_COUNTER.most_common(limit)

    # ======================================================
    # Zero Result Searches
    # ======================================================

    def zero_result_searches(self, limit=10):

        return ZERO_RESULT_COUNTER.most_common(limit)

    # ======================================================
    # Trending Searches
    # ======================================================

    def trending_searches(self):

        trending_list = []

        for keyword, count in self.top_searches(20):

            trending_list.append({

                "keyword": keyword,

                "count": count

            })

        return trending_list

    # ======================================================
    # Search Performance
    # ======================================================

    def performance(self):

        return {

            "total_searches": sum(

                SEARCH_COUNTER.values()

            ),

            "cached_queries": len(

                SEARCH_CACHE

            ),

            "recent_queries": len(

                RECENT_SEARCHES

            ),

            "history_size": len(

                SEARCH_HISTORY

            ),

            "zero_result_queries": sum(

                ZERO_RESULT_COUNTER.values()

            )

        }

    # ======================================================
    # Search Dashboard
    # ======================================================

    def dashboard(self):

        return {

            "top_searches":

                self.top_searches(),

            "trending":

                self.trending_searches(),

            "performance":

                self.performance(),

            "recent":

                self.recent()

        }

# ======================================================
# Keyboard Navigation
# ======================================================

    def keyboard_navigation(self, key):

        if not self.last_results:

            return None

        current = SESSION.get("selected_index", 0)

        if key == "ArrowDown":

            current += 1

        elif key == "ArrowUp":

            current -= 1

        elif key == "Home":

            current = 0

        elif key == "End":

            current = len(self.last_results) - 1

        current = max(

            0,

            min(current, len(self.last_results) - 1)

        )

        SESSION["selected_index"] = current

        return self.last_results[current]

    # ======================================================
    # Selected Result
    # ======================================================

    def selected_result(self):

        if not self.last_results:

            return None

        index = SESSION.get(

            "selected_index",

            0

        )

        if index >= len(self.last_results):

            index = 0

        return self.last_results[index]

    # ======================================================
    # Reset Selection
    # ======================================================

    def reset_selection(self):

        SESSION["selected_index"] = 0

    # ======================================================
    # Focus Search
    # ======================================================

    def focus_search(self):

        SESSION["search_focus"] = True

    # ======================================================
    # Blur Search
    # ======================================================

    def blur_search(self):

        SESSION["search_focus"] = False

    # ======================================================
    # Search Focus Status
    # ======================================================

    def has_focus(self):

        return SESSION.get(

            "search_focus",

            False

        )

    # ======================================================
    # ESC Key
    # ======================================================

    def escape(self):

        self.reset_selection()

        self.blur_search()

        return True
# ======================================================
    # Query Normalizer
    # ======================================================

    def normalize_query(self, query):

        query = query.lower().strip()

        while "  " in query:
            query = query.replace("  ", " ")

        return query

    # ======================================================
    # Spell Correct
    # ======================================================

    def spell_correct(self, query):

        suggestion = did_you_mean(query)

        if suggestion:
            return suggestion

        return query

    # ======================================================
    # Synonym Search
    # ======================================================

    def synonym_query(self, query):

        synonyms = {

            "teacher": "faculty",

            "lecturer": "assistant professor",

            "result": "results",

            "answer key": "answerkey",

            "admit card": "hall ticket",

            "vacancy": "recruitment",

            "job": "recruitment",

            "exam": "examination"

        }

        q = query.lower()

        return synonyms.get(q, query)

    # ======================================================
    # Optimized Query
    # ======================================================

    def optimized_query(self, query):

        query = self.normalize_query(query)

        query = self.spell_correct(query)

        query = self.synonym_query(query)

        return query

    # ======================================================
    # Smart Search
    # ======================================================

    def smart_search(self, query):

        query = self.optimized_query(query)

        return self.search(query)

    # ======================================================
    # Empty Query Check
    # ======================================================

    def is_empty(self, query):

        return len(query.strip()) == 0

    # ======================================================
    # Search Health
    # ======================================================

    def health(self):

        return {

            "cache": len(SEARCH_CACHE),

            "recent": len(RECENT_SEARCHES),

            "history": len(SEARCH_HISTORY),

            "status": "healthy"

        }
# ======================================================
    # Export Session
    # ======================================================

    def export_session(self):

        return {

            "query": SESSION.get("query"),

            "results": SESSION.get("results"),

            "did_you_mean": SESSION.get("did_you_mean"),

            "selected_index": SESSION.get(

                "selected_index",

                0

            ),

            "search_time": SESSION.get(

                "time",

                0

            )

        }

    # ======================================================
    # Reset Session
    # ======================================================

    def reset(self):

        SESSION.clear()

        SESSION.update({

            "query": "",

            "results": [],

            "did_you_mean": "",

            "selected_index": 0,

            "search_focus": False,

            "time": 0

        })

        return True

    # ======================================================
    # Validate Controller
    # ======================================================

    def validate(self):

        try:

            assert isinstance(

                SEARCH_CACHE,

                dict

            )

            assert isinstance(

                RECENT_SEARCHES,

                deque

            )

            assert isinstance(

                SEARCH_HISTORY,

                deque

            )

            return True

        except Exception as error:

            logger.exception(error)

            return False

    # ======================================================
    # Initialize
    # ======================================================

    def initialize(self):

        self.reset()

        logger.info(

            "Search Controller Initialized"

        )

        return self.validate()


# ==========================================================
# Global Controller
# ==========================================================

controller = SearchController()

controller.initialize()

logger.info(
    "Search Controller V5 Loaded Successfully"
)

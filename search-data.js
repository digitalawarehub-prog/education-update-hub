/* ==========================================================
   Search Data V4
   Part 1 : Configuration + Helpers
========================================================== */

"use strict";

/* Global Search Database */

window.SEARCH_DATA = window.SEARCH_DATA || [];

/* ==========================================================
   Configuration
========================================================== */

const SEARCH_CONFIG = {

    minLength: 2,

    maxResults: 15,

    highlight: true,

    caseSensitive: false,

    latestFirst: true

};

/* ==========================================================
   Safe String
========================================================== */

function safe(value) {

    if (value === undefined || value === null) {

        return "";

    }

    return String(value).trim();

}

/* ==========================================================
   Normalize Text
========================================================== */

function normalize(text) {

    text = safe(text);

    if (!SEARCH_CONFIG.caseSensitive) {

        text = text.toLowerCase();

    }

    return text;

}

/* ==========================================================
   Highlight Keyword
========================================================== */

function highlight(text, keyword) {

    if (!SEARCH_CONFIG.highlight) {

        return text;

    }

    keyword = normalize(keyword);

    if (!keyword) {

        return text;

    }

    return text.replace(

        new RegExp(keyword, "ig"),

        function(match) {

            return `<mark>${match}</mark>`;

        }

    );

}

/* ==========================================================
   Validate Search Record
========================================================== */

function validRecord(record) {

    return (

        record &&

        record.title &&

        record.url

    );

}

console.log("Search Data V4 Part 1 Loaded");
/* ==========================================================
   Search Data V4
   Part 2 : Search Index + Sorting + Category Filter
========================================================== */

/* ==========================================================
   Remove Duplicate Records
========================================================== */

function removeDuplicates(records) {

    const unique = [];
    const seen = new Set();

    records.forEach(record => {

        if (!validRecord(record)) return;

        const key = normalize(record.url);

        if (seen.has(key)) return;

        seen.add(key);

        unique.push(record);

    });

    return unique;

}

/* ==========================================================
   Sort Search Records
========================================================== */

function sortRecords(records) {

    return records.sort((a, b) => {

        if (SEARCH_CONFIG.latestFirst) {

            const da = new Date(a.publish_date || 0);
            const db = new Date(b.publish_date || 0);

            if (db - da !== 0) {

                return db - da;

            }

        }

        return normalize(a.title)
            .localeCompare(normalize(b.title));

    });

}

/* ==========================================================
   Category Filter
========================================================== */

function filterCategory(records, category) {

    category = normalize(category);

    if (!category) {

        return records;

    }

    return records.filter(record =>

        normalize(record.category)
        .includes(category)

    );

}

/* ==========================================================
   Build Search Index
========================================================== */

function buildIndex() {

    window.SEARCH_DATA = sortRecords(

        removeDuplicates(

            window.SEARCH_DATA

        )

    );

    console.log(

        "Indexed Records :",

        window.SEARCH_DATA.length

    );

}

/* ==========================================================
   Initialize
========================================================== */

buildIndex();

console.log(
    "Search Data V4 Part 2 Loaded"
);
/* ==========================================================
   Search Data V4
   Part 3 : Fast Search + Relevance Engine
========================================================== */

/* ==========================================================
   Calculate Search Score
========================================================== */

function calculateScore(record, query) {

    query = normalize(query);

    let score = 0;

    const title = normalize(record.title);
    const description = normalize(record.description);
    const category = normalize(record.category);
    const keywords = normalize(
        (record.keywords || []).join(" ")
    );

    // Exact Match
    if (title === query) {

        score += 100;

    }

    // Title Match
    if (title.includes(query)) {

        score += 60;

    }

    // Category Match
    if (category.includes(query)) {

        score += 30;

    }

    // Description Match
    if (description.includes(query)) {

        score += 20;

    }

    // Keywords Match
    if (keywords.includes(query)) {

        score += 15;

    }

    return score;

}


/* ==========================================================
   Search Records
========================================================== */

function searchRecords(query, category = "") {

    query = normalize(query);

    if (query.length < SEARCH_CONFIG.minLength) {

        return [];

    }

    let records = filterCategory(
        window.SEARCH_DATA,
        category
    );

    let results = [];

    records.forEach(record => {

        const score = calculateScore(
            record,
            query
        );

        if (score > 0) {

            results.push({

                ...record,

                score: score

            });

        }

    });

    results.sort((a, b) =>

        b.score - a.score

    );

    return results.slice(
        0,
        SEARCH_CONFIG.maxResults
    );

}


/* ==========================================================
   Search Preview
========================================================== */

function previewSearch(query) {

    const results = searchRecords(query);

    console.table(

        results.map(item => ({

            Title: item.title,

            Score: item.score,

            Category: item.category

        }))

    );

    return results;

}

console.log(
    "Search Data V4 Part 3 Loaded"
);
/* ==========================================================
   Search Data V4
   Part 4 : Fuzzy Search + Suggestions
========================================================== */

/* ==========================================================
   Search Synonyms
========================================================== */

const SEARCH_SYNONYMS = {

    "job": ["jobs", "recruitment", "vacancy"],

    "result": ["results", "merit", "scorecard"],

    "admit": ["admit card", "hall ticket"],

    "answer": ["answer key", "key"],

    "scholarship": ["scheme"],

    "ctet": ["teacher eligibility"],

    "utet": ["uttarakhand tet"]

};


/* ==========================================================
   Expand Query
========================================================== */

function expandQuery(query) {

    query = normalize(query);

    let words = query.split(/\s+/);

    let expanded = [...words];

    words.forEach(word => {

        if (SEARCH_SYNONYMS[word]) {

            expanded.push(...SEARCH_SYNONYMS[word]);

        }

    });

    return [...new Set(expanded)];

}


/* ==========================================================
   Fuzzy Match
========================================================== */

function fuzzyMatch(text, query) {

    text = normalize(text);

    query = normalize(query);

    if (!text || !query) {

        return false;

    }

    return text.includes(query) ||

           query.includes(text);

}


/* ==========================================================
   Smart Search
========================================================== */

function smartSearch(query, category = "") {

    const expanded = expandQuery(query);

    let results = [];

    filterCategory(
        window.SEARCH_DATA,
        category
    ).forEach(record => {

        let score = 0;

        expanded.forEach(word => {

            if (
                fuzzyMatch(
                    record.title,
                    word
                )
            ) score += 50;

            if (
                fuzzyMatch(
                    record.description,
                    word
                )
            ) score += 20;

            if (
                fuzzyMatch(
                    record.category,
                    word
                )
            ) score += 15;

            if (
                (record.keywords || [])
                .join(" ")
                .toLowerCase()
                .includes(word)
            ) score += 10;

        });

        if (score > 0) {

            results.push({

                ...record,

                score

            });

        }

    });

    results.sort(
        (a, b) => b.score - a.score
    );

    return results.slice(
        0,
        SEARCH_CONFIG.maxResults
    );

}


/* ==========================================================
   Search Suggestions
========================================================== */

function searchSuggestions(query) {

    query = normalize(query);

    if (!query) {

        return [];

    }

    let suggestions = [];

    window.SEARCH_DATA.forEach(record => {

        if (
            normalize(record.title)
            .startsWith(query)
        ) {

            suggestions.push(record.title);

        }

    });

    return [...new Set(suggestions)]
        .slice(0, 8);

}

console.log(
    "Search Data V4 Part 4 Loaded"
);
/* ==========================================================
   Search Data V4
   Part 5 : Cache + Recent Searches + Trending
========================================================== */

/* ==========================================================
   Search Cache
========================================================== */

const SEARCH_CACHE = new Map();

/* ==========================================================
   Recent Searches
========================================================== */

const RECENT_SEARCHES = [];

const MAX_RECENT_SEARCHES = 10;

/* ==========================================================
   Trending Keywords
========================================================== */

const TRENDING_SEARCHES = {};

/* ==========================================================
   Save Search
========================================================== */

function saveRecentSearch(query) {

    query = normalize(query);

    if (!query) return;

    const index = RECENT_SEARCHES.indexOf(query);

    if (index !== -1) {

        RECENT_SEARCHES.splice(index, 1);

    }

    RECENT_SEARCHES.unshift(query);

    if (RECENT_SEARCHES.length > MAX_RECENT_SEARCHES) {

        RECENT_SEARCHES.pop();

    }

    TRENDING_SEARCHES[query] =
        (TRENDING_SEARCHES[query] || 0) + 1;

}

/* ==========================================================
   Cached Search
========================================================== */

function cachedSearch(query, category = "") {

    const cacheKey =
        normalize(query) + "|" + normalize(category);

    if (SEARCH_CACHE.has(cacheKey)) {

        return SEARCH_CACHE.get(cacheKey);

    }

    const results = smartSearch(query, category);

    SEARCH_CACHE.set(cacheKey, results);

    saveRecentSearch(query);

    return results;

}

/* ==========================================================
   Get Recent Searches
========================================================== */

function getRecentSearches() {

    return [...RECENT_SEARCHES];

}

/* ==========================================================
   Get Trending Searches
========================================================== */

function getTrendingSearches(limit = 10) {

    return Object.entries(TRENDING_SEARCHES)

        .sort((a, b) => b[1] - a[1])

        .slice(0, limit)

        .map(item => item[0]);

}

/* ==========================================================
   Clear Cache
========================================================== */

function clearSearchCache() {

    SEARCH_CACHE.clear();

    console.log(
        "Search cache cleared."
    );

}

console.log(
    "Search Data V4 Part 5 Loaded"
);
/* ==========================================================
   Search Data V4
   Part 6 : Initialization + Validation + Statistics
========================================================== */

/* ==========================================================
   Validate Search Database
========================================================== */

function validateSearchData() {

    let valid = 0;
    let invalid = 0;

    window.SEARCH_DATA.forEach(record => {

        if (validRecord(record)) {

            valid++;

        } else {

            invalid++;

        }

    });

    console.log("==================================");
    console.log("Search Database Validation");
    console.log("==================================");
    console.log("Valid Records :", valid);
    console.log("Invalid Records :", invalid);
    console.log("==================================");

}


/* ==========================================================
   Search Statistics
========================================================== */

function searchStatistics() {

    console.log("========== Search Statistics ==========");

    console.log(
        "Total Records :",
        window.SEARCH_DATA.length
    );

    console.log(
        "Recent Searches :",
        RECENT_SEARCHES.length
    );

    console.log(
        "Cache Entries :",
        SEARCH_CACHE.size
    );

    console.log(
        "Trending Keywords :",
        Object.keys(TRENDING_SEARCHES).length
    );

    console.log("=======================================");

}


/* ==========================================================
   Initialize Search Engine
========================================================== */

function initSearchData() {

    buildIndex();

    validateSearchData();

    searchStatistics();

    console.log(
        "Search Data V4 Initialized Successfully."
    );

}


/* ==========================================================
   Reload Search Database
========================================================== */

function reloadSearchData(records) {

    if (!Array.isArray(records)) {

        console.error(
            "Invalid Search Data."
        );

        return;

    }

    window.SEARCH_DATA = records;

    SEARCH_CACHE.clear();

    buildIndex();

    console.log(
        "Search Database Reloaded."
    );

}


/* ==========================================================
   Global Functions
========================================================== */

window.searchRecords = searchRecords;
window.smartSearch = smartSearch;
window.cachedSearch = cachedSearch;
window.searchSuggestions = searchSuggestions;
window.getRecentSearches = getRecentSearches;
window.getTrendingSearches = getTrendingSearches;
window.reloadSearchData = reloadSearchData;


/* ==========================================================
   Auto Initialize
========================================================== */

document.addEventListener(

    "DOMContentLoaded",

    function () {

        initSearchData();

    }

);

console.log(
    "Search Data V4 Loaded Successfully"
);

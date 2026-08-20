/* ==========================================================
   Education Update Hub - Search V6
   Works on homepage + generated/posts/*.html
   ========================================================== */
"use strict";

(() => {
    let searchData = [];
    let searchLoaded = false;
    let initialized = false;

    const ROOT = "/";
    const INDEX_URL = "/search-index.json";
    const FALLBACK_GLOBAL = () => Array.isArray(window.searchData) ? window.searchData : [];

    const get = (...ids) => {
        for (const id of ids) {
            const el = document.getElementById(id);
            if (el) return el;
        }
        return null;
    };

    const input = () => get("searchInput", "searchBox");
    const button = () => get("searchBtn");
    const resultsBox = () => get("searchResults");

    const normalize = value =>
        String(value || "")
            .toLowerCase()
            .replace(/\s+/g, " ")
            .trim();

    const escapeHtml = value =>
        String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    function absoluteUrl(url) {
        if (!url) return "#";

        try {
            if (/^https?:\/\//i.test(url)) {
                return url;
            }

            if (url.startsWith("/")) {
                return url;
            }

            if (url.startsWith("generated/posts/")) {
                return "/" + url;
            }

            return new URL(url, window.location.origin + "/").pathname;
        } catch {
            return "#";
        }
    }

    async function loadSearchIndex() {
        try {
            const response = await fetch(
                INDEX_URL + "?v=" + Date.now(),
                { cache: "no-store" }
            );

            if (!response.ok) {
                throw new Error("HTTP " + response.status);
            }

            const data = await response.json();

            searchData = Array.isArray(data)
                ? data
                : [];

            searchLoaded = true;

            console.log(
                "[Search V6] Index loaded:",
                searchData.length
            );

            return true;
        } catch (error) {
            const fallback = FALLBACK_GLOBAL();
            if (fallback.length) {
                searchData = fallback;
                searchLoaded = true;
                console.warn("[Search V7] Using search-data.js fallback:", fallback.length);
                return true;
            }
            searchLoaded = false;
            console.error("[Search V7] Index load failed:", error);
            return false;
        }
    }

    function score(job, query) {
        const q = normalize(query);

        const fields = {
            title: normalize(job.title),
            category: normalize(job.category),
            department: normalize(job.department),
            description: normalize(job.description),
            state: normalize(job.state),
            keywords: normalize(
                Array.isArray(job.keywords)
                    ? job.keywords.join(" ")
                    : job.keywords
            )
        };

        let value = 0;

        if (fields.title === q) value += 120;
        else if (fields.title.startsWith(q)) value += 90;
        else if (fields.title.includes(q)) value += 70;

        if (fields.category.includes(q)) value += 30;
        if (fields.department.includes(q)) value += 25;
        if (fields.state.includes(q)) value += 20;
        if (fields.description.includes(q)) value += 15;
        if (fields.keywords.includes(q)) value += 20;

        // Token match: useful for multi-word searches.
        const tokens = q.split(" ").filter(Boolean);

        for (const token of tokens) {
            if (fields.title.includes(token)) value += 12;
            if (fields.description.includes(token)) value += 5;
            if (fields.keywords.includes(token)) value += 6;
        }

        return value;
    }

    function searchPosts(query) {
        const q = normalize(query);

        if (!searchLoaded) {
            return [];
        }

        if (q.length < 2) {
            renderResults([]);
            return [];
        }

        const seen = new Set();
        const results = [];

        for (const job of searchData) {
            const url = absoluteUrl(job.url);
            const s = score(job, q);

            if (s <= 0 || seen.has(url)) {
                continue;
            }

            seen.add(url);

            results.push({
                ...job,
                url,
                _score: s
            });
        }

        results.sort((a, b) => b._score - a._score);

        renderResults(results.slice(0, 20));

        return results;
    }

    function renderResults(results) {
        const box = resultsBox();

        if (!box) return;

        box.innerHTML = "";

        if (!results.length) {
            box.innerHTML = `
                <div class="search-no-result">
                    No matching result found
                </div>
            `;
            return;
        }

        const fragment = document.createDocumentFragment();

        results.forEach(job => {
            const link = document.createElement("a");

            link.className = "search-result-card";
            link.href = job.url;

            link.innerHTML = `
                <div class="search-result-content">
                    <h3>${escapeHtml(job.title)}</h3>
                    <span class="search-result-category">
                        ${escapeHtml(job.category || "Latest Jobs")}
                    </span>
                    <p>
                        ${escapeHtml(
                            String(job.description || "")
                                .substring(0, 160)
                        )}
                    </p>
                </div>
            `;

            fragment.appendChild(link);
        });

        box.appendChild(fragment);
    }

    function hideResults() {
        const box = resultsBox();
        if (box) box.innerHTML = "";
    }

    function initializeSearch() {
        const field = input();
        const btn = button();

        if (!field || initialized) {
            return;
        }

        initialized = true;

        field.addEventListener("input", () => {
            searchPosts(field.value);
        });

        field.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                event.preventDefault();
                searchPosts(field.value);
            }

            if (event.key === "Escape") {
                field.value = "";
                hideResults();
            }
        });

        if (btn) {
            btn.addEventListener("click", event => {
                event.preventDefault();
                searchPosts(field.value);
            });
        }

        document.addEventListener("click", event => {
            const wrapper =
                field.closest(".search-box") ||
                field.closest(".search-wrapper");

            if (
                wrapper &&
                !wrapper.contains(event.target)
            ) {
                hideResults();
            }
        });

        console.log("[Search V6] Initialized");
    }

    window.initializeSearch = initializeSearch;

    // Search index can load independently of header timing.
    loadSearchIndex();

    // Header is injected by load.js.
    document.addEventListener(
        "DOMContentLoaded",
        () => {
            initializeSearch();
        }
    );

    window.addEventListener(
        "load",
        () => {
            initializeSearch();
            setTimeout(initializeSearch, 250);
            setTimeout(initializeSearch, 1000);
        }
    );

    document.addEventListener(
        "layoutReady",
        () => {
            initializeSearch();
        }
    );

    document.addEventListener(
        "layoutLoaded",
        () => {
            initializeSearch();
        }
    );
})();

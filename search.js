/* ==========================================================
   Education Update Hub - Search V8
   Single, reliable search engine for all pages
   ========================================================== */
"use strict";

(() => {
    if (window.__EUH_SEARCH_V8__) return;
    window.__EUH_SEARCH_V8__ = true;

    const INDEX_URL = "/search-index.json";
    let searchData = [];
    let searchReady = false;

    const get = id => document.getElementById(id);

    function normalize(value) {
        return String(value || "")
            .toLowerCase()
            .normalize("NFKC")
            .replace(/[–—]/g, "-")
            .replace(/\s+/g, " ")
            .trim();
    }

    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function absoluteUrl(url) {
        const value = String(url || "").trim();
        if (!value) return "#";
        if (/^https?:\/\//i.test(value)) return value;
        if (value.startsWith("/")) return value;
        return "/" + value.replace(/^\/+/, "");
    }

    function currentElements() {
        return {
            input: get("searchBox") || get("searchInput"),
            button: get("searchBtn"),
            panel: get("searchPanel"),
            results: get("searchResults"),
            status: get("searchStatus"),
            count: get("searchCount"),
            empty: get("emptySearch"),
            wrapper: get("siteSearch")
        };
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

            if (!Array.isArray(data)) {
                throw new Error("Invalid search index");
            }

            searchData = data.filter(item => item && item.title);
            searchReady = true;
            updateStatus(searchData.length + " पोस्ट सर्च के लिए उपलब्ध हैं।");
            return true;
        } catch (error) {
            // search-data.js is a local fallback for GitHub Pages/CDN cases
            // where search-index.json is temporarily unavailable.
            const fallback = Array.isArray(window.searchData)
                ? window.searchData
                : [];

            if (fallback.length) {
                searchData = fallback.filter(item => item && item.title);
                searchReady = true;
                updateStatus(searchData.length + " पोस्ट सर्च के लिए उपलब्ध हैं।");
                console.warn("[Search V8] JSON failed; fallback loaded.", error);
                return true;
            }

            searchReady = false;
            updateStatus("Search database उपलब्ध नहीं है।");
            console.error("[Search V8] Index load failed:", error);
            return false;
        }
    }

    function updateStatus(text) {
        const { status } = currentElements();
        if (status) status.textContent = text;
    }

    function score(item, query) {
        const q = normalize(query);

        const fields = {
            title: normalize(item.title),
            category: normalize(item.category),
            department: normalize(item.department),
            state: normalize(item.state),
            description: normalize(item.description),
            keywords: normalize(
                Array.isArray(item.keywords)
                    ? item.keywords.join(" ")
                    : item.keywords
            )
        };

        let points = 0;

        if (fields.title === q) points += 200;
        else if (fields.title.startsWith(q)) points += 120;
        else if (fields.title.includes(q)) points += 90;

        if (fields.category.includes(q)) points += 45;
        if (fields.department.includes(q)) points += 35;
        if (fields.state.includes(q)) points += 25;
        if (fields.keywords.includes(q)) points += 25;
        if (fields.description.includes(q)) points += 15;

        for (const token of q.split(/\s+/).filter(Boolean)) {
            if (fields.title.includes(token)) points += 20;
            if (fields.category.includes(token)) points += 10;
            if (fields.description.includes(token)) points += 5;
            if (fields.keywords.includes(token)) points += 5;
        }

        return points;
    }

    function searchPosts(query) {
        const q = normalize(query);

        if (!searchReady || q.length < 2) {
            return [];
        }

        const seen = new Set();

        return searchData
            .map(item => ({
                item,
                score: score(item, q)
            }))
            .filter(row => row.score > 0)
            .sort((a, b) => b.score - a.score)
            .map(row => row.item)
            .filter(item => {
                const url = absoluteUrl(item.url);
                if (seen.has(url)) return false;
                seen.add(url);
                return true;
            })
            .slice(0, 30);
    }

    function renderResults(query) {
        const { panel, results, count, empty, status } = currentElements();

        if (!results) return;

        const q = normalize(query);

        if (q.length < 2) {
            results.innerHTML = "";
            if (panel) panel.classList.remove("active");
            if (count) count.textContent = "0 Results";
            if (empty) empty.style.display = "none";
            if (status) status.textContent = searchReady
                ? "Search करने के लिए कम से कम 2 अक्षर लिखें।"
                : "Search database लोड हो रहा है...";
            return;
        }

        if (panel) panel.classList.add("active");

        if (!searchReady) {
            results.innerHTML = `
                <div class="search-no-result">
                    Search database लोड हो रहा है, कृपया फिर से प्रयास करें।
                </div>`;
            return;
        }

        const found = searchPosts(q);

        if (count) {
            count.textContent = found.length + " Result" +
                (found.length === 1 ? "" : "s");
        }

        if (!found.length) {
            results.innerHTML = `
                <div class="search-no-result">
                    🔍 "${escapeHtml(query)}" के लिए कोई परिणाम नहीं मिला।
                </div>`;
            if (empty) empty.style.display = "none";
            if (status) status.textContent = "कोई matching post नहीं मिली।";
            return;
        }

        if (empty) empty.style.display = "none";
        if (status) status.textContent = "Search results";

        results.innerHTML = found.map(item => {
            const url = absoluteUrl(item.url);
            return `
                <a class="search-result-card" href="${escapeHtml(url)}">
                    <div class="search-result-content">
                        <h3>${escapeHtml(item.title)}</h3>
                        <span class="search-result-category">
                            ${escapeHtml(item.category || "Education Update")}
                        </span>
                        <p>${escapeHtml(
                            String(item.description || "").substring(0, 180)
                        )}</p>
                    </div>
                </a>`;
        }).join("");
    }

    function initSearch() {
        const { input, button, wrapper } = currentElements();

        if (!input || input.dataset.searchV8Bound === "1") {
            return false;
        }

        input.dataset.searchV8Bound = "1";

        input.addEventListener("input", () => {
            renderResults(input.value);
        });

        input.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                event.preventDefault();
                renderResults(input.value);
            }

            if (event.key === "Escape") {
                input.value = "";
                renderResults("");
            }
        });

        if (button) {
            button.addEventListener("click", event => {
                event.preventDefault();
                renderResults(input.value);
                input.focus();
            });
        }

        document.addEventListener("click", event => {
            const { panel } = currentElements();
            if (wrapper && !wrapper.contains(event.target) && panel) {
                panel.classList.remove("active");
            }
        });

        console.log("[Search V8] Initialized");
        return true;
    }

    window.initializeSearch = initSearch;

    // Header is dynamically inserted by load.js.
    // Try immediately, then again after layout injection.
    initSearch();

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initSearch);
    }

    document.addEventListener("layoutReady", initSearch);
    document.addEventListener("layoutLoaded", initSearch);

    window.addEventListener("load", () => {
        initSearch();
        setTimeout(initSearch, 250);
        setTimeout(initSearch, 1000);
    });

    // Load data independently of DOM/header timing.
    loadSearchIndex();
})();

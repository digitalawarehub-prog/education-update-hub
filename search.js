/* ==========================================================
   Education Update Hub - Search FINAL
   Works after header.html is injected by load.js and on all pages.
   ========================================================== */
"use strict";

(() => {
    const INDEX_URL = "/search-index.json";
    const FALLBACK_URL = "/search-data.js";
    let indexPromise = null;

    const $ = id => document.getElementById(id);

    const normalize = value => String(value || "")
        .toLowerCase()
        .replace(/\s+/g, " ")
        .trim();

    const escapeHtml = value => String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    function absoluteUrl(url) {
        if (!url) return "#";
        try {
            if (/^https?:\/\//i.test(url)) return url;
            if (url.startsWith("/")) return url;
            return "/" + url.replace(/^\/+/, "");
        } catch (_) {
            return "#";
        }
    }

    const HINDI = {
        recruitment: "भर्ती", vacancy: "रिक्ति", notification: "अधिसूचना",
        "admit card": "प्रवेश पत्र", result: "परिणाम", "answer key": "उत्तर कुंजी",
        syllabus: "पाठ्यक्रम", scholarship: "छात्रवृत्ति", exam: "परीक्षा",
        jobs: "नौकरी", job: "नौकरी", application: "आवेदन", "apply online": "ऑनलाइन आवेदन",
        uttarakhand: "उत्तराखंड", patwari: "पटवारी", lekhpal: "लेखपाल",
        railway: "रेलवे", banking: "बैंकिंग", teacher: "शिक्षक", police: "पुलिस",
        forest: "वन"
    };

    function expand(value) {
        let text = normalize(value);
        for (const [en, hi] of Object.entries(HINDI)) {
            if (text.includes(en)) text += " " + hi;
        }
        return text;
    }

    async function loadIndex() {
        if (indexPromise) return indexPromise;

        indexPromise = fetch(INDEX_URL + "?v=" + Date.now(), { cache: "no-store" })
            .then(r => {
                if (!r.ok) throw new Error("HTTP " + r.status);
                return r.json();
            })
            .then(data => {
                if (!Array.isArray(data) || !data.length) throw new Error("Empty index");
                return data.filter(x => x && x.title && x.url);
            })
            .catch(async () => {
                const r = await fetch(FALLBACK_URL + "?v=" + Date.now(), { cache: "no-store" });
                if (!r.ok) throw new Error("Fallback HTTP " + r.status);
                const text = await r.text();
                const m = text.match(/const\s+searchData\s*=\s*([\s\S]*);\s*$/);
                if (!m) throw new Error("Invalid search-data.js");
                const data = JSON.parse(m[1]);
                return Array.isArray(data) ? data.filter(x => x && x.title && x.url) : [];
            })
            .catch(error => {
                console.error("[Search] Index load failed", error);
                return [];
            });

        return indexPromise;
    }

    function score(item, query) {
        const q = expand(query);
        if (!q) return 0;

        const fields = [
            [expand(item.title), 100],
            [expand(item.category), 25],
            [expand(item.department), 20],
            [expand(item.state), 20],
            [expand(item.description), 12],
            [expand(Array.isArray(item.keywords) ? item.keywords.join(" ") : item.keywords), 18]
        ];

        let points = 0;
        const tokens = q.split(" ").filter(Boolean);

        for (const [value, weight] of fields) {
            if (!value) continue;
            if (value === q) points += weight + 40;
            else if (value.startsWith(q)) points += weight + 25;
            else if (value.includes(q)) points += weight;
        }

        for (const token of tokens) {
            if (token.length < 2) continue;
            if (fields[0][0].includes(token)) points += 12;
            else if (fields.some(([value]) => value.includes(token))) points += 4;
        }

        return points;
    }

    async function search(query) {
        const q = normalize(query);
        if (q.length < 2) return [];

        const data = await loadIndex();
        const seen = new Set();
        return data.map(item => ({ item, score: score(item, q) }))
            .filter(x => x.score > 0)
            .sort((a, b) => b.score - a.score)
            .filter(x => {
                const url = absoluteUrl(x.item.url);
                if (seen.has(url)) return false;
                seen.add(url);
                return true;
            })
            .slice(0, 20)
            .map(x => ({ ...x.item, url: absoluteUrl(x.item.url) }));
    }

    function render(results, query) {
        const panel = $("searchPanel");
        const box = $("searchResults");
        const count = $("searchCount");
        const status = $("searchStatus");
        const empty = $("emptySearch");
        if (!panel || !box) return;

        if (normalize(query).length < 2) {
            panel.classList.remove("active");
            box.innerHTML = "";
            if (count) count.textContent = "0 Results";
            if (empty) empty.style.display = "none";
            if (status) status.textContent = "Start typing to search...";
            return;
        }

        panel.classList.add("active");
        if (count) count.textContent = results.length + (results.length === 1 ? " Result" : " Results");

        if (!results.length) {
            box.innerHTML = "";
            if (empty) empty.style.display = "block";
            if (status) status.textContent = "No matching post found.";
            return;
        }

        if (empty) empty.style.display = "none";
        if (status) status.textContent = "Search results";

        box.innerHTML = results.map(item => `
            <a class="search-result-card" href="${escapeHtml(item.url)}">
                <div class="search-result-content">
                    <h4>${escapeHtml(item.title)}</h4>
                    <span class="search-category">${escapeHtml(item.category || "Education Update")}</span>
                    <p>${escapeHtml(String(item.description || "").slice(0, 180))}</p>
                </div>
            </a>
        `).join("");
    }

    function bindSearch() {
        const input = $("searchBox") || $("searchInput");
        if (!input || input.dataset.searchBound === "1") return;
        input.dataset.searchBound = "1";

        const button = $("searchBtn");
        const clear = $("clearSearch");

        const run = async () => {
            const query = input.value;
            const panel = $("searchPanel");
            const status = $("searchStatus");
            if (normalize(query).length >= 2 && status) status.textContent = "Searching...";
            const results = await search(query);
            render(results, query);
            if (panel && normalize(query).length >= 2) panel.classList.add("active");
        };

        input.addEventListener("input", run);
        input.addEventListener("keydown", e => {
            if (e.key === "Enter") { e.preventDefault(); run(); }
            if (e.key === "Escape") { input.value = ""; render([], ""); }
        });

        if (button && button.dataset.searchBound !== "1") {
            button.dataset.searchBound = "1";
            button.addEventListener("click", e => { e.preventDefault(); run(); });
        }

        if (clear && clear.dataset.searchBound !== "1") {
            clear.dataset.searchBound = "1";
            clear.addEventListener("click", () => { input.value = ""; render([], ""); input.focus(); });
        }

        document.addEventListener("click", e => {
            const wrapper = input.closest(".search-wrapper");
            const panel = $("searchPanel");
            if (wrapper && panel && !wrapper.contains(e.target)) panel.classList.remove("active");
        });

        loadIndex();
        console.log("[Search FINAL] Ready");
    }

    window.initializeSearch = bindSearch;

    document.addEventListener("DOMContentLoaded", bindSearch);
    window.addEventListener("load", bindSearch);
    document.addEventListener("layoutReady", bindSearch);
    document.addEventListener("layoutLoaded", bindSearch);
})();

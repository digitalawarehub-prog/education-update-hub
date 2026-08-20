/* Education Update Hub - Search V8
   Works after load.js injects header.html and on generated posts. */
"use strict";
(() => {
  let INDEX = [];
  let INDEX_READY = false;
  let INITIALIZED = false;

  const $ = id => document.getElementById(id);
  const normalize = v => String(v || "").toLowerCase().normalize("NFKC").replace(/[–—]/g, "-").replace(/\s+/g, " ").trim();
  const escapeHtml = v => String(v || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");

  function urlFor(item) {
    const raw = item && (item.url || item.html_file);
    if (!raw) return "#";
    try {
      return new URL(raw, window.location.origin + "/").pathname;
    } catch (_) {
      return "#";
    }
  }

  const HINDI = {
    recruitment:"भर्ती", vacancy:"रिक्ति", notification:"अधिसूचना", "admit card":"प्रवेश पत्र",
    result:"परिणाम", "answer key":"उत्तर कुंजी", syllabus:"पाठ्यक्रम", scholarship:"छात्रवृत्ति",
    exam:"परीक्षा", job:"नौकरी", jobs:"नौकरियां", teacher:"शिक्षक", police:"पुलिस", forest:"वन",
    uttarakhand:"उत्तराखंड", application:"आवेदन", "apply online":"ऑनलाइन आवेदन", patwari:"पटवारी",
    lekhpal:"लेखपाल", railway:"रेलवे", banking:"बैंकिंग", bank:"बैंक", upsc:"यूपीएससी", ssc:"एसएससी"
  };

  function expanded(v) {
    let t = normalize(v);
    for (const [en, hi] of Object.entries(HINDI)) {
      if (t.includes(en)) t += " " + hi;
    }
    return t;
  }

  function score(item, query) {
    const q = normalize(query);
    const fields = {
      title: expanded(item.title),
      category: expanded(item.category),
      department: expanded(item.department),
      state: expanded(item.state),
      description: expanded(item.description),
      keywords: expanded(Array.isArray(item.keywords) ? item.keywords.join(" ") : item.keywords)
    };
    let s = 0;
    if (fields.title === q) s += 200;
    else if (fields.title.startsWith(q)) s += 130;
    else if (fields.title.includes(q)) s += 100;
    if (fields.category.includes(q)) s += 45;
    if (fields.department.includes(q)) s += 35;
    if (fields.state.includes(q)) s += 25;
    if (fields.keywords.includes(q)) s += 30;
    if (fields.description.includes(q)) s += 15;
    for (const token of q.split(" ").filter(Boolean)) {
      if (fields.title.includes(token)) s += 18;
      if (fields.keywords.includes(token)) s += 8;
      if (fields.description.includes(token)) s += 5;
    }
    return s;
  }

  async function loadIndex() {
    try {
      const r = await fetch("/search-index.json?v=" + Date.now(), {cache:"no-store"});
      if (!r.ok) throw new Error("HTTP " + r.status);
      const data = await r.json();
      INDEX = Array.isArray(data) ? data.filter(x => x && x.title && urlFor(x) !== "#") : [];
      INDEX_READY = INDEX.length > 0;
    } catch (e) {
      try {
        const r = await fetch("/search-data.js?v=" + Date.now(), {cache:"no-store"});
        const text = await r.text();
        const m = text.match(/const\s+searchData\s*=\s*([\s\S]*);\s*$/);
        if (!m) throw new Error("Invalid search-data.js");
        const data = JSON.parse(m[1]);
        INDEX = Array.isArray(data) ? data.filter(x => x && x.title && urlFor(x) !== "#") : [];
        INDEX_READY = INDEX.length > 0;
      } catch (e2) {
        INDEX = [];
        INDEX_READY = false;
        console.error("[Search V8] Index load failed", e2);
      }
    }
    const status = $("searchStatus");
    if (status) status.textContent = INDEX_READY ? `${INDEX.length} posts available for search.` : "Search database is temporarily unavailable.";
  }

  function render(query) {
    const input = $("searchBox") || $("searchInput");
    const panel = $("searchPanel");
    const box = $("searchResults");
    const count = $("searchCount");
    const empty = $("emptySearch");
    if (!box) return;
    const q = normalize(query || (input && input.value));
    if (q.length < 2) {
      if (panel) panel.classList.remove("active");
      box.innerHTML = "";
      if (count) count.textContent = "0 Results";
      if (empty) empty.style.display = "none";
      return;
    }
    if (panel) panel.classList.add("active");
    if (!INDEX_READY) {
      box.innerHTML = "<div class='search-no-result'>Search database is loading…</div>";
      return;
    }
    const seen = new Set();
    const results = INDEX.map(item => ({item, s: score(item, q)}))
      .filter(x => x.s > 0)
      .sort((a,b) => b.s - a.s)
      .map(x => x.item)
      .filter(item => {
        const u = urlFor(item);
        if (seen.has(u)) return false;
        seen.add(u); return true;
      })
      .slice(0, 30);

    if (count) count.textContent = `${results.length} Result${results.length === 1 ? "" : "s"}`;
    if (!results.length) {
      box.innerHTML = "<div class='search-no-result'>No matching result found</div>";
      if (empty) empty.style.display = "block";
      return;
    }
    if (empty) empty.style.display = "none";
    box.innerHTML = results.map(item => {
      const url = urlFor(item);
      return `<a class="search-result-item search-result-card" href="${escapeHtml(url)}"><span class="search-result-category">${escapeHtml(item.category || "Update")}</span><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(String(item.description || "").slice(0,160))}</p></a>`;
    }).join("");
  }

  function initialize() {
    const input = $("searchBox") || $("searchInput");
    if (!input || INITIALIZED) return;
    INITIALIZED = true;
    const button = $("searchBtn");
    const clear = $("clearSearch");
    input.addEventListener("input", () => render(input.value));
    input.addEventListener("keydown", e => {
      if (e.key === "Enter") { e.preventDefault(); render(input.value); }
      if (e.key === "Escape") { input.value = ""; render(""); }
    });
    if (button) button.addEventListener("click", e => { e.preventDefault(); render(input.value); });
    if (clear) clear.addEventListener("click", () => { input.value = ""; render(""); input.focus(); });
    document.addEventListener("click", e => {
      const wrapper = $("siteSearch") || input.closest(".search-wrapper") || input.closest(".search-box");
      if (wrapper && !wrapper.contains(e.target)) {
        const panel = $("searchPanel"); if (panel) panel.classList.remove("active");
      }
    });
    console.log("[Search V8] Initialized");
  }

  window.initializeSearch = initialize;
  loadIndex();
  document.addEventListener("DOMContentLoaded", initialize);
  window.addEventListener("load", initialize);
  document.addEventListener("layoutReady", initialize);
  document.addEventListener("layoutLoaded", initialize);

  // Extra safety: load.js injects the header asynchronously.
  const observer = new MutationObserver(() => initialize());
  observer.observe(document.documentElement, {childList:true, subtree:true});
})();

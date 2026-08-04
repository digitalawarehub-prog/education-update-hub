/* ==========================================================
   Education Update Hub
   Search V5.2 Professional
   Part 1 : Configuration + Loader + Helpers
========================================================== */

"use strict";

// ============================================
// Global Variables
// ============================================

let searchData = [];
let filteredResults = [];
let selectedIndex = -1;
let searchLoaded = false;

// ============================================
// DOM Helper
// ============================================

function $(id) {
    return document.getElementById(id);
}

// ============================================
// Normalize Text
// ============================================

function normalize(text) {

    return String(text || "")
        .toLowerCase()
        .trim();

}

// ============================================
// Escape HTML
// ============================================

function escapeHtml(text) {

    return String(text || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");

}

// ============================================
// Fetch Search Index
// ============================================

async function loadSearchIndex() {

    try {

        const response =
            await fetch(
                "search-index.json",
                {
                    cache: "no-cache"
                }
            );

        if (!response.ok) {

            throw new Error(
                "Unable to load search-index.json"
            );

        }

        searchData =
            await response.json();

        searchLoaded = true;

        console.log(
            "Search Index Loaded :",
            searchData.length
        );

        const total =
            $("searchTotalPosts");

        if (total) {

            total.textContent =
                searchData.length +
                " Posts Indexed";

        }

    }

    catch (error) {

        console.error(
            "Search Index Error",
            error
        );

        searchLoaded = false;

    }

}

// ============================================
// Clear Search Results
// ============================================

function clearResults() {

    filteredResults = [];

    if ($("searchResults"))
        $("searchResults").innerHTML = "";

    if ($("searchSuggestions"))
        $("searchSuggestions").innerHTML = "";

    if ($("searchCount"))
        $("searchCount").textContent =
            "0 Results";

    if ($("searchStatus"))
        $("searchStatus").textContent =
            "Start typing to search...";

}

// ============================================
// Open Search Panel
// ============================================

function openSearchPanel() {

    $("searchPanel")
        ?.classList
        .add("active");

}

// ============================================
// Close Search Panel
// ============================================

function closeSearchPanel() {

    $("searchPanel")
        ?.classList
        .remove("active");

}

// ============================================
// Console
// ============================================

console.log(
    "Search V5.2 Part 1 Loaded"
);
// ==========================================================
// Search Engine
// Part 2 : Filtering + Ranking
// ==========================================================

// ============================================
// Score Result
// ============================================

function scoreResult(job, query) {

    query = normalize(query);

    let score = 0;

    const title =
        normalize(job.title);

    const category =
        normalize(job.category);

    const department =
        normalize(job.department);

    const description =
        normalize(job.description);

    if (title === query)
        score += 100;

    if (title.startsWith(query))
        score += 80;

    if (title.includes(query))
        score += 60;

    if (category.includes(query))
        score += 25;

    if (department.includes(query))
        score += 20;

    if (description.includes(query))
        score += 10;

    return score;

}

// ============================================
// Search Engine
// ============================================

function searchPosts(query) {

    query = normalize(query);

    if (!searchLoaded) {

        console.warn(
            "Search Index Not Loaded"
        );

        return [];

    }

    if (query.length < 2) {

        clearResults();

        return [];

    }

    const results = [];

    const seen = new Set();

    for (const job of searchData) {

        const title =
            normalize(job.title);

        const category =
            normalize(job.category);

        const department =
            normalize(job.department);

        const description =
            normalize(job.description);

        if (

            title.includes(query)

            ||

            category.includes(query)

            ||

            department.includes(query)

            ||

            description.includes(query)

        ) {

            const url =
                job.url || "";

            if (seen.has(url))
                continue;

            seen.add(url);

            job._score =
                scoreResult(job, query);

            results.push(job);

        }

    }

    results.sort(function(a, b) {

        return b._score - a._score;

    });

    filteredResults = results;

    renderResults(results);

    renderSuggestions(results);

    return results;

}

// ============================================
// Search Count
// ============================================

function updateSearchCount(total) {

    const box =
        $("searchCount");

    if (!box)
        return;

    box.textContent =
        total + " Results";

}

// ============================================
// Search Status
// ============================================

function updateSearchStatus(text) {

    const box =
        $("searchStatus");

    if (!box)
        return;

    box.textContent =
        text;

}

console.log(
    "Search V5.2 Part 2 Loaded"
);
// ==========================================================
// Search V5.2 Professional
// Part 3 : Result Rendering Engine
// ==========================================================

// ============================================
// Empty State
// ============================================

function showEmptyState(show) {

    const empty = $("emptySearch");

    if (!empty) return;

    empty.style.display =
        show ? "block" : "none";

}

// ============================================
// Top Result
// ============================================

function renderTopResult(job) {

    const box = $("topResult");

    if (!box) return;

    if (!job) {

        box.innerHTML = "";

        return;

    }

    box.innerHTML = `

<a href="${job.url}"
class="top-result-card">

<div class="top-result-title">

🏆 ${escapeHtml(job.title)}

</div>

<div class="top-result-meta">

${escapeHtml(job.category)}

</div>

</a>

`;

}

// ============================================
// Result Card
// ============================================

function createResultCard(job) {

    return `

<a
href="${job.url}"
class="search-result-card">

<div class="search-result-image">

<img
src="${job.image || "images/default-job.png"}"
loading="lazy"
alt="${escapeHtml(job.title)}">

</div>

<div class="search-result-content">

<h3>

${escapeHtml(job.title)}

</h3>

<div class="result-badges">

<span class="badge">

${escapeHtml(job.category)}

</span>

</div>

<p>

${escapeHtml(
(job.description || "")
.substring(0,140)
)}

</p>

</div>

</a>

`;

}

// ============================================
// Render Results
// ============================================

function renderResults(results) {

    const container =
        $("searchResults");

    if (!container)
        return;

    container.innerHTML = "";

    updateSearchCount(
        results.length
    );

    if (results.length === 0) {

        updateSearchStatus(
            "No matching result found"
        );

        renderTopResult(null);

        showEmptyState(true);

        return;

    }

    showEmptyState(false);

    updateSearchStatus(
        "Showing best matches"
    );

    renderTopResult(
        results[0]
    );

    results
        .slice(0,20)
        .forEach(job => {

            container.insertAdjacentHTML(

                "beforeend",

                createResultCard(job)

            );

        });

}

// ============================================
// Search Statistics
// ============================================

function updateStatistics() {

    const total =
        $("searchTotalPosts");

    if (
        total &&
        searchLoaded
    ) {

        total.textContent =
            searchData.length +
            " Posts Indexed";

    }

}

console.log(
    "Search V5.2 Part 3 Loaded"
);
// ==========================================================
// Search V5.2 Professional
// Part 4 : Suggestions + Navigation
// ==========================================================

// ============================================
// Render Suggestions
// ============================================

function renderSuggestions(results){

    const box = $("searchSuggestions");

    if(!box) return;

    box.innerHTML = "";

    selectedIndex = -1;

    if(results.length===0){

        box.style.display="none";

        return;

    }

    results.slice(0,8).forEach((job,index)=>{

        const item =
            document.createElement("div");

        item.className="search-item";

        item.dataset.index=index;

        item.innerHTML=`

<div class="search-item-title">

${escapeHtml(job.title)}

</div>

<div class="search-item-meta">

${escapeHtml(job.category)}

</div>

`;

        item.onclick=function(){

            location.href=job.url;

        };

        item.onmouseenter=function(){

            selectedIndex=index;

            highlightSuggestion();

        };

        box.appendChild(item);

    });

    box.style.display="block";

}

// ============================================
// Highlight
// ============================================

function highlightSuggestion(){

    const items=document.querySelectorAll(".search-item");

    items.forEach(item=>{

        item.classList.remove("active");

    });

    if(

        selectedIndex>=0 &&

        selectedIndex<items.length

    ){

        items[selectedIndex]

            .classList.add("active");

    }

}

// ============================================
// Hide Suggestions
// ============================================

function hideSuggestions(){

    const box=$("searchSuggestions");

    if(box){

        box.style.display="none";

    }

}

// ============================================
// Keyboard Navigation
// ============================================

document.addEventListener(

"keydown",

function(e){

const items=

document.querySelectorAll(

".search-item"

);

if(items.length===0)

return;

if(e.key==="ArrowDown"){

e.preventDefault();

selectedIndex++;

if(selectedIndex>=items.length)

selectedIndex=0;

highlightSuggestion();

}

else if(e.key==="ArrowUp"){

e.preventDefault();

selectedIndex--;

if(selectedIndex<0)

selectedIndex=items.length-1;

highlightSuggestion();

}

else if(

e.key==="Enter"

&&

selectedIndex>=0

){

e.preventDefault();

items[selectedIndex].click();

}

}

);

// ============================================
// Open Search Panel
// ============================================

$("searchBox")?.addEventListener(

"focus",

function(){

openSearchPanel();

}

);

// ============================================
// Close Panel Outside Click
// ============================================

document.addEventListener(

"click",

function(e){

const wrapper=

document.querySelector(

".search-wrapper"

);

if(

wrapper &&

!wrapper.contains(e.target)

){

hideSuggestions();

closeSearchPanel();

}

}

);

// ============================================
// Live Search
// ============================================

$("searchBox")?.addEventListener(

"input",

function(){

const value=this.value;

searchPosts(value);

}

);

console.log(

"Search V5.2 Part 4 Loaded"

);
// ==========================================================
// Search V5.2 Professional
// Part 5 : Voice + Recent + Final Init
// ==========================================================

// ============================================
// Save Recent Search
// ============================================

function saveRecentSearch(query){

    query = normalize(query);

    if(!query) return;

    let recent = JSON.parse(
        localStorage.getItem(
            "recentSearches"
        ) || "[]"
    );

    recent = recent.filter(
        x => x !== query
    );

    recent.unshift(query);

    recent = recent.slice(0,10);

    localStorage.setItem(
        "recentSearches",
        JSON.stringify(recent)
    );

}

// ============================================
// Load Recent Search
// ============================================

function loadRecentSearch(){

    const box = $("recentSearchList");

    if(!box) return;

    box.innerHTML = "";

    const recent = JSON.parse(
        localStorage.getItem(
            "recentSearches"
        ) || "[]"
    );

    recent.forEach(text=>{

        const chip =
            document.createElement("span");

        chip.className =
            "search-chip";

        chip.textContent =
            text;

        chip.onclick = function(){

            $("searchBox").value =
                text;

            searchPosts(text);

        };

        box.appendChild(chip);

    });

}

// ============================================
// Voice Search
// ============================================

function startVoiceSearch(){

    if(
        !("webkitSpeechRecognition" in window)
    ){
        alert(
            "Voice Search is not supported."
        );
        return;
    }

    const recognition =
        new webkitSpeechRecognition();

    recognition.lang = "en-IN";

    recognition.start();

    recognition.onresult =
        function(event){

        const text =
            event.results[0][0].transcript;

        $("searchBox").value =
            text;

        searchPosts(text);

    };

}

// ============================================
// Buttons
// ============================================

$("voiceBtn")?.addEventListener(
    "click",
    startVoiceSearch
);

$("clearSearch")?.addEventListener(
    "click",
    function(){

        $("searchBox").value = "";

        clearResults();

        hideSuggestions();

        $("searchBox").focus();

    }
);

$("searchBtn")?.addEventListener(
    "click",
    function(){

        const query =
            $("searchBox").value;

        saveRecentSearch(query);

        loadRecentSearch();

        searchPosts(query);

    }
);

// ============================================
// Did You Mean
// ============================================

function showDidYouMean(text){

    const box =
        $("didYouMean");

    if(!box) return;

    if(!text){

        box.style.display =
            "none";

        return;

    }

    box.innerHTML =
        "Did you mean: <strong>"
        + escapeHtml(text)
        + "</strong>";

    box.style.display =
        "block";

}

// ============================================
// Auto Load
// ============================================

window.addEventListener(
    "load",
    async function(){

        await loadSearchIndex();

        loadRecentSearch();

        updateStatistics();

        console.log(
            "Search V5.2 Ready"
        );

    }
);

console.log(
    "Search V5.2 Final Loaded"
);
function initializeSearch() {

    $("searchBox")?.addEventListener("input", function () {
        searchPosts(this.value);
    });

    $("searchBtn")?.addEventListener("click", function () {
        const query = $("searchBox").value;
        saveRecentSearch(query);
        loadRecentSearch();
        searchPosts(query);
    });

    $("voiceBtn")?.addEventListener("click", startVoiceSearch);

    $("clearSearch")?.addEventListener("click", function () {
        $("searchBox").value = "";
        clearResults();
        hideSuggestions();
    });

}
window.initializeSearch = initializeSearch;

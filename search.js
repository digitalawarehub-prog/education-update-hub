/* ==========================================================
   Search V5 Pro
   Part 5
   Live Search + Suggestions + Keyboard Navigation
========================================================== */

let searchData = [];
let selectedIndex = -1;

// ============================================
// Load Search Index
// ============================================

async function loadSearchIndex() {

    try {

        const response = await fetch("search-index.json");

        searchData = await response.json();

    }

    catch (e) {

        console.error(
            "Search Index Load Failed",
            e
        );

    }

}

// ============================================
// Normalize
// ============================================

function normalize(text){

    return String(text || "")
        .toLowerCase()
        .trim();

}

// ============================================
// Live Suggestions
// ============================================

function searchSuggestions(query){

    query = normalize(query);

    if(query.length < 2){

        hideSuggestions();

        return;

    }

    let results = [];

    for(const job of searchData){

        const title =
            normalize(job.title);

        if(title.includes(query)){

            results.push(job);

        }

        if(results.length >= 8){

            break;

        }

    }

    renderSuggestions(results);

}

// ============================================
// Render Suggestions
// ============================================

function renderSuggestions(items){

    const box =
        document.getElementById(
            "searchSuggestions"
        );

    box.innerHTML = "";

    selectedIndex = -1;

    if(items.length === 0){

        box.style.display = "none";

        return;

    }

    items.forEach((item,index)=>{

        const div =
            document.createElement("div");

        div.className =
            "search-item";

        div.dataset.index = index;

        div.innerHTML =

        `
        <span class="search-title">

        ${item.title}

        </span>

        `;

        div.onclick = ()=>{

            location.href =
            item.url;

        };

        box.appendChild(div);

    });

    box.style.display = "block";

}

// ============================================
// Hide Suggestions
// ============================================

function hideSuggestions(){

    document.getElementById(

        "searchSuggestions"

    ).style.display = "none";

}

// ============================================
// Keyboard Navigation
// ============================================

document.addEventListener(

"keydown",

function(e){

const items =

document.querySelectorAll(

".search-item"

);

if(items.length===0)
return;

if(e.key==="ArrowDown"){

selectedIndex++;

if(selectedIndex>=items.length)
selectedIndex=0;

}

else if(e.key==="ArrowUp"){

selectedIndex--;

if(selectedIndex<0)
selectedIndex=items.length-1;

}

else if(

e.key==="Enter"

&&

selectedIndex>=0

){

items[selectedIndex].click();

}

items.forEach(

x=>x.classList.remove(

"active"

)

);

if(selectedIndex>=0){

items[selectedIndex]

.classList.add(

"active"

);

}

}

);

// ============================================
// Start
// ============================================

window.addEventListener(

"load",

loadSearchIndex

);
/* ==========================================================
   Search V5 Pro
   Part 6
   Voice Search + Did You Mean + Recent Search
========================================================== */

// ============================================
// Voice Search
// ============================================

function startVoiceSearch(){

    if(!('webkitSpeechRecognition' in window)){

        alert("Voice Search is not supported.");

        return;

    }

    const recognition =
        new webkitSpeechRecognition();

    recognition.lang = "en-IN";

    recognition.interimResults = false;

    recognition.maxAlternatives = 1;

    recognition.start();

    recognition.onresult = function(event){

        const text =
            event.results[0][0].transcript;

        const box =
            document.getElementById("searchBox");

        box.value = text;

        searchSuggestions(text);

    };

}

// ============================================
// Save Recent Search
// ============================================

function saveRecentSearch(query){

    query = normalize(query);

    if(!query) return;

    let recent =
        JSON.parse(

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

    return JSON.parse(

        localStorage.getItem(

            "recentSearches"

        ) || "[]"

    );

}

// ============================================
// Did You Mean
// ============================================

function didYouMean(query){

    query = normalize(query);

    let best = null;

    let score = 0;

    for(const job of searchData){

        const title =
            normalize(job.title);

        let s = similarity(

            query,

            title

        );

        if(s > score){

            score = s;

            best = job.title;

        }

    }

    if(score >= 0.60){

        const label =

        document.getElementById(

            "didYouMean"

        );

        label.innerHTML =

        `Did you mean:
        <strong>${best}</strong>`;

        label.style.display = "block";

    }

}

// ============================================
// Similarity
// ============================================

function similarity(a,b){

    a = normalize(a);

    b = normalize(b);

    if(a===b) return 1;

    let same = 0;

    for(let i=0;i<Math.min(a.length,b.length);i++){

        if(a[i]===b[i]){

            same++;

        }

    }

    return same / Math.max(a.length,b.length);

}

// ============================================
// Search Submit
// ============================================

function submitSearch(){

    const query =

    document.getElementById(

        "searchBox"

    ).value;

    saveRecentSearch(query);

    didYouMean(query);

    searchSuggestions(query);

}

// ============================================
// Auto Events
// ============================================

window.addEventListener(

"load",

function(){

const box =

document.getElementById(

"searchBox"

);

if(box){

box.addEventListener(

"keyup",

function(){

submitSearch();

}

);

}

}

);

console.log(

"Search V5 Pro Ready"

);

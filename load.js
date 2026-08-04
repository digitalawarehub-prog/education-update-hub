/* ==========================================================
   Load.js V4
   Part 1 : Configuration + Initialization
========================================================== */

"use strict";

/* ==========================================================
   Configuration
========================================================== */

const LOAD_CONFIG = {

    headerFile: "header.html",

    footerFile: "footer.html",

    timeout: 10000,

    cache: true,

    debug: true

};


/* ==========================================================
   DOM Elements
========================================================== */

const headerContainer = document.getElementById("header");

const footerContainer = document.getElementById("footer");


/* ==========================================================
   Logger
========================================================== */

function log(message) {

    if (LOAD_CONFIG.debug) {

        console.log("[Load.js]", message);

    }

}


/* ==========================================================
   Safe Fetch
========================================================== */

async function fetchFile(path) {

    try {

        const response = await fetch(path, {

            cache: LOAD_CONFIG.cache
                ? "default"
                : "no-store"

        });

        if (!response.ok) {

            throw new Error(
                "Unable to load " + path
            );

        }

        return await response.text();

    }

    catch (error) {

        console.error(error);

        return "";

    }

}


/* ==========================================================
   Check Element
========================================================== */

function hasElement(element) {

    return element !== null;

}


/* ==========================================================
   Initialization
========================================================== */

function initLoader() {

    log("Load.js V4 Initialized");

}


document.addEventListener(

    "DOMContentLoaded",

    initLoader

);
/* ==========================================================
   Load.js V4
   Part 2 : Header + Footer Loader
========================================================== */

/* ==========================================================
   Loading Placeholder
========================================================== */

function showLoading(element) {

    if (!hasElement(element)) return;

    element.innerHTML = `
        <div class="loading-placeholder">
            Loading...
        </div>
    `;

}


/* ==========================================================
   Load HTML
========================================================== */

async function loadHTML(container, file) {

    if (!hasElement(container)) {

        return false;

    }

    showLoading(container);

    const html = await fetchFile(file);

    if (!html) {

        container.innerHTML = `
            <div class="load-error">
                Unable to load ${file}
            </div>
        `;

        return false;

    }

    container.innerHTML = html;

    log(file + " loaded successfully.");

    return true;

}


/* ==========================================================
   Load Header
========================================================== */

async function loadHeader() {

    return await loadHTML(

        headerContainer,

        LOAD_CONFIG.headerFile

    );

}


/* ==========================================================
   Load Footer
========================================================== */

async function loadFooter() {

    return await loadHTML(

        footerContainer,

        LOAD_CONFIG.footerFile

    );

}


/* ==========================================================
   Load All Layout Files
========================================================== */

async function loadLayout() {

    await Promise.all([

        loadHeader(),

        loadFooter()

    ]);

    log("Layout Loaded Successfully.");

}

console.log(
    "Load.js V4 Part 2 Loaded"
);
/* ==========================================================
   Load.js V4
   Part 3 : Active Menu + Retry + Auto Initialize
========================================================== */

/* ==========================================================
   Highlight Active Menu
========================================================== */

function highlightActiveMenu() {

    const currentPage = window.location.pathname
        .split("/")
        .pop() || "index.html";

    document.querySelectorAll("header a").forEach(link => {

        const href = link.getAttribute("href");

        if (!href) return;

        link.classList.remove("active");

        if (href === currentPage) {

            link.classList.add("active");

        }

    });

}


/* ==========================================================
   Retry Loader
========================================================== */

async function retryLoad(loader, retries = 2) {

    for (let i = 0; i <= retries; i++) {

        const success = await loader();

        if (success) {

            return true;

        }

        log(`Retry ${i + 1}/${retries}`);

    }

    return false;

}


/* ==========================================================
   Load Complete Layout
========================================================== */

async function initializeLayout() {

    await Promise.all([

        retryLoad(loadHeader),

        retryLoad(loadFooter)

    ]);

    highlightActiveMenu();

    log("Header/Footer Initialized.");

}


/* ==========================================================
   Performance Timer
========================================================== */

function performanceLog(startTime) {

    const time = performance.now() - startTime;

    log(`Layout Loaded in ${time.toFixed(2)} ms`);

}


/* ==========================================================
   Auto Start
========================================================== */

document.addEventListener(
    "DOMContentLoaded",
    async function () {

        const start = performance.now();

        await initializeLayout();

        performanceLog(start);

    }
);

console.log(
    "Load.js V4 Part 3 Loaded Successfully"
);
/* ==========================================================
   Load.js V4
   Part 4 : Cache + Events + Error Recovery
========================================================== */

/* ==========================================================
   Custom Events
========================================================== */

function dispatchLoadEvent(name, detail = {}) {

    document.dispatchEvent(

        new CustomEvent(name, {

            detail: detail

        })

    );

}


/* ==========================================================
   Refresh Layout
========================================================== */

async function refreshLayout() {

    log("Refreshing Layout...");

    await initializeLayout();

    dispatchLoadEvent(

        "layoutRefreshed"

    );
   // Initialize Search After Header Load

   if (window.initializeSearch) {
      window.initializeSearch();

   }
}


/* ==========================================================
   Force Reload
========================================================== */

async function forceReload() {

    LOAD_CONFIG.cache = false;

    await refreshLayout();

    LOAD_CONFIG.cache = true;

}


/* ==========================================================
   404 Recovery
========================================================== */

function handle404(container, file) {

    if (!hasElement(container)) {

        return;

    }

    container.innerHTML = `

        <div class="load-error">

            <h3>⚠ Unable to Load</h3>

            <p>${file} could not be loaded.</p>

        </div>

    `;

}


/* ==========================================================
   Enhanced Loader
========================================================== */

async function safeLoad(container, file) {

    try {

        const ok = await loadHTML(

            container,

            file

        );

        if (!ok) {

            handle404(

                container,

                file

            );

        }

        return ok;

    }

    catch (error) {

        console.error(error);

        handle404(

            container,

            file

        );

        return false;

    }

}


/* ==========================================================
   Lazy Layout
========================================================== */

async function lazyLoadLayout() {

    requestAnimationFrame(

        async () => {

            await safeLoad(

                headerContainer,

                LOAD_CONFIG.headerFile

            );

            await safeLoad(

                footerContainer,

                LOAD_CONFIG.footerFile

            );

            highlightActiveMenu();

            dispatchLoadEvent(

                "layoutLoaded"

            );

        }

    );

}


/* ==========================================================
   Public API
========================================================== */

window.refreshLayout = refreshLayout;

window.forceReloadLayout = forceReload;

window.loadLayout = lazyLoadLayout;

console.log(
    "Load.js V4 Part 4 Loaded Successfully"
);
/* ==========================================================
   Load.js V4
   Part 5 : Performance + Preload + Cleanup
========================================================== */

/* ==========================================================
   Performance Monitor
========================================================== */

const LOAD_STATS = {

    startTime: 0,

    endTime: 0,

    retries: 0,

    filesLoaded: 0

};


/* ==========================================================
   Start Timer
========================================================== */

function startLoading() {

    LOAD_STATS.startTime = performance.now();

}


/* ==========================================================
   Stop Timer
========================================================== */

function finishLoading() {

    LOAD_STATS.endTime = performance.now();

    const total = (

        LOAD_STATS.endTime -

        LOAD_STATS.startTime

    ).toFixed(2);

    log(`Loading Completed in ${total} ms`);

}


/* ==========================================================
   File Loaded Counter
========================================================== */

function fileLoaded() {

    LOAD_STATS.filesLoaded++;

}


/* ==========================================================
   Preload Resource
========================================================== */

function preloadResource(path) {

    const link = document.createElement("link");

    link.rel = "prefetch";

    link.href = path;

    document.head.appendChild(link);

}


/* ==========================================================
   Preload Header & Footer
========================================================== */

function preloadLayout() {

    preloadResource(

        LOAD_CONFIG.headerFile

    );

    preloadResource(

        LOAD_CONFIG.footerFile

    );

}


/* ==========================================================
   Retry Counter
========================================================== */

function increaseRetry() {

    LOAD_STATS.retries++;

}


/* ==========================================================
   Cleanup
========================================================== */

function cleanupLoader() {

    LOAD_STATS.retries = 0;

    log("Loader cleanup completed.");

}


/* ==========================================================
   Report
========================================================== */

function loaderReport() {

    console.group("Load.js Statistics");

    console.log(

        "Files Loaded :",

        LOAD_STATS.filesLoaded

    );

    console.log(

        "Retries :",

        LOAD_STATS.retries

    );

    console.log(

        "Load Time :",

        (

            LOAD_STATS.endTime -

            LOAD_STATS.startTime

        ).toFixed(2),

        "ms"

    );

    console.groupEnd();

}


/* ==========================================================
   Initialize Performance
========================================================== */

document.addEventListener(

    "DOMContentLoaded",

    function () {

        startLoading();

        preloadLayout();

    }

);

console.log(
    "Load.js V4 Part 5 Loaded Successfully"
);
/* ==========================================================
   Load.js V4
   Part 6 : Final Initialization + Validation + Public API
========================================================== */

/* ==========================================================
   Validate Layout
========================================================== */

function validateLayout() {

    const status = {

        header: hasElement(headerContainer),

        footer: hasElement(footerContainer)

    };

    console.group("Layout Validation");

    console.log("Header Container :", status.header);

    console.log("Footer Container :", status.footer);

    console.groupEnd();

    return status.header || status.footer;

}


/* ==========================================================
   Reset Layout
========================================================== */

function resetLayout() {

    if (hasElement(headerContainer)) {

        headerContainer.innerHTML = "";

    }

    if (hasElement(footerContainer)) {

        footerContainer.innerHTML = "";

    }

    cleanupLoader();

    log("Layout Reset Completed.");

}


/* ==========================================================
   Build Layout
========================================================== */

async function buildLayout() {

    startLoading();

    validateLayout();

    await initializeLayout();

    finishLoading();

    loaderReport();

}


/* ==========================================================
   Destroy Layout
========================================================== */

function destroyLayout() {

    resetLayout();

    SEARCH_CACHE?.clear?.();

    log("Layout Destroyed.");

}


/* ==========================================================
   Public API
========================================================== */

window.buildLayout = buildLayout;

window.resetLayout = resetLayout;

window.destroyLayout = destroyLayout;

window.validateLayout = validateLayout;


/* ==========================================================
   Auto Initialize
========================================================== */

console.log(
    "Load.js V4 Loaded Successfully"
);

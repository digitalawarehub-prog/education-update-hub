/* ==========================================================
   Education Update Hub - Load.js V5
   Header/Footer loader for root + generated post pages
   ========================================================== */
"use strict";

const LOAD_CONFIG = {
    headerFile: "/header.html",
    footerFile: "/footer.html",
    timeout: 10000,
    cache: false
};

function getElement(id) {
    return document.getElementById(id);
}

function logLoad(message) {
    console.log("[Load V5]", message);
}

async function fetchText(url) {
    const controller = new AbortController();
    const timer = setTimeout(
        () => controller.abort(),
        LOAD_CONFIG.timeout
    );

    try {
        const response = await fetch(
            url + "?v=" + Date.now(),
            {
                cache: LOAD_CONFIG.cache
                    ? "default"
                    : "no-store",
                signal: controller.signal
            }
        );

        if (!response.ok) {
            throw new Error(
                `${url} -> HTTP ${response.status}`
            );
        }

        return await response.text();
    } finally {
        clearTimeout(timer);
    }
}

async function loadInto(id, file) {
    const element = getElement(id);

    if (!element) {
        return false;
    }

    try {
        const html = await fetchText(file);

        if (!html) {
            throw new Error("Empty response");
        }

        element.innerHTML = html;

        logLoad(`${file} loaded`);

        return true;
    } catch (error) {
        console.error(
            `[Load V5] Failed to load ${file}`,
            error
        );

        element.innerHTML = "";

        return false;
    }
}

function highlightActiveMenu() {
    const current =
        window.location.pathname
            .split("/")
            .pop() || "index.html";

    document
        .querySelectorAll(".navbar a")
        .forEach(link => {
            link.classList.remove("active");

            const href =
                link.getAttribute("href") || "";

            if (
                href === current ||
                href.endsWith("/" + current)
            ) {
                link.classList.add("active");
            }
        });
}

async function initializeLayout() {
    // Load header first so search elements exist before
    // search initialization.
    await loadInto(
        "header",
        LOAD_CONFIG.headerFile
    );

    await loadInto(
        "footer",
        LOAD_CONFIG.footerFile
    );

    highlightActiveMenu();

    if (window.initializeSearch) {
        window.initializeSearch();
    }

    document.dispatchEvent(
        new CustomEvent("layoutReady")
    );

    document.dispatchEvent(
        new CustomEvent("layoutLoaded")
    );

    logLoad("Layout initialized");
}

document.addEventListener(
    "DOMContentLoaded",
    initializeLayout
);

window.refreshLayout = initializeLayout;

console.log("[Load V5] Loaded");

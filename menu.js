/* ==========================================================
   Menu.js V4
   Part 1 : Configuration + Initialization
========================================================== */

"use strict";

/* ==========================================================
   Menu Configuration
========================================================== */

const MENU = {

    mobileBreakpoint: 992,

    animationSpeed: 300,

    stickyHeader: true,

    autoClose: true,

    activeMenu: true,

    smoothScroll: true

};


/* ==========================================================
   DOM Elements
========================================================== */

const body = document.body;

const header = document.querySelector("header");

const nav = document.querySelector(".navbar");

const menuButton = document.querySelector(".menu-toggle");

const mobileMenu = document.querySelector(".mobile-menu");

const overlay = document.querySelector(".menu-overlay");


/* ==========================================================
   Helper Functions
========================================================== */

function hasElement(element) {

    return element !== null;

}

function isMobile() {

    return window.innerWidth <= MENU.mobileBreakpoint;

}

function addClass(element, className) {

    if (hasElement(element)) {

        element.classList.add(className);

    }

}

function removeClass(element, className) {

    if (hasElement(element)) {

        element.classList.remove(className);

    }

}

function toggleClass(element, className) {

    if (hasElement(element)) {

        element.classList.toggle(className);

    }

}


/* ==========================================================
   Menu State
========================================================== */

let menuOpened = false;


/* ==========================================================
   Initialization
========================================================== */

function initMenu() {

    console.log("Menu.js V4 Initialized");

}

document.addEventListener(

    "DOMContentLoaded",

    initMenu

);
/* ==========================================================
   Menu.js V4
   Part 2 : Mobile Menu + Overlay + Scroll Lock
========================================================== */

/* ==========================================================
   Open Menu
========================================================== */

function openMenu() {

    if (!isMobile()) return;

    menuOpened = true;

    addClass(body, "menu-open");

    addClass(mobileMenu, "active");

    addClass(overlay, "active");

}


/* ==========================================================
   Close Menu
========================================================== */

function closeMenu() {

    menuOpened = false;

    removeClass(body, "menu-open");

    removeClass(mobileMenu, "active");

    removeClass(overlay, "active");

}


/* ==========================================================
   Toggle Menu
========================================================== */

function toggleMenu() {

    if (menuOpened) {

        closeMenu();

    } else {

        openMenu();

    }

}


/* ==========================================================
   Menu Button
========================================================== */

if (hasElement(menuButton)) {

    menuButton.addEventListener(

        "click",

        toggleMenu

    );

}


/* ==========================================================
   Overlay Click
========================================================== */

if (hasElement(overlay)) {

    overlay.addEventListener(

        "click",

        closeMenu

    );

}


/* ==========================================================
   Auto Close On Menu Link Click
========================================================== */

if (hasElement(mobileMenu)) {

    mobileMenu.querySelectorAll("a")

    .forEach(link => {

        link.addEventListener(

            "click",

            function () {

                if (

                    MENU.autoClose &&

                    isMobile()

                ) {

                    closeMenu();

                }

            }

        );

    });

}


/* ==========================================================
   Window Resize
========================================================== */

window.addEventListener(

    "resize",

    function () {

        if (

            !isMobile() &&

            menuOpened

        ) {

            closeMenu();

        }

    }

);

console.log(
    "Menu.js V4 Part 2 Loaded"
);
/* ==========================================================
   Menu.js V4
   Part 3 : Sticky Header + Active Menu + Smooth Scroll
========================================================== */

/* ==========================================================
   Sticky Header
========================================================== */

function handleStickyHeader() {

    if (!MENU.stickyHeader) {

        return;

    }

    if (!hasElement(header)) {

        return;

    }

    if (window.scrollY > 80) {

        addClass(
            header,
            "sticky"
        );

    } else {

        removeClass(
            header,
            "sticky"
        );

    }

}


/* ==========================================================
   Active Navigation Link
========================================================== */

function updateActiveMenu() {

    if (!MENU.activeMenu) {

        return;

    }

    const currentPage = window.location.pathname
        .split("/")
        .pop() || "index.html";

    document.querySelectorAll("nav a").forEach(link => {

        removeClass(
            link,
            "active"
        );

        const href = link.getAttribute("href");

        if (!href) {

            return;

        }

        if (href === currentPage) {

            addClass(
                link,
                "active"
            );

        }

    });

}


/* ==========================================================
   Smooth Scroll
========================================================== */

function enableSmoothScroll() {

    if (!MENU.smoothScroll) {

        return;

    }

    document.querySelectorAll(
        'a[href^="#"]'
    ).forEach(anchor => {

        anchor.addEventListener(

            "click",

            function (e) {

                const target = document.querySelector(

                    this.getAttribute("href")

                );

                if (!target) {

                    return;

                }

                e.preventDefault();

                target.scrollIntoView({

                    behavior: "smooth",

                    block: "start"

                });

            }

        );

    });

}


/* ==========================================================
   Scroll Event
========================================================== */

window.addEventListener(

    "scroll",

    handleStickyHeader

);


/* ==========================================================
   Initialize Features
========================================================== */

document.addEventListener(

    "DOMContentLoaded",

    function () {

        handleStickyHeader();

        updateActiveMenu();

        enableSmoothScroll();

    }

);

console.log(
    "Menu.js V4 Part 3 Loaded"
);
/* ==========================================================
   Menu.js V4
   Part 4 : Accessibility + Keyboard + Outside Click
========================================================== */

/* ==========================================================
   ESC Key Close
========================================================== */

document.addEventListener(

    "keydown",

    function(event) {

        if (
            event.key === "Escape" &&
            menuOpened
        ) {

            closeMenu();

        }

    }

);


/* ==========================================================
   Click Outside Menu
========================================================== */

document.addEventListener(

    "click",

    function(event) {

        if (!menuOpened) {

            return;

        }

        if (!isMobile()) {

            return;

        }

        if (
            mobileMenu &&
            menuButton &&
            !mobileMenu.contains(event.target) &&
            !menuButton.contains(event.target)
        ) {

            closeMenu();

        }

    }

);


/* ==========================================================
   Accessibility
========================================================== */

function setupAccessibility() {

    if (!menuButton) {

        return;

    }

    menuButton.setAttribute(

        "aria-label",

        "Toggle Navigation Menu"

    );

    menuButton.setAttribute(

        "aria-expanded",

        "false"

    );

}


/* ==========================================================
   Update ARIA State
========================================================== */

function updateAriaState() {

    if (!menuButton) {

        return;

    }

    menuButton.setAttribute(

        "aria-expanded",

        menuOpened

    );

}


/* ==========================================================
   Override Menu Functions
========================================================== */

const originalOpenMenu = openMenu;

openMenu = function() {

    originalOpenMenu();

    updateAriaState();

};


const originalCloseMenu = closeMenu;

closeMenu = function() {

    originalCloseMenu();

    updateAriaState();

};


/* ==========================================================
   Focus First Menu Link
========================================================== */

function focusFirstLink() {

    if (!mobileMenu) {

        return;

    }

    const firstLink = mobileMenu.querySelector("a");

    if (firstLink) {

        firstLink.focus();

    }

}


const originalToggleMenu = toggleMenu;

toggleMenu = function() {

    originalToggleMenu();

    if (menuOpened) {

        focusFirstLink();

    }

};


/* ==========================================================
   Initialize Accessibility
========================================================== */

document.addEventListener(

    "DOMContentLoaded",

    function() {

        setupAccessibility();

        updateAriaState();

    }

);

console.log(
    "Menu.js V4 Part 4 Loaded Successfully"
);
/* ==========================================================
   Menu.js V4
   Part 5 : Dropdown + Touch Support + Performance
========================================================== */

/* ==========================================================
   Dropdown Menu
========================================================== */

function initDropdowns() {

    document.querySelectorAll(".has-dropdown").forEach(item => {

        const trigger = item.querySelector("a");
        const dropdown = item.querySelector(".dropdown");

        if (!trigger || !dropdown) return;

        trigger.addEventListener("click", function(e) {

            if (!isMobile()) return;

            e.preventDefault();

            document
                .querySelectorAll(".has-dropdown.active")
                .forEach(openItem => {

                    if (openItem !== item) {

                        openItem.classList.remove("active");

                    }

                });

            item.classList.toggle("active");

        });

    });

}


/* ==========================================================
   Touch Device Support
========================================================== */

function enableTouchSupport() {

    document.querySelectorAll(".has-dropdown").forEach(item => {

        item.addEventListener("touchstart", function() {

            item.classList.add("touch-device");

        }, { passive: true });

    });

}


/* ==========================================================
   Close All Dropdowns
========================================================== */

function closeDropdowns() {

    document.querySelectorAll(".has-dropdown.active")
        .forEach(item => {

            item.classList.remove("active");

        });

}


/* ==========================================================
   Active Parent Menu
========================================================== */

function highlightParentMenu() {

    const current = window.location.pathname
        .split("/")
        .pop();

    document.querySelectorAll(".dropdown a").forEach(link => {

        if (link.getAttribute("href") === current) {

            const parent = link.closest(".has-dropdown");

            if (parent) {

                parent.classList.add("active-parent");

            }

        }

    });

}


/* ==========================================================
   Performance Optimization
========================================================== */

let resizeTimer = null;

window.addEventListener("resize", function() {

    clearTimeout(resizeTimer);

    resizeTimer = setTimeout(function() {

        if (!isMobile()) {

            closeDropdowns();

        }

    }, 150);

});


/* ==========================================================
   Initialize
========================================================== */

document.addEventListener("DOMContentLoaded", function() {

    initDropdowns();

    enableTouchSupport();

    highlightParentMenu();

});

console.log(
    "Menu.js V4 Part 5 Loaded Successfully"
);
/* ==========================================================
   Menu.js V4
   Part 6 : Final Initialization + Validation
========================================================== */

/* ==========================================================
   Validate Menu
========================================================== */

function validateMenu() {

    console.group("Menu Validation");

    console.log("Header :", !!header);
    console.log("Navbar :", !!nav);
    console.log("Menu Button :", !!menuButton);
    console.log("Mobile Menu :", !!mobileMenu);
    console.log("Overlay :", !!overlay);

    console.groupEnd();

}


/* ==========================================================
   Reset Menu
========================================================== */

function resetMenu() {

    closeMenu();

    closeDropdowns();

}


/* ==========================================================
   Destroy Menu
========================================================== */

function destroyMenu() {

    resetMenu();

    console.log(
        "Menu destroyed successfully."
    );

}


/* ==========================================================
   Performance Report
========================================================== */

function menuStatistics() {

    console.group("Menu Statistics");

    console.log(
        "Screen Width :",
        window.innerWidth
    );

    console.log(
        "Mobile Mode :",
        isMobile()
    );

    console.log(
        "Menu Open :",
        menuOpened
    );

    console.log(
        "Dropdowns :",
        document.querySelectorAll(".has-dropdown").length
    );

    console.groupEnd();

}


/* ==========================================================
   Initialize Menu V4
========================================================== */

function initMenuV4() {

    validateMenu();

    handleStickyHeader();

    updateActiveMenu();

    enableSmoothScroll();

    initDropdowns();

    enableTouchSupport();

    highlightParentMenu();

    updateAriaState();

    menuStatistics();

    console.log(
        "Menu.js V4 Initialized Successfully."
    );

}


/* ==========================================================
   Public API
========================================================== */

window.openMenu = openMenu;
window.closeMenu = closeMenu;
window.toggleMenu = toggleMenu;
window.resetMenu = resetMenu;
window.destroyMenu = destroyMenu;


/* ==========================================================
   Auto Initialize
========================================================== */

document.addEventListener(

    "DOMContentLoaded",

    function () {

        initMenuV4();

    }

);

console.log(
    "Menu.js V4 Loaded Successfully"
);

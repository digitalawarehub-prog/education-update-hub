/* ==========================================================
   Education Update Hub - Common Script V8
   Safe on dynamically loaded header/footer pages
   ========================================================== */
"use strict";

(() => {
    function initCommon() {
        const menu = document.querySelector(".menu-toggle");
        const nav = document.querySelector(".navbar");

        if (menu && nav && menu.dataset.commonBound !== "1") {
            menu.dataset.commonBound = "1";
            menu.addEventListener("click", () => {
                nav.classList.toggle("active");
            });
        }

        // Back to top
        let btn = document.getElementById("topBtn");

        if (!btn) {
            btn = document.createElement("button");
            btn.innerHTML = "⬆";
            btn.id = "topBtn";
            btn.setAttribute("aria-label", "Back to top");
            Object.assign(btn.style, {
                position: "fixed",
                right: "20px",
                bottom: "20px",
                padding: "12px 16px",
                background: "#0d6efd",
                color: "#fff",
                border: "none",
                borderRadius: "50%",
                display: "none",
                cursor: "pointer",
                zIndex: "9999"
            });
            document.body.appendChild(btn);
        }

        const updateTopButton = () => {
            btn.style.display =
                window.scrollY > 300 ? "block" : "none";
        };

        if (btn.dataset.scrollBound !== "1") {
            btn.dataset.scrollBound = "1";
            window.addEventListener("scroll", updateTopButton, { passive: true });
            btn.addEventListener("click", () => {
                window.scrollTo({ top: 0, behavior: "smooth" });
            });
            updateTopButton();
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initCommon, { once: true });
    } else {
        initCommon();
    }

    // Header is inserted by load.js after DOMContentLoaded.
    document.addEventListener("layoutReady", initCommon);
    document.addEventListener("layoutLoaded", initCommon);
})();

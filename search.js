/* Education Update Hub - Search compatibility loader.
   The authoritative search implementation lives in header.html and is
   initialized by load.js after the header is injected. */
(function(){
  "use strict";
  window.addEventListener("layoutReady", function(){
    if (typeof window.initializeSearch === "function") window.initializeSearch();
  });
})();

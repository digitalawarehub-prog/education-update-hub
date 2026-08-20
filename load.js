/* Education Update Hub - Layout Loader V7 */
"use strict";
const LOAD_CONFIG={headerFile:"/header.html",footerFile:"/footer.html",timeout:10000,cache:false};
const getElement=id=>document.getElementById(id);
async function fetchText(url){const c=new AbortController();const t=setTimeout(()=>c.abort(),LOAD_CONFIG.timeout);try{const r=await fetch(url+"?v="+Date.now(),{cache:"no-store",signal:c.signal});if(!r.ok)throw new Error(`${url} -> HTTP ${r.status}`);return await r.text();}finally{clearTimeout(t);}}
async function loadInto(id,file){const el=getElement(id);if(!el)return false;try{const html=await fetchText(file);if(!html)throw new Error("Empty response");el.innerHTML=html;return true;}catch(e){console.error(`[Load V7] Failed to load ${file}`,e);el.innerHTML="";return false;}}
function highlightActiveMenu(){const current=location.pathname.split("/").pop()||"index.html";document.querySelectorAll(".navbar a").forEach(a=>{a.classList.remove("active");const h=a.getAttribute("href")||"";if(h===current||h.endsWith("/"+current))a.classList.add("active");});}
function forceFooterLast(){const f=getElement("footer");if(f&&document.body)document.body.appendChild(f);}
function loadScriptOnce(src){return new Promise(resolve=>{if(document.querySelector(`script[data-euh-src="${src}"]`)){resolve();return;}const s=document.createElement("script");s.src=src+"?v="+Date.now();s.dataset.euhSrc=src;s.onload=resolve;s.onerror=()=>{console.error("[Load V7] Script failed:",src);resolve();};document.body.appendChild(s);});}
async function initializeLayout(){await loadInto("header",LOAD_CONFIG.headerFile);await loadInto("footer",LOAD_CONFIG.footerFile);forceFooterLast();highlightActiveMenu();await loadScriptOnce("/search.js");if(window.initializeSearch)window.initializeSearch();document.dispatchEvent(new CustomEvent("layoutReady"));document.dispatchEvent(new CustomEvent("layoutLoaded"));}
document.addEventListener("DOMContentLoaded",initializeLayout);window.refreshLayout=initializeLayout;console.log("[Load V7] Loaded");

/* ==========================================
MENU.JS
Education Update Hub
========================================== */
document.addEventListener("DOMContentLoaded", () => {
const menuToggle = document.getElementById("menuToggle");
const navbar = document.getElementById("navbar");
/* ==========================
MOBILE MENU
========================== */
if(menuToggle && navbar){
menuToggle.addEventListener("click", () => {
navbar.classList.toggle("active");
});
}
/* ==========================
MOBILE DROPDOWN
========================== */
const dropdowns=document.querySelectorAll(".has-dropdown");
dropdowns.forEach(item=>{
const link=item.querySelector("a");
link.addEventListener("click",function(e){
if(window.innerWidth<=768){
e.preventDefault();
item.classList.toggle("active");
}
});
});
/* ==========================
CLICK OUTSIDE MENU
========================== */
document.addEventListener("click",function(e){
if(window.innerWidth<=768){
if(
navbar &&
menuToggle &&
!navbar.contains(e.target) &&
!menuToggle.contains(e.target)
){
navbar.classList.remove("active");
}
}
});
/* ==========================
WINDOW RESIZE
========================== */
window.addEventListener("resize",function(){
if(window.innerWidth>768){
navbar.classList.remove("active");
dropdowns.forEach(item=>{
item.classList.remove("active");
});
}
});
});
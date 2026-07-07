/* ===========================
Mobile Menu
=========================== */
const menu=document.querySelector(".menu-toggle");
const nav=document.querySelector(".navbar ul");
menu.addEventListener("click",()=>{
nav.classList.toggle("active");
});
/* ===========================
Search
=========================== */
function searchPosts(){
let input=document.getElementById("searchInput").value.toLowerCase();
let cards=document.querySelectorAll(".card");
cards.forEach(card=>{
let title=card.innerText.toLowerCase();
if(title.indexOf(input)>-1){
card.style.display="block";
}
else{
card.style.display="none";
}
});
}
/* ===========================
Back To Top
=========================== */
let btn=document.createElement("button");
btn.innerHTML="⬆";
btn.id="topBtn";
document.body.appendChild(btn);
btn.style.position="fixed";
btn.style.right="20px";
btn.style.bottom="20px";
btn.style.padding="12px 16px";
btn.style.background="#0d6efd";
btn.style.color="#fff";
btn.style.border="none";
btn.style.borderRadius="50%";
btn.style.display="none";
btn.style.cursor="pointer";
btn.style.zIndex="9999";
window.onscroll=function(){
if(document.documentElement.scrollTop>300){
btn.style.display="block";
}
else{
btn.style.display="none";
}
}
btn.onclick=function(){
window.scrollTo({
top:0,
behavior:"smooth"
});
}
/* ===========================
Smooth Scroll
=========================== */
document.querySelectorAll('a[href^="#"]').forEach(anchor=>{
anchor.addEventListener("click",function(e){
e.preventDefault();
document.querySelector(this.getAttribute("href")).scrollIntoView({
behavior:"smooth"
});
});
});
const searchInput = document.getElementById("searchInput");
const searchResults = document.getElementById("searchResults");
if(searchInput){
searchInput.addEventListener("keyup",function(){
const keyword=this.value.trim().toLowerCase();
searchResults.innerHTML="";
if(keyword.length<2){
searchResults.style.display="none";
return;
}
const results=searchData.filter(item=>{
return(
item.title.toLowerCase().includes(keyword) ||
item.category.toLowerCase().includes(keyword)
);
});
if(results.length===0){
searchResults.innerHTML=`
<div class="search-item no-result">
No Result Found
</div>
`;
searchResults.style.display="block";
return;
}
results.slice(0,10).forEach(item=>{
searchResults.innerHTML+=`
<a href="${item.url}" class="search-item">
<img src="${item.image}" alt="${item.title}">
<div class="search-content">
<h4>${item.title}</h4>
<p>${item.category}</p>
</div>
</a>
`;
});
searchResults.style.display="block";
});
document.addEventListener("click",function(e){
if(!e.target.closest(".search-box")){
searchResults.style.display="none";
}
});
}
/* ==========================================
SEARCH PART 4
Keyboard Navigation + Enter Search
========================================== */
let selectedIndex = -1;
searchInput.addEventListener("keydown", function(e){
const items=document.querySelectorAll(".search-item");
if(items.length===0) return;
/* Down Arrow */
if(e.key==="ArrowDown"){
e.preventDefault();
selectedIndex++;
if(selectedIndex>=items.length){
selectedIndex=0;
}
updateSelection(items);
}
/* Up Arrow */
if(e.key==="ArrowUp"){
e.preventDefault();
selectedIndex--;
if(selectedIndex<0){
selectedIndex=items.length-1;
}
updateSelection(items);
}
/* Enter */
if(e.key==="Enter"){
e.preventDefault();
if(selectedIndex>-1){
window.location.href=items[selectedIndex].href;
}
}
/* ESC */
if(e.key==="Escape"){
searchResults.style.display="none";
selectedIndex=-1;
}
});
function updateSelection(items){
items.forEach(item=>{
item.classList.remove("active-search");
});
if(selectedIndex>-1){
items[selectedIndex].classList.add("active-search");
items[selectedIndex].scrollIntoView({
block:"nearest"
});
}
}
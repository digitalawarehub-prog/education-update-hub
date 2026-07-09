// ==========================
// HEADER LOAD
// ==========================
fetch("header.html")
.then(response => response.text())
.then(data=>{
document.getElementById("header").innerHTML=data;
// Date
const dateBox=document.getElementById("current-date");
if(dateBox){
const options={
weekday:"long",
day:"2-digit",
month:"long",
year:"numeric"
};
dateBox.textContent=
new Date().toLocaleDateString("en-GB",options);
}
// Search Start
if(typeof initSearch==="function"){
initSearch();
}
});
// ==========================
// FOOTER LOAD
// ==========================
fetch("footer.html")
.then(response=>response.text())
.then(data=>{
document.getElementById("footer").innerHTML=data;
});
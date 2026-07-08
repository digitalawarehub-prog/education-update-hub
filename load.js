// ===========================
// Load Header
// ===========================
fetch("header.html")
.then(response => response.text())
.then(data => {
document.getElementById("header").innerHTML = data;
// Current Date
const dateBox = document.getElementById("current-date");
if(dateBox){
const options = {
weekday:"long",
day:"2-digit",
month:"long",
year:"numeric"
};
dateBox.textContent =
new Date().toLocaleDateString("en-GB", options);
}
})
.catch(error => console.log("Header Load Error:", error));
// ===========================
// Load Footer
// ===========================
fetch("footer.html")
.then(response => response.text())
.then(data => {
document.getElementById("footer").innerHTML = data;
})
.catch(error => console.log("Footer Load Error:", error));
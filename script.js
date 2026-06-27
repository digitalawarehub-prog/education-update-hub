function myFunction() {
    document.getElementById("demo").innerHTML = 
    "Welcome to Digital Aware Hub";
}
function searchSite() {
    let text =
    document.getElementById("Search").value;
    alert("You searched: " + text);
}
function searchPosts() {
    let input = document.getElementById("searchInput").value.toLowerCase().trim();
    let posts = document.querySelectorAll(".card");
    posts.forEach(post => {
        let text = post.textContent.toLowerCase();
        if (text.includes(input)) {
            post.style.display = "";
        } else {
            post.style.display = "none";
        }
    });
}
const navLinks = document.querySelector(".nav-links");
window.addEventListener("resize", function () {
    if (window.innerWidth > 768 && navLinks) {
        navLinks.classList.remove("active");
    }
});
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
    let input = document.getElementById("searchInput").value.toLowerCase();
    let cards = document.getElementsByClassName("card");
    for (let i = 0; i < cards.length; i++) {
        let text = cards[i].innerText.toLowerCase();
        if (text.indexOf(input) > -1) {
            cards[i].style.display = "";
        } else {
            cards[i].style.display = "none";
        }
    }
}
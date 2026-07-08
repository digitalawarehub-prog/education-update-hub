document.getElementById("header").innerHTML = `
<header>
<div class="top-header">
<div class="logo">
<a href="index.html">
<img src="images/logo.png" alt="Education Update Hub">
</a>
</div>
<div class="site-title">
<h1><span>Education</span> Update Hub</h1>
<p>Latest Government Jobs, Admit Card, Results & Education Updates</p>
</div>
<div class="search-box">
<form action="search.html">
<input type="text" placeholder="Search Jobs, Admit Card, Results..." name="q">
<button type="submit">Search</button>
</form>
</div>
</div>
<nav class="navbar">
<ul>
<li><a href="index.html">Home</a></li>
<li class="dropdown">
<a href="#">Uttarakhand Jobs ▼</a>
<ul class="dropdown-menu">
<li><a href="ukpsc.html">UKPSC</a></li>
<li><a href="uksssc.html">UKSSSC</a></li>
<li><a href="high-court.html">High Court</a></li>
</ul>
</li>
<li class="dropdown">
<a href="#">Central Jobs ▼</a>
<ul class="dropdown-menu">
<li><a href="upsc.html">UPSC</a></li>
<li><a href="ssc.html">SSC</a></li>
<li><a href="banking-jobs.html">Banking</a></li>
<li><a href="railway-jobs.html">Railway</a></li>
</ul>
</li>
<li class="dropdown">
<a href="#">Teaching Exams ▼</a>
<ul class="dropdown-menu">
<li><a href="ctet.html">CTET</a></li>
<li><a href="utet.html">UTET</a></li>
<li><a href="ugc-net.html">UGC NET</a></li>
<li><a href="csir-ugc-net.html">CSIR UGC NET</a></li>
<li><a href="cuet.html">CUET</a></li>
<li><a href="neet-ug.html">NEET UG</a></li>
</ul>
</li>
<li><a href="admit-card.html">Admit Card</a></li>
<li><a href="result.html">Results</a></li>
<li><a href="answer-key.html">Answer Key</a></li>
<li><a href="syllabus.html">Syllabus</a></li>
<li><a href="scholarship.html">Scholarship</a></li>
<li><a href="contact.html">Contact</a></li>
</ul>
</nav>
</header>
`;
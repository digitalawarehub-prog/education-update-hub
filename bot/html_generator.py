import html,re,json
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parent.parent
POST=ROOT/"generated/posts"; POST.mkdir(parents=True,exist_ok=True)
BASE="https://educationupdatehub.in"
INFO={"recruitment":("💼","Recruitment"),"result":("🏆","Result"),"admit_card":("🎫","Admit Card"),
"answer_key":("📝","Answer Key"),"syllabus":("📚","Syllabus"),"entrance_exam":("🎓","Entrance Exam"),
"scholarship":("💰","Scholarship"),"interview":("👤","Interview"),"exam_schedule":("🗓️","Exam Schedule"),
"notice":("📢","Notice")}
def e(x):return html.escape(str(x or ""))
def slug(x):return re.sub(r"[^a-z0-9]+","-",str(x).lower()).strip("-")[:120] or "update"
def btn(url,text,cls):
    return f'<a class="btn {cls}" href="{e(url)}" target="_blank" rel="noopener">{e(text)}</a>' if url else ""
def rows(j):
    c=j.get("category","notice")
    maps={
    "recruitment":[("Department",j.get("department")),("Post Name",j.get("post_name")),("Total Posts",j.get("total_posts")),("Qualification",j.get("qualification")),("Salary",j.get("salary")),("Age Limit",j.get("age_limit")),("Application Start",j.get("application_start")),("Last Date",j.get("last_date"))],
    "result":[("Organization",j.get("organization")),("Exam / Post",j.get("post_name") or j.get("title")),("Result Date",j.get("result_date")),("Status","Released")],
    "admit_card":[("Organization",j.get("organization")),("Exam / Post",j.get("post_name") or j.get("title")),("Exam Date",j.get("exam_date")),("Status","Available")],
    "answer_key":[("Organization",j.get("organization")),("Exam / Post",j.get("post_name") or j.get("title")),("Exam Date",j.get("exam_date")),("Status","Available")],
    "syllabus":[("Organization",j.get("organization")),("Exam / Post",j.get("post_name") or j.get("title")),("Syllabus","Available")],
    "entrance_exam":[("Organization",j.get("organization")),("Exam Name",j.get("post_name") or j.get("title")),("Eligibility",j.get("qualification")),("Application Start",j.get("application_start")),("Last Date",j.get("last_date")),("Exam Date",j.get("exam_date")),("Fee",j.get("fee"))],
    "scholarship":[("Organization",j.get("organization")),("Scholarship",j.get("post_name") or j.get("title")),("Eligibility",j.get("qualification")),("Last Date",j.get("last_date")),("Amount / Stipend",j.get("salary"))],
    "interview":[("Organization",j.get("organization")),("Post",j.get("post_name") or j.get("title")),("Interview Date",j.get("interview_date") or j.get("exam_date")),("Qualification",j.get("qualification")),("Venue / Mode",j.get("selection_process"))],
    "exam_schedule":[("Organization",j.get("organization")),("Exam / Stage",j.get("post_name") or j.get("title")),("Exam Date",j.get("exam_date")),("Schedule",j.get("selection_process"))],
    "notice":[("Department",j.get("department")),("Organization",j.get("organization")),("Important Date",j.get("exam_date") or j.get("last_date"))]}
    return [(a,b) for a,b in maps.get(c,maps["notice"]) if b]
def actions(j):
    c=j.get("category","notice")
    if c=="recruitment": return btn(j.get("apply_url"),"🚀 Apply Online","green")+btn(j.get("notification_url"),"📄 Notification","orange")+btn(j.get("official_url"),"🌐 Official Website","blue")
    if c=="result": return btn(j.get("result_url") or j.get("apply_url"),"🏆 View Result","red")+btn(j.get("notification_url"),"📄 Notification","orange")+btn(j.get("official_url"),"🌐 Official Website","blue")
    if c=="admit_card": return btn(j.get("admit_card_url"),"🎫 Download Admit Card","purple")+btn(j.get("official_url"),"🌐 Official Website","blue")
    if c=="answer_key": return btn(j.get("answer_key_url"),"📝 Download Answer Key","gold")+btn(j.get("official_url"),"🌐 Official Website","blue")
    if c=="syllabus": return btn(j.get("syllabus_url"),"📚 Download Syllabus","blue")+btn(j.get("official_url"),"🌐 Official Website","blue")
    if c=="entrance_exam": return btn(j.get("apply_url"),"🟢 Apply / Register","green")+btn(j.get("notification_url"),"📄 Notification","orange")+btn(j.get("official_url"),"🌐 Official Website","blue")
    if c=="scholarship": return btn(j.get("apply_url"),"💰 Apply Now","green")+btn(j.get("notification_url"),"📄 Details","orange")+btn(j.get("official_url"),"🌐 Official Website","blue")
    if c=="interview": return btn(j.get("apply_url"),"👤 Interview / Apply","green")+btn(j.get("notification_url"),"📄 Interview Notice","orange")+btn(j.get("official_url"),"🌐 Official Website","blue")
    return btn(j.get("notification_url"),"📄 Official Notice","orange")+btn(j.get("official_url"),"🌐 Official Website","blue")
CSS="""*{box-sizing:border-box}body{margin:0;background:#f4f7fb;color:#172033;font-family:Arial,sans-serif}a{text-decoration:none}.wrap{max-width:1150px;margin:auto;padding:24px 18px}.top{background:#fff;border-bottom:1px solid #e4e9f0}.brand{max-width:1150px;margin:auto;padding:18px;display:flex;align-items:center;gap:12px}.brand b{font-size:27px;color:#1265d9}.brand span{color:#f28b18}.brand small{display:block;color:#748096}.nav{background:#075ed6;color:#fff;text-align:center;padding:10px}.nav a{color:#fff;margin:0 8px;font-size:13px;font-weight:bold}.hero{background:linear-gradient(135deg,#0868df,#174ca6);color:#fff;padding:38px;border-radius:18px;margin-bottom:20px}.hero h1{font-size:38px;margin:10px 0}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.card,.post,.stat{background:#fff;border:1px solid #e2e8f0;border-radius:15px;padding:20px;box-shadow:0 5px 18px #12233a10}.card:hover{transform:translateY(-2px)}.card .ico{font-size:28px}.card h3{font-size:17px;line-height:1.35;color:#172b4d}.card small{color:#1265d9;font-weight:bold}.badge{color:#1265d9;font-weight:bold}.post h1{font-size:36px;line-height:1.2}.meta{color:#778297;font-size:12px}.table{width:100%;border-collapse:collapse;margin:18px 0}.table th,.table td{padding:12px;border-bottom:1px solid #e5eaf0;text-align:left}.table th{width:32%;background:#f0f5fb;color:#234b7c}.btn{display:inline-block;color:#fff;padding:11px 16px;border-radius:8px;margin:4px;font-weight:bold;font-size:14px}.green{background:#17a957}.orange{background:#e56b2d}.blue{background:#126ee8}.purple{background:#7350ca}.red{background:#d83e50}.gold{background:#d49313}@media(max-width:750px){.grid{grid-template-columns:1fr}.hero h1{font-size:28px}.nav a{display:inline-block;margin:4px;font-size:11px}.post h1{font-size:28px}}"""
def pagehead(t,d):return f'<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(t)}</title><meta name="description" content="{e(d[:155])}"><style>{CSS}</style></head><body><header class="top"><div class="brand">📖 <div><b>Education <span>Update Hub</span></b><small>Latest Government Jobs, Results & Education Updates</small></div></div><div class="nav"><a href="/">Home</a><a href="/latest-jobs.html">Jobs</a><a href="/result.html">Results</a><a href="/admit-card.html">Admit Card</a><a href="/answer-key.html">Answer Key</a><a href="/syllabus.html">Syllabus</a><a href="/scholarship.html">Scholarship</a><a href="/entrance-exams.html">Entrance Exams</a></div></header>'
def post_html(j):
    icon,label=INFO.get(j.get("category"),INFO["notice"]); r="".join(f"<tr><th>{e(a)}</th><td>{e(b)}</td></tr>" for a,b in rows(j))
    content=j.get("content_html") or e(j.get("description") or j.get("summary") or "")
    return pagehead(j.get("title","Government Update"),j.get("meta_description",""))+f'<main class="wrap"><div class="post"><div class="badge">{icon} {label}</div><h1>{e(j.get("title"))}</h1><div class="meta">Updated {datetime.now().strftime("%d %b %Y")}</div><p>{e(j.get("meta_description"))}</p><h2>{icon} {label} Details</h2><table class="table">{r or "<tr><th>Information</th><td>Available in official source</td></tr>"}</table><div>{actions(j)}</div><section>{content}</section></div></main></body></html>'
def write_post(j):
    p=POST/(slug(j.get("title"))+".html");p.write_text(post_html(j),encoding="utf-8");return p
def card(j):
    icon,label=INFO.get(j.get("category"),INFO["notice"])
    return f'<a class="card" href="/generated/posts/{slug(j.get("title"))}.html"><div class="ico">{icon}</div><small>{label}</small><h3>{e(j.get("title"))}</h3><small>View Details →</small></a>'
def build_files(jobs):
    jobs=[j for j in jobs if j.get("title")]
    cards="".join(card(j) for j in jobs)
    (ROOT/"index.html").write_text(pagehead("Education Update Hub","Latest Government Jobs, Results, Admit Cards, Scholarships and Education Updates.")+f'<main class="wrap"><section class="hero"><h1>Latest Government Jobs, Results,<br>Admit Card & Scholarships</h1><p>Official updates with important dates and direct links.</p></section><h2>🔥 Latest Updates</h2><div class="grid">{cards}</div></main></body></html>',encoding="utf-8")
    cats={"latest-jobs.html":("Latest Jobs","recruitment"),"result.html":("Latest Results","result"),"admit-card.html":("Latest Admit Cards","admit_card"),"answer-key.html":("Latest Answer Keys","answer_key"),"syllabus.html":("Latest Syllabus","syllabus"),"entrance-exams.html":("Entrance Exams","entrance_exam"),"scholarship.html":("Scholarship Updates","scholarship"),"teaching-exams.html":("Exam Schedule","exam_schedule")}
    for fn,(name,c) in cats.items():
        cc="".join(card(j) for j in jobs if j.get("category")==c)
        (ROOT/fn).write_text(pagehead(name,name)+f'<main class="wrap"><h1>{name}</h1><div class="grid">{cc or "<div class=post>No new updates in this category.</div>"}</div></main></body></html>',encoding="utf-8")

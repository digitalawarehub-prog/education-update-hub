"""Canonical post URL helpers with legacy-file compatibility."""
from __future__ import annotations
import hashlib,re,unicodedata
from pathlib import Path
BASE_URL="https://educationupdatehub.in"
ROOT_DIR=Path(__file__).resolve().parent.parent
POSTS_DIR=ROOT_DIR/"generated"/"posts"
REPLACEMENTS={"सरकारी":"government","नौकरी":"job","नौकरियां":"jobs","भर्ती":"recruitment","भर्तियां":"recruitments","रिक्ति":"vacancy","अधिसूचना":"notification","प्रवेश":"admit","पत्र":"card","परिणाम":"result","उत्तर":"answer","कुंजी":"key","छात्रवृत्ति":"scholarship","परीक्षा":"exam","पाठ्यक्रम":"syllabus","शिक्षक":"teacher","पुलिस":"police","वन":"forest","विभाग":"department","केंद्र":"central","राज्य":"state","उत्तराखंड":"uttarakhand","ऑनलाइन":"online","आवेदन":"application","अंतिम":"last","तिथि":"date","योजना":"scheme","विज्ञापन":"advertisement","अभ्यर्थी":"candidate"}
def safe(v,default=""): return default if v is None else str(v).strip()
def slugify(title,job=None):
    job=job or {}; original=safe(title) or "update"
    raw=re.sub(r"\{\{.*?\}\}","",original).strip().lower().replace("&"," and ")
    for src,dst in sorted(REPLACEMENTS.items(),key=lambda x:len(x[0]),reverse=True): raw=raw.replace(src,dst)
    raw=unicodedata.normalize("NFKD",raw).encode("ascii","ignore").decode("ascii")
    slug=re.sub(r"[^a-z0-9]+","-",raw); slug=re.sub(r"-+","-",slug).strip("-")
    jid=re.sub(r"[^a-z0-9]+","",safe(job.get("job_id")).lower())[-10:]
    if slug:
        slug=slug[:130].rstrip("-")
        if jid:return f"{slug}-{jid}"[:150].rstrip("-")
        if re.search(r"[^\x00-\x7f]",original): return f"{slug}-{hashlib.sha1(original.encode()).hexdigest()[:8]}"[:150].rstrip("-")
        return slug
    digest=hashlib.sha1((original+"|"+safe(job.get("job_id"))).encode()).hexdigest()[:10]
    return f"update-{digest}"
def stored_filename(job):
    raw=safe(job.get("html_file")).replace("\\","/"); marker="generated/posts/"
    if marker in raw:
        name=raw.split(marker,1)[1].split("/",1)[0]
        if name.endswith(".html") and Path(name).name==name and (POSTS_DIR/name).is_file(): return name
    return ""
def post_filename(job): return stored_filename(job) or f"{slugify(job.get('title',''),job)}.html"
def canonical_filename(job): return f"{slugify(job.get('title',''),job)}.html"
def post_relative_url(job): return f"generated/posts/{post_filename(job)}"
def post_site_url(job): return f"{BASE_URL}/generated/posts/{post_filename(job)}"
def post_path(job): return POSTS_DIR/post_filename(job)
def post_exists(job): return post_path(job).is_file()

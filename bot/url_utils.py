"""Canonical URL helpers for Education Update Hub.

Keeps current generated URLs consistent while preserving an already-existing
html_file when it is valid. This prevents category/home/search links from
pointing at a different slug than the file that was actually generated.
"""
import hashlib
import re
from pathlib import Path
from unidecode import unidecode

BASE_URL = "https://educationupdatehub.in"
ROOT_DIR = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT_DIR / "generated" / "posts"

REPLACEMENTS = {
    "सरकारी":"government", "नौकरी":"job", "नौकरियां":"jobs", "भर्ती":"recruitment",
    "भर्तियां":"recruitments", "रिक्ति":"vacancy", "रिक्तियां":"vacancies",
    "अधिसूचना":"notification", "प्रवेश":"admit", "पत्र":"card", "परिणाम":"result",
    "उत्तर":"answer", "कुंजी":"key", "छात्रवृत्ति":"scholarship", "परीक्षा":"exam",
    "पाठ्यक्रम":"syllabus", "शिक्षक":"teacher", "पुलिस":"police", "वन":"forest",
    "विभाग":"department", "केंद्र":"central", "राज्य":"state", "उत्तराखंड":"uttarakhand",
    "ऑनलाइन":"online", "आवेदन":"application", "अंतिम":"last", "तिथि":"date",
    "योजना":"scheme", "विज्ञापन":"advertisement", "अभ्यर्थी":"candidate",
}

def safe(value, default=""):
    if value is None:
        return default
    return str(value).strip()

def _generated_relative(value):
    value=safe(value).replace('\\','/')
    value=value.lstrip('/')
    if not value.startswith('generated/posts/') or not value.endswith('.html'):
        return ''
    if '..' in Path(value).parts:
        return ''
    return value

def slugify(title, job=None):
    job = job or {}
    original = safe(title) or "update"
    raw = re.sub(r"\{\{.*?\}\}", "", original).strip().lower().replace("&", " and ")
    for src,dst in sorted(REPLACEMENTS.items(), key=lambda x: len(x[0]), reverse=True):
        raw=raw.replace(src,dst)
    raw=unidecode(raw)
    slug=re.sub(r"[^a-z0-9]+","-",raw)
    slug=re.sub(r"-+","-",slug).strip("-")
    job_id=safe(job.get('job_id'))
    jid=re.sub(r"[^a-z0-9]+","",job_id.lower())[-10:]
    if slug:
        slug=slug[:135].rstrip('-')
        if jid:
            slug=f"{slug}-{jid}"
        elif len(original)!=len(slug) or re.search(r"[^\x00-\x7f]",original):
            slug=f"{slug}-{hashlib.sha1(original.encode('utf-8')).hexdigest()[:8]}"
        return slug[:150].rstrip('-')
    category=re.sub(r"[^a-z0-9]+","-",safe(job.get('category'),'update').lower()).strip('-') or 'update'
    year_match=re.findall(r"20\d{2}", original+' '+safe(job.get('year')))
    year=year_match[-1] if year_match else '2026'
    digest=hashlib.sha1((original+'|'+job_id).encode('utf-8')).hexdigest()[:10]
    return f"{category}-{year}-{jid or digest}"[:150].rstrip('-')

def post_filename(job):
    return slugify(job.get('title',''),job)+'.html'

def post_relative_url(job):
    # Prefer a valid filename already assigned by generate_post().
    existing=_generated_relative(job.get('html_file'))
    if existing and (ROOT_DIR/existing).is_file():
        return existing
    return f"generated/posts/{post_filename(job)}"

def post_site_url(job):
    return f"{BASE_URL}/{post_relative_url(job).lstrip('/')}"

def post_path(job):
    existing=_generated_relative(job.get('html_file'))
    if existing and (ROOT_DIR/existing).is_file():
        return ROOT_DIR/existing
    return POSTS_DIR/post_filename(job)

def post_exists(job):
    return post_path(job).is_file()

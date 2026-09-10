from pathlib import Path
from html import escape
import re
ROOT=Path(__file__).resolve().parent.parent
FILE=ROOT/'archive.html'
def fmt(v):
 s=str(v or '')
 m=re.search(r'(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})',s)
 return f'{int(m.group(3)):02d}-{int(m.group(2)):02d}-{int(m.group(1)):04d}' if m else s

def build_archive(jobs):
 jobs=sorted(jobs or [],key=lambda j:str(j.get('site_published_at') or j.get('publish_date') or j.get('notification_date') or ''),reverse=True)
 cards=[]
 for j in jobs:
  rel=str(j.get('html_file') or '').replace('\\','/')
  if not rel.startswith('generated/posts/'):
   slug=str(j.get('slug') or '')
   rel=f'generated/posts/{slug}.html' if slug else '#'
  title=escape(str(j.get('title') or 'Update')); cat=escape(str(j.get('category') or 'Archive')); pub=fmt(j.get('notification_date') or j.get('publish_date') or j.get('site_published_at')); last=fmt(j.get('last_date')); summary=escape(str(j.get('summary') or j.get('description') or '')[:500])
  cards.append('<article class="card"><span class="badge">'+cat+'</span><h2><a href="/'+escape(rel.lstrip('/'))+'">'+title+'</a></h2><div class="meta">Published: '+escape(pub or 'उपलब्ध नहीं')+(' | Last Date: '+escape(last) if last else '')+'</div><b class="closed">Application Closed</b><p>'+summary+'</p><a class="read" href="/'+escape(rel.lstrip('/'))+'">Read Full Update →</a></article>')
 css='''<style>body{margin:0;background:#f5f8fc;font-family:Arial,sans-serif;color:#172033}.wrap{max-width:1100px;margin:25px auto;padding:0 15px}.intro{background:#fff;padding:18px;border-radius:14px;margin-bottom:20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}.card{background:#fff;padding:20px;border:1px solid #e5eaf1;border-radius:14px;box-shadow:0 3px 14px #0001}.badge{background:#eaf2ff;color:#0754a6;padding:6px 10px;border-radius:18px}.card h2 a{color:#172033;text-decoration:none}.meta{color:#68758a;font-size:13px;margin:10px 0}.closed{display:inline-block;background:#eee;color:#666;padding:6px 10px;border-radius:6px}.read{display:inline-block;background:#126ee8;color:#fff;padding:10px 14px;border-radius:8px;text-decoration:none}</style>'''
 FILE.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Archive - Education Update Hub</title>'+css+'</head><body><div id="header"></div><main class="wrap"><h1>📁 Archived Updates</h1><div class="intro">जिन अपडेट/भर्तियों की आवेदन अंतिम तिथि समाप्त हो चुकी है, वे यहां रहेंगी। इन पोस्ट पर <b>Application Closed</b> status दिखेगा।</div><section class="grid">'+(''.join(cards) or '<div class="intro">अभी कोई archived update नहीं है।</div>')+'</section></main><div id="footer"></div><script src="load.js"></script></body></html>',encoding='utf8')
 return FILE

from __future__ import annotations
import json, logging, os, re, time, requests, io
from bs4 import BeautifulSoup
try:
    import fitz
except Exception:
    fitz = None
log=logging.getLogger('EUH_AI')
API='https://openrouter.ai/api/v1/chat/completions'
MODEL=os.getenv('OPENROUTER_MODEL','openrouter/free')
KEY=os.getenv('OPENROUTER_API_KEY','').strip()
BAD={'','not mentioned','not available','check notification','check official notification','as per rules','उपलब्ध नहीं','आधिकारिक अधिसूचना देखें','n/a','na','none','null','.'}
MONTH={'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,'may':5,'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'sept':9,'september':9,'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12}

def clean(v):
    s=str(v or '').strip()
    for a,b in [('â€“','–'),('â€”','—'),('â€˜','‘'),('â€™','’'),('â€œ','“'),('â€�','”'),('â€¦','…'),('�','')]: s=s.replace(a,b)
    return re.sub(r'\s+',' ',s).strip()

def real(v): return clean(v).casefold() not in BAD

def source_text(job):
    """Get the actual notice/detail text used by AI. Supports HTML and PDF URLs.
    Scraper records often contain only a title+URL, so AI must fetch the detail
    page itself instead of silently producing an empty/weak post.
    """
    text=clean(job.get('notification_text') or job.get('content') or job.get('description'))
    url=clean(job.get('notification_pdf') or job.get('url'))
    if len(text)<120 and url:
        try:
            r=requests.get(url,timeout=(8,30),headers={'User-Agent':'Mozilla/5.0 Education Update Hub'})
            r.raise_for_status()
            ctype=(r.headers.get('Content-Type') or '').lower()
            is_pdf='application/pdf' in ctype or r.content[:4]==b'%PDF' or url.lower().split('#',1)[0].endswith('.pdf')
            if is_pdf:
                if fitz:
                    doc=fitz.open(stream=r.content,filetype='pdf')
                    pages=[]
                    for i,page in enumerate(doc):
                        pages.append(page.get_text('text') or '')
                        if sum(len(x) for x in pages)>=30000: break
                    text=clean(' '.join(pages))
                else:
                    text=''
            else:
                ss=BeautifulSoup(r.text,'html.parser')
                for x in ss(['script','style','noscript','svg','nav','footer','header']): x.decompose()
                text=clean(ss.get_text(' ',strip=True))
        except Exception as exc:
            log.warning('Source fetch failed | %s | %s', url, exc.__class__.__name__)
    return text[:30000]

def classify(title):
    t=clean(title).casefold()
    if any(x in t for x in ('admit card','admit-card','hall ticket','call letter','e-admit','प्रवेश पत्र')): return 'admit-card','Admit Card'
    if any(x in t for x in ('answer key','answer-key','answerkey','उत्तर कुंजी','उत्तरकुंजी')): return 'answer-key','Answer Key'
    if re.search(r'\b(result|results|merit list|score card|scorecard)\b',t) or 'परिणाम' in t: return 'result','Result'
    if 'syllabus' in t or 'पाठ्यक्रम' in t: return 'syllabus','Syllabus'
    if 'scholarship' in t or 'छात्रवृत्ति' in t: return 'scholarship','Scholarship'
    if any(x in t for x in ('entrance exam','entrance test','admission test','प्रवेश परीक्षा')): return 'entrance','Entrance Exam'
    if any(x in t for x in ('walk-in interview','walk in interview','interview schedule','interview','साक्षात्कार')): return 'interview','Interview'
    if any(x in t for x in ('examination schedule','exam schedule','exam date','examination date','schedule updated','important notice','notice regarding','regarding the examination','परीक्षा के आयोजन','परीक्षा तिथि','महत्वपूर्ण सूचना','सूचना')) and not any(x in t for x in ('applications are invited','application invited','apply online','online application','आवेदन आमंत्रित','ऑनलाइन आवेदन')): return 'notice','Notice'
    if any(x in t for x in ('recruitment','vacancy','vacancies','applications are invited','application invited','apply online','engagement of','appointment of','भर्ती','रिक्ति','आवेदन आमंत्रित')): return 'recruitment','Recruitment'
    return 'notice','Notice'

def parse_json(v):
    if isinstance(v,dict): return v
    s=clean(v)
    if not s:return {}
    s=re.sub(r'^```(?:json)?\s*|\s*```$','',s,flags=re.I|re.S).strip()
    try:return json.loads(s)
    except: pass
    m=re.search(r'\{.*\}',s,re.S)
    if m:
        try:return json.loads(m.group(0))
        except: pass
    return {}

def normalize_date(v):
    s=clean(v)
    if not real(s): return ''
    def f(m):
        a,b,c=m.groups()
        if len(a)==4:return f'{int(c):02d}-{int(b):02d}-{int(a):04d}'
        if b.isdigit():return f'{int(a):02d}-{int(b):02d}-{int(c):04d}'
        n=MONTH.get(b.lower().strip('.'))
        return f'{int(a):02d}-{n:02d}-{int(c):04d}' if n else m.group(0)
    s=re.sub(r'\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b',f,s)
    s=re.sub(r'\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})\b',f,s)
    s=re.sub(r'\b(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember|t)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(20\d{2})\b',f,s,flags=re.I)
    return s

def call(prompt):
    headers={
        'Authorization':f'Bearer {KEY}',
        'Content-Type':'application/json',
        'HTTP-Referer':'https://educationupdatehub.in',
        'X-Title':'Education Update Hub'
    }
    base={
        'model':MODEL,
        'messages':[
            {'role':'system','content':'Return only one valid JSON object. No markdown.'},
            {'role':'user','content':prompt}
        ],
        'temperature':0.1,
        'max_tokens':2200
    }
    # Some free OpenRouter providers/models do not implement response_format.
    # Try structured JSON first, then retry once without that optional field.
    payload=dict(base)
    payload['response_format']={'type':'json_object'}
    r=requests.post(API,headers=headers,json=payload,timeout=50)
    if r.status_code==429:
        raise RuntimeError('OPENROUTER_RATE_LIMIT')
    if r.status_code==400:
        try:
            err=r.json()
            msg=str(err.get('error',{}).get('message','')).lower()
        except Exception:
            msg=''
        if 'response_format' in msg or 'json' in msg or 'unsupported' in msg:
            r=requests.post(API,headers=headers,json=base,timeout=50)
    r.raise_for_status()
    data=r.json()
    msg=((data.get('choices') or [{}])[0].get('message') or {})
    content=msg.get('content')
    if isinstance(content,list):
        content=''.join(
            str(x.get('text','')) for x in content if isinstance(x,dict)
        )
    if not content:
        return {}
    return parse_json(content)

def enrich(job):
    if not KEY: raise RuntimeError('OPENROUTER_API_KEY_MISSING')
    source=source_text(job)
    if len(source)<120: raise RuntimeError('AI_SOURCE_TOO_SHORT')
    forced,forced_cat=classify(job.get('title'))
    prompt=f'''You are the human editor of Education Update Hub. Use ONLY the source text.
Rules: examination schedule/date/important notice = Notice unless it actually invites applications; walk-in/interview = Interview; admit card/result/answer key/syllabus/scholarship/entrance keep their own type; recruitment only for genuine vacancy/application/engagement. Never invent. Missing fields must be empty. Department must be the actual organization/commission/department, never the word Government. Preserve every useful official URL. All dates must be DD-MM-YYYY.
Write a genuinely human editorial post, not a data dump: natural SEO title, 2-4 sentence original summary, a useful 2-4 paragraph intro, 5-8 concise key points, practical how-to steps, 3-6 important notes, and 4-6 specific FAQs. Do not use generic filler such as 'candidates are advised to check the official website' unless it adds a real instruction. The table fields must be extracted from the source wherever present: vacancy, qualification, salary, age_limit, application_fee, selection_process, exam_date, application_start_date, last_date, notification_date. If a value is not explicitly available, return an empty string rather than guessing.
Existing title: {clean(job.get('title'))}
URL: {clean(job.get('url'))}
Forced type: {forced}
SOURCE:
{source}
Return JSON keys: title,summary,category,post_type,department,vacancy,qualification,salary,age_limit,application_fee,selection_process,exam_date,application_start_date,last_date,notification_date,intro,key_points,how_to,important_notes,faq. FAQ is an array of objects with question and answer.'''
    ai={}
    for _ in range(2):
        ai=call(prompt)
        if ai: break
        time.sleep(.5)
    if not ai: raise RuntimeError('AI_INVALID_JSON')
    # A valid JSON response is not enough: require the editorial sections that
    # make the published article genuinely human-readable. Retry once with a
    # focused repair prompt if the provider returned only a title/summary.
    rich_ok = bool(clean(ai.get('intro'))) and isinstance(ai.get('key_points'), list) and len(ai.get('key_points') or []) >= 3
    if not rich_ok:
        repair = prompt + "\nIMPORTANT: Your previous output was too thin. Return the same JSON again with a real intro, at least 5 useful key_points, how_to, important_notes and 4 FAQs. Do not leave these sections empty when the source contains relevant information."
        ai2=call(repair)
        if ai2: ai=ai2
    out=dict(job); typ,cat=classify(ai.get('title') or job.get('title'))
    if forced in {'notice','interview','admit-card','result','answer-key','syllabus','scholarship','entrance'}: typ,cat=forced,forced_cat
    out['post_type']=typ; out['category']=cat
    for k in ('title','summary','department','vacancy','qualification','salary','age_limit','application_fee','selection_process','exam_date','application_start_date','last_date','notification_date','intro','how_to'):
        v=clean(ai.get(k))
        if v: out[k]=normalize_date(v) if k in {'exam_date','application_start_date','last_date','notification_date'} else v
    if not out.get('title') or not out.get('summary'): raise RuntimeError('AI_EMPTY_CONTENT')
    for k in ('key_points','important_notes','faq'):
        if isinstance(ai.get(k),list): out[k]=ai[k]
    # Deterministic extraction is the safety net for the information table.
    # It prevents a good AI article from publishing with an empty table when
    # the model omitted a field that is clearly present in the notice/PDF.
    try:
        from structured_details import extract_details
        fallback=extract_details({**job, **out, 'content': source})
    except Exception:
        fallback={}
    for k in ('vacancy','qualification','salary','age_limit','application_fee','selection_process','exam_date','application_start_date','last_date','notification_date'):
        if not real(out.get(k)) and real(fallback.get(k)):
            out[k]=clean(fallback.get(k))
        if not real(out.get(k)): out[k]=''
    out['url']=clean(job.get('url')); out['apply_link']=clean(job.get('apply_link')); out['notification_pdf']=clean(job.get('notification_pdf')); out['official_website']=clean(job.get('official_website')) or out['url']; out['ai_generated']=True; out['ai_model']=MODEL
    return out

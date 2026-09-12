from __future__ import annotations
import json, logging, os, re, time, requests
from bs4 import BeautifulSoup
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
    text=clean(job.get('content') or job.get('description'))
    url=clean(job.get('url'))
    if len(text)<120 and url and not url.lower().endswith('.pdf'):
        try:
            r=requests.get(url,timeout=25,headers={'User-Agent':'Mozilla/5.0 Education Update Hub'})
            r.raise_for_status(); s=BeautifulSoup(r.text,'html.parser')
            for x in s(['script','style','noscript','svg','nav','footer','header']): x.decompose()
            text=clean(s.get_text(' ',strip=True))
        except Exception: pass
    return text[:18000]

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
Rules: examination schedule/date/important notice = Notice unless it actually invites applications; walk-in/interview = Interview; admit card/result/answer key/syllabus/scholarship/entrance keep their own type; recruitment only for genuine vacancy/application/engagement. Never invent. Missing fields must be empty. Department must be actual organization/commission/department, never Government. Preserve URLs. All dates DD-MM-YYYY. Write a natural SEO title and a human-written 2-4 sentence summary. Also create useful intro, key_points, how_to, important_notes and FAQ from the source, without filler.
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
    out=dict(job); typ,cat=classify(ai.get('title') or job.get('title'))
    if forced in {'notice','interview','admit-card','result','answer-key','syllabus','scholarship','entrance'}: typ,cat=forced,forced_cat
    out['post_type']=typ; out['category']=cat
    for k in ('title','summary','department','vacancy','qualification','salary','age_limit','application_fee','selection_process','exam_date','application_start_date','last_date','notification_date','intro','how_to'):
        v=clean(ai.get(k))
        if v: out[k]=normalize_date(v) if k in {'exam_date','application_start_date','last_date','notification_date'} else v
    if not out.get('title') or not out.get('summary'): raise RuntimeError('AI_EMPTY_CONTENT')
    for k in ('key_points','important_notes','faq'):
        if isinstance(ai.get(k),list): out[k]=ai[k]
    for k in ('vacancy','qualification','salary','age_limit','application_fee','selection_process','exam_date','application_start_date','last_date','notification_date'):
        if not real(out.get(k)): out[k]=''
    out['url']=clean(job.get('url')); out['apply_link']=clean(job.get('apply_link')); out['notification_pdf']=clean(job.get('notification_pdf')); out['official_website']=clean(job.get('official_website')) or out['url']; out['ai_generated']=True; out['ai_model']=MODEL
    return out

# ==========================================================
# EHU QUALITY GUARD (final)
# ==========================================================

def _salary_verified(ai_value, source):
    """Return salary only when the same pay information is supported by source."""
    v = clean(ai_value)
    src = clean(source)
    if not v or len(v) > 180:
        return ''
    low = v.casefold()
    bad = ('application fee', 'exam fee', 'registration fee', 'essential qualification',
           'conditions of service', 'and other conditions', 'click here', 'stipulated dates')
    if any(x in low for x in bad):
        return ''

    # Pay-level salary (e.g. Level-7) must actually occur in the source.
    lm = re.search(r'\blevel\s*[-–]?\s*(\d+[a-z]?)\b', v, re.I)
    if lm:
        level = lm.group(1).casefold()
        if not re.search(rf'\blevel\s*[-–]?\s*{re.escape(level)}\b', src, re.I):
            return ''
        return v

    # Monetary salary: reject tiny values that are overwhelmingly likely to be fees.
    nums = [int(re.sub(r'[^0-9]', '', n)) for n in re.findall(r'(?:₹|rs\.?|inr|रु\.?)\s*([0-9][0-9,]*)', v, re.I)]
    if not nums or any(n < 1000 for n in nums):
        return ''

    # Every monetary value in the AI answer should exist in the source and be near
    # an explicit pay/salary/remuneration heading.
    for n in nums:
        if not re.search(rf'(?<!\d){n:,}(?!\d)|(?<!\d){n}(?!\d)', src):
            return ''
    if not re.search(r'(?:pay\s*scale|scale\s+of\s+pay|basic\s+pay|pay\s*level|pay\s*matrix|salary|remuneration|consolidated\s+pay|emoluments?|stipend|वेतनमान|वेतन\s*स्तर|वेतन|मानदेय|पारिश्रमिक)', src, re.I):
        return ''
    return v


def _quality_ok(out, source):
    title = clean(out.get('title'))
    summary = clean(out.get('summary'))
    intro = clean(out.get('intro'))
    how = clean(out.get('how_to'))
    if len(title) < 18 or len(summary) < 80 or len(intro) < 80 or len(how) < 50:
        return False
    if _ehu_corrupt_text(summary) or _ehu_corrupt_text(intro) or _ehu_corrupt_text(how):
        return False
    points = out.get('key_points')
    if not isinstance(points, list) or len([x for x in points if clean(x)]) < 4:
        return False
    faq = out.get('faq')
    if not isinstance(faq, list) or len([x for x in faq if isinstance(x, dict) and clean(x.get('question')) and clean(x.get('answer'))]) < 3:
        return False
    # No obvious raw extraction garbage.
    blob = ' '.join([summary, intro] + [clean(x) for x in points if x])
    if any(x in blob.casefold() for x in ('support_agent', 'go to index', 'previous button', '�', 'â€', 'à¤')):
        return False
    return True


def _finalize_ai(job, ai, source):
    forced, forced_cat = classify(job.get('title'))
    out = dict(job)
    typ, cat = classify(ai.get('title') or job.get('title'))
    if forced in {'notice','interview','admit-card','result','answer-key','syllabus','scholarship','entrance'}:
        typ, cat = forced, forced_cat
    out['post_type'] = typ
    out['category'] = cat
    for k in ('title','summary','department','vacancy','qualification','salary','age_limit','application_fee',
              'selection_process','exam_date','application_start_date','last_date','notification_date','intro','how_to'):
        v = clean(ai.get(k))
        if v:
            out[k] = normalize_date(v) if k in {'exam_date','application_start_date','last_date','notification_date'} else v
    for k in ('key_points','important_notes','faq'):
        if isinstance(ai.get(k), list):
            out[k] = ai[k]

    out['salary'] = _salary_verified(out.get('salary'), source)
    if not _quality_ok(out, source):
        raise RuntimeError('AI_LOW_VALUE_CONTENT')

    # Remove unsafe factual fields rather than showing AI/OCR garbage.
    for k in ('department','vacancy','qualification','age_limit','application_fee','selection_process',
              'exam_date','application_start_date','last_date','notification_date'):
        if _ehu_corrupt_text(out.get(k)):
            out[k] = ''
    out['key_points'] = [_ehu_safe(x) for x in out.get('key_points', []) if _ehu_safe(x)][:7]
    out['important_notes'] = [_ehu_safe(x) for x in out.get('important_notes', []) if _ehu_safe(x)][:6]
    out['faq'] = [
        {'question': _ehu_safe(x.get('question')), 'answer': _ehu_safe(x.get('answer'))}
        for x in out.get('faq', []) if isinstance(x, dict) and _ehu_safe(x.get('question')) and _ehu_safe(x.get('answer'))
    ][:5]
    if len(out['faq']) < 3:
        raise RuntimeError('AI_LOW_VALUE_CONTENT')
    out['title'] = clean(out.get('title') or job.get('title'))
    out['url'] = clean(job.get('url'))
    out['apply_link'] = clean(job.get('apply_link'))
    out['notification_pdf'] = clean(job.get('notification_pdf') or job.get('official_notification_pdf'))
    out['official_website'] = clean(job.get('official_website')) or out['url']
    out['ai_generated'] = True
    out['ai_model'] = MODEL
    return out


def _quality_batch_prompt(items):
    blocks = []
    for idx, job in enumerate(items, 1):
        source = source_text(job)[:5200]
        forced, _ = classify(job.get('title'))
        blocks.append(
            f'POST {idx}\nTITLE: {clean(job.get("title"))}\nURL: {clean(job.get("url"))}\nTYPE: {forced}\nSOURCE:\n{source}'
        )
    return '''You are the senior human editor of Education Update Hub. Create one ORIGINAL, useful website article record for each POST. Use ONLY the supplied source. Do not invent or guess any factual detail.

IMPORTANT QUALITY RULES:
- This is a human-readable editorial article, NOT a PDF dump or OCR rewrite.
- Explain what the update means for a reader, then present the verified facts clearly.
- summary must be at least 2 natural sentences; intro must be a useful paragraph; provide 4-7 specific key points, a practical how_to paragraph, 3-5 useful FAQs, and important_notes.
- Do not use filler such as “in this article we will discuss” repeatedly.
- Salary/pay must be copied only when the source explicitly gives pay scale, pay level, salary, remuneration, stipend or emoluments. Never confuse application/exam fee with salary. If absent, return an empty salary.
- Vacancy, qualification, age, fee and dates must be supported by the source. Never invent.
- A recruitment post must remain a recruitment post only if the source actually concerns a vacancy/application/engagement.
- Never turn selected/qualified candidates, results, exam schedules, previous-year papers, score pages or notices into recruitment articles.
- Dates must be DD-MM-YYYY.
- Return ONLY JSON: {"posts":[...]} and exactly one object per POST.

Fields: title, summary, category, post_type, department, vacancy, qualification, salary, age_limit, application_fee, selection_process, exam_date, application_start_date, last_date, notification_date, intro, key_points, how_to, important_notes, faq.

''' + '\n\n'.join(blocks)


def _call_quality_batch(items):
    headers = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json',
               'HTTP-Referer': 'https://educationupdatehub.in', 'X-Title': 'Education Update Hub'}
    payload = {
        'model': MODEL,
        'messages': [
            {'role': 'system', 'content': 'Return only one valid JSON object. No markdown.'},
            {'role': 'user', 'content': _quality_batch_prompt(items)},
        ],
        'temperature': 0.15,
        'max_tokens': 4200 if len(items) <= 2 else 6000,
        'response_format': {'type': 'json_object'},
    }
    r = requests.post(API, headers=headers, json=payload, timeout=90)
    if r.status_code == 429:
        raise RuntimeError('OPENROUTER_RATE_LIMIT')
    if r.status_code == 400:
        try:
            msg = str(r.json().get('error', {}).get('message', '')).lower()
        except Exception:
            msg = ''
        if 'response_format' in msg or 'json' in msg or 'unsupported' in msg:
            payload.pop('response_format', None)
            r = requests.post(API, headers=headers, json=payload, timeout=90)
    if r.status_code == 429:
        raise RuntimeError('OPENROUTER_RATE_LIMIT')
    r.raise_for_status()
    data = r.json()
    content = ((data.get('choices') or [{}])[0].get('message') or {}).get('content')
    if isinstance(content, list):
        content = ''.join(str(x.get('text', '')) for x in content if isinstance(x, dict))
    obj = parse_json(content)
    posts = obj.get('posts') if isinstance(obj, dict) else None
    if not isinstance(posts, list) or len(posts) != len(items):
        raise RuntimeError(f'AI_BATCH_INCOMPLETE:{len(posts) if isinstance(posts, list) else 0}/{len(items)}')
    return posts


def enrich_many(jobs, target=5):
    jobs = list(jobs or [])
    if not KEY:
        raise RuntimeError('OPENROUTER_API_KEY_MISSING')
    made = []
    # Small batches reduce truncation and make the free-tier request more reliable.
    idx = 0
    while idx < len(jobs) and len(made) < target:
        batch = jobs[idx:idx+2]
        idx += 2
        try:
            ai_posts = _call_quality_batch(batch)
        except RuntimeError as exc:
            if str(exc) == 'AI_BATCH_INCOMPLETE:0/2' and len(batch) == 2:
                # One retry as individual posts; no local/template fallback.
                ai_posts = []
                for item in batch:
                    ai_posts.extend(_call_quality_batch([item]))
            else:
                raise
        for job, ai in zip(batch, ai_posts):
            try:
                made.append(_finalize_ai(job, ai, source_text(job)))
                if len(made) >= target:
                    break
            except RuntimeError as exc:
                log.warning('AI candidate rejected | %s | %s', job.get('title'), exc)
        if idx >= len(jobs) and len(made) < target:
            break
    if len(made) != target:
        raise RuntimeError(f'AI_TARGET_NOT_REACHED:{len(made)}/{target}')
    return made

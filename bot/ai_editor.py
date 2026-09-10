from __future__ import annotations
import io, json, logging, os, re, time, requests
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
    for candidate in (s, re.sub(r',\s*([}\]])',r'\1',s)):
        try:return json.loads(candidate)
        except Exception: pass
    # Extract the largest JSON object without assuming the model put markdown around it.
    start=s.find('{'); end=s.rfind('}')
    if start>=0 and end>start:
        frag=s[start:end+1]
        for candidate in (frag, re.sub(r',\s*([}\]])',r'\1',frag)):
            try:return json.loads(candidate)
            except Exception: pass
    return {}

def normalize_date(v):
    s=clean(v)
    if not real(s): return ''
    def f(m):
        a,b,c=m.groups()
        if len(a)==4:return f'{int(c):02d}-{int(b):02d}-{int(a):04d}'
        if b.isdigit():return f'{int(a):02d}-{int(b):02d}-{int(c):04d}'
        n=MONTH.get(b.lower().strip('.')); return f'{int(a):02d}-{n:02d}-{int(c):04d}' if n else m.group(0)
    s=re.sub(r'\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b',f,s)
    s=re.sub(r'\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})\b',f,s)
    s=re.sub(r'\b(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember|t)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(20\d{2})\b',f,s,flags=re.I)
    return s

def fetch_pdf_text(url):
    if not url:return ''
    try:
        r=requests.get(url,timeout=(5,25),headers={'User-Agent':'Mozilla/5.0 Education Update Hub','Accept':'application/pdf,*/*;q=0.8'},verify=False)
        if r.status_code>=400 or r.content[:4]!=b'%PDF': return ''
        if fitz is None:return ''
        doc=fitz.open(stream=r.content,filetype='pdf')
        text=clean(' '.join((p.get_text('text') or '') for p in list(doc)[:20]))
        return text[:24000]
    except Exception as e:
        log.warning('AI PDF fetch failed | %s | %s',url,e.__class__.__name__)
        return ''

def source_text(job):
    parts=[]
    for k in ('notification_text','content','description','raw_text','body','text'):
        t=clean(job.get(k))
        if t: parts.append(t)
    text=clean(' '.join(parts))
    pdf=clean(job.get('notification_pdf') or job.get('official_notification_pdf'))
    if len(text)<2500 and pdf and not pdf.startswith(('javascript:','#')):
        pt=fetch_pdf_text(pdf)
        if pt: text=clean(text+' '+pt)
    url=clean(job.get('url'))
    if len(text)<500 and url and not url.lower().split('#',1)[0].endswith('.pdf'):
        try:
            r=requests.get(url,timeout=15,headers={'User-Agent':'Mozilla/5.0 Education Update Hub'},verify=False)
            r.raise_for_status(); s=BeautifulSoup(r.text,'html.parser')
            for x in s(['script','style','noscript','svg','nav','footer','header']): x.decompose()
            text=clean(text+' '+s.get_text(' ',strip=True))
        except Exception: pass
    return text[:26000]

def first_match(text, patterns, maxlen=500):
    for p in patterns:
        m=re.search(p,text,re.I)
        if m:
            v=clean(m.group(1))
            if v and len(v)<=maxlen:return v
    return ''

def extract_fields(text):
    t=clean(text)
    out={}
    out['vacancy']=first_match(t,[r'(?:total\s+(?:number\s+of\s+)?(?:vacancies|posts)|number\s+of\s+vacancies|total\s+vacancies|total\s+posts)\s*[:\-–]?\s*(\d{1,6})',r'\b(\d{1,6})\s+(?:posts?|vacancies|vacant posts?)\b',r'(?:कुल\s*)?(?:रिक्त\s*पद|पदों\s*की\s*संख्या|कुल\s*पद|रिक्तियां)\s*[:\-–]?\s*(\d{1,6})'],50)
    out['qualification']=first_match(t,[r'(?:essential\s+)?(?:educational\s+)?qualification\s*[:\-–]\s*(.{3,500}?)(?=\s+(?:age|experience|salary|pay\s*scale|selection|fee|last\s+date)\b)',r'eligibility(?:\s+criteria)?\s*[:\-–]\s*(.{3,500}?)(?=\s+(?:age|experience|salary|selection|fee|last\s+date)\b)',r'(?:शैक्षणिक\s*)?(?:योग्यता|अर्हता)\s*[:\-–]\s*(.{3,500}?)(?=\s+(?:आयु|अनुभव|वेतन|चयन|शुल्क|अंतिम)\b)'])
    out['salary']=first_match(t,[r'(?:salary|pay\s*scale|remuneration|pay\s+level)\s*[:\-–]\s*(.{2,300}?)(?=\s+(?:age|qualification|selection|fee|last\s+date)\b)',r'(?:वेतन|मानदेय|वेतनमान|पे\s*लेवल)\s*[:\-–]\s*(.{2,300}?)(?=\s+(?:आयु|योग्यता|चयन|शुल्क|अंतिम)\b)'])
    out['age_limit']=first_match(t,[r'(?:age\s*limit|age\s*criteria|upper\s+age\s+limit|maximum\s+age)\s*[:\-–]?\s*(.{2,220}?)(?=\s+(?:salary|qualification|experience|fee|selection|last\s+date)\b)',r'(?:आयु\s*सीमा|उम्र\s*सीमा|अधिकतम\s*आयु)\s*[:\-–]?\s*(.{2,220}?)(?=\s+(?:वेतन|योग्यता|अनुभव|शुल्क|चयन|अंतिम)\b)'])
    out['application_fee']=first_match(t,[r'(?:application\s+fee|examination\s+fee|exam\s+fee|fee)\s*[:\-–]?\s*(.{2,220}?)(?=\s+(?:selection|last\s+date|age|qualification)\b)',r'(?:आवेदन\s*शुल्क|परीक्षा\s*शुल्क)\s*[:\-–]?\s*(.{2,220}?)(?=\s+(?:चयन|अंतिम|आयु|योग्यता)\b)'])
    out['selection_process']=first_match(t,[r'(?:selection\s*process|selection\s*procedure|mode\s+of\s+selection)\s*[:\-–]?\s*(.{2,280}?)(?=\s+(?:exam|fee|last\s+date|age|salary)\b)',r'(?:चयन\s*प्रक्रिया|चयन\s*पद्धति)\s*[:\-–]?\s*(.{2,280}?)(?=\s+(?:परीक्षा|शुल्क|अंतिम|आयु|वेतन)\b)'])
    date_patterns={
      'last_date':[r'(?:last\s+date|deadline|closing\s+date|last\s+date\s+to\s+apply|closure\s+of\s+(?:online\s+)?registration)\s*[:\-–]?\s*([^|;<]{3,80})',r'(?:अंतिम\s*तिथि|अंतिम\s*तारीख|आवेदन\s*की\s*अंतिम\s*तिथि)\s*[:\-–]?\s*([^|;<]{3,80})'],
      'application_start_date':[r'(?:application\s+start\s+date|start\s+date|commencement\s+of\s+(?:online\s+)?registration)\s*[:\-–]?\s*([^|;<]{3,80})',r'(?:आवेदन\s*प्रारंभ|आवेदन\s*आरंभ\s*तिथि)\s*[:\-–]?\s*([^|;<]{3,80})'],
      'exam_date':[r'(?:exam(?:ination)?\s+date|date\s+of\s+exam)\s*[:\-–]?\s*([^|;<]{3,80})',r'(?:परीक्षा\s*तिथि|परीक्षा\s*दिनांक)\s*[:\-–]?\s*([^|;<]{3,80})']}
    for k,ps in date_patterns.items(): out[k]=normalize_date(first_match(t,ps,120))
    return {k:v for k,v in out.items() if real(v)}

def call(prompt, compact=False):
    headers={'Authorization':f'Bearer {KEY}','Content-Type':'application/json','HTTP-Referer':'https://educationupdatehub.in','X-Title':'Education Update Hub'}
    base={'model':MODEL,'messages':[{'role':'system','content':'You are a strict JSON API. Return ONLY one valid JSON object. Double quotes only. No markdown, no comments, no trailing commas.'},{'role':'user','content':prompt}], 'temperature':0.0,'max_tokens':1700 if compact else 2400}
    for use_format in (True,False):
        payload=dict(base)
        if use_format: payload['response_format']={'type':'json_object'}
        try:
            r=requests.post(API,headers=headers,json=payload,timeout=55)
        except requests.RequestException as e:
            raise RuntimeError(f'OPENROUTER_NETWORK_{e.__class__.__name__}')
        if r.status_code==429: raise RuntimeError('OPENROUTER_RATE_LIMIT')
        if r.status_code==400 and use_format: continue
        r.raise_for_status()
        data=r.json(); msg=((data.get('choices') or [{}])[0].get('message') or {}); content=msg.get('content')
        if isinstance(content,list): content=''.join(str(x.get('text','')) for x in content if isinstance(x,dict))
        parsed=parse_json(content)
        if parsed:return parsed
        if not use_format: return {}
    return {}

def enrich(job):
    if not KEY: raise RuntimeError('OPENROUTER_API_KEY_MISSING')
    source=source_text(job)
    if len(source)<120: raise RuntimeError('AI_SOURCE_TOO_SHORT')
    forced,forced_cat=classify(job.get('title'))
    prompt=f'''Write a genuinely useful, human-edited government-job/update article data package for Education Update Hub. Use ONLY the supplied source. Never invent a fact. Empty string is allowed for a field that is genuinely absent. The final article should not sound like a template: summary 2-4 natural sentences; intro 2-3 natural sentences; key_points 4-7 concise factual bullets; how_to 3-6 practical steps when applicable; important_notes 2-5 factual notes; FAQ 3-5 source-grounded Q&A. Preserve official URLs. Dates DD-MM-YYYY. Department must be the actual organization/commission, not the word Government. For recruitment, fill vacancy/qualification/salary/age/fee/selection whenever stated in the source.
TITLE: {clean(job.get('title'))}
URL: {clean(job.get('url'))}
PDF: {clean(job.get('notification_pdf'))}
TYPE: {forced}
SOURCE:
{source}
Return exactly these JSON keys: title,summary,category,post_type,department,vacancy,qualification,salary,age_limit,application_fee,selection_process,exam_date,application_start_date,last_date,notification_date,intro,key_points,how_to,important_notes,faq. FAQ must be an array of objects with question and answer.'''
    ai=call(prompt)
    if not ai:
        compact_prompt=f'''Return only valid JSON. Summarize this official update without inventing facts. Keys: title,summary,department,vacancy,qualification,salary,age_limit,application_fee,selection_process,exam_date,application_start_date,last_date,intro,key_points,how_to,important_notes,faq. Keep values short. FAQ array of question/answer objects. SOURCE: {source[:14000]}'''
        ai=call(compact_prompt,compact=True)
    if not ai: raise RuntimeError('AI_INVALID_JSON')
    fallback=extract_fields(source)
    out=dict(job)
    typ,cat=classify(ai.get('title') or job.get('title'))
    if forced in {'notice','interview','admit-card','result','answer-key','syllabus','scholarship','entrance'}: typ,cat=forced,forced_cat
    out['post_type']=typ; out['category']=cat
    fields=('title','summary','department','vacancy','qualification','salary','age_limit','application_fee','selection_process','exam_date','application_start_date','last_date','notification_date','intro','how_to')
    for k in fields:
        v=clean(ai.get(k))
        if not real(v): v=clean(fallback.get(k))
        if v: out[k]=normalize_date(v) if k in {'exam_date','application_start_date','last_date','notification_date'} else v
    for k in ('key_points','important_notes','faq'):
        if isinstance(ai.get(k),list) and ai[k]: out[k]=ai[k]
    if not out.get('title'): out['title']=clean(job.get('title'))
    if not out.get('summary'):
        out['summary']=clean(job.get('description') or job.get('content'))[:500]
    if not out.get('intro'):
        out['intro']=out.get('summary','')
    for k in ('vacancy','qualification','salary','age_limit','application_fee','selection_process','exam_date','application_start_date','last_date','notification_date'):
        if not real(out.get(k)): out[k]=''
    out['url']=clean(job.get('url')); out['apply_link']=clean(job.get('apply_link')); out['notification_pdf']=clean(job.get('notification_pdf')); out['official_website']=clean(job.get('official_website')) or out['url']; out['ai_generated']=True; out['ai_model']=MODEL
    return out

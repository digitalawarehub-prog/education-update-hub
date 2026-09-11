from __future__ import annotations
import json,logging,os,re,requests,io
from bs4 import BeautifulSoup
try:
 from pypdf import PdfReader
except Exception: PdfReader=None
log=logging.getLogger('EUH_AI')
API='https://openrouter.ai/api/v1/chat/completions';MODEL=os.getenv('OPENROUTER_MODEL','openrouter/free');KEY=os.getenv('OPENROUTER_API_KEY','').strip()
BAD={'','not mentioned','not available','check notification','check official notification','as per rules','उपलब्ध नहीं','आधिकारिक अधिसूचना देखें','n/a','na','none','null','.'}
MONTH={'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,'may':5,'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'sept':9,'september':9,'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12}
def clean(v):
 s=str(v or '').strip()
 for a,b in [('â€“','–'),('â€”','—'),('â€˜','‘'),('â€™','’'),('â€œ','“'),('â€�','”'),('â€¦','…'),('�','')]:s=s.replace(a,b)
 return re.sub(r'\s+',' ',s).strip()
def real(v):return clean(v).casefold() not in BAD
def source_text(job):
 text=clean(job.get('content') or job.get('description'));url=clean(job.get('url'))
 if len(text)<120 and url and not url.lower().split('?')[0].endswith('.pdf'):
  try:
   r=requests.get(url,timeout=20,headers={'User-Agent':'Mozilla/5.0 Education Update Hub'});r.raise_for_status();s=BeautifulSoup(r.text,'html.parser')
   for x in s(['script','style','noscript','svg','nav','footer','header']):x.decompose()
   text=clean(s.get_text(' ',strip=True))
  except:pass
 if len(text)<120:text=clean(text+' '+pdf_text(job.get('notification_pdf') or url))
 return text[:18000]
def pdf_text(url):
 if not url or PdfReader is None or not str(url).lower().split('?')[0].endswith('.pdf'):return ''
 try:
  r=requests.get(url,timeout=20,headers={'User-Agent':'Mozilla/5.0 Education Update Hub'});r.raise_for_status();reader=PdfReader(io.BytesIO(r.content));return clean(' '.join((p.extract_text() or '') for p in reader.pages[:10]))[:18000]
 except:return ''
def classify(title):
 t=clean(title).casefold()
 if any(x in t for x in ('admit card','admit-card','hall ticket','call letter','e-admit','प्रवेश पत्र')):return 'admit-card','Admit Card'
 if any(x in t for x in ('answer key','answer-key','answerkey','उत्तर कुंजी','उत्तरकुंजी')):return 'answer-key','Answer Key'
 if re.search(r'\b(result|results|merit list|score card|scorecard)\b',t) or 'परिणाम' in t:return 'result','Result'
 if 'syllabus' in t or 'पाठ्यक्रम' in t:return 'syllabus','Syllabus'
 if 'scholarship' in t or 'छात्रवृत्ति' in t:return 'scholarship','Scholarship'
 if any(x in t for x in ('entrance exam','entrance test','admission test','प्रवेश परीक्षा')):return 'entrance','Entrance Exam'
 if any(x in t for x in ('walk-in interview','walk in interview','interview','साक्षात्कार')):return 'interview','Interview'
 if any(x in t for x in ('recruitment','vacancy','vacancies','applications are invited','application invited','apply online','engagement of','appointment of','भर्ती','रिक्ति','आवेदन आमंत्रित')):return 'recruitment','Recruitment'
 return 'notice','Notice'
def parse_json(v):
 if isinstance(v,dict):return v
 s=clean(v);s=re.sub(r'^```(?:json)?\s*|\s*```$','',s,flags=re.I|re.S).strip()
 try:return json.loads(s)
 except:pass
 m=re.search(r'\{.*\}',s,re.S)
 if m:
  try:return json.loads(m.group(0))
  except:pass
 return {}
def normalize_date(v):
 s=clean(v)
 def f(m):
  a,b,c=m.groups()
  if len(a)==4:return f'{int(c):02d}-{int(b):02d}-{int(a):04d}'
  if b.isdigit():return f'{int(a):02d}-{int(b):02d}-{int(c):04d}'
  n=MONTH.get(b.lower().strip('.'));return f'{int(a):02d}-{n:02d}-{int(c):04d}' if n else m.group(0)
 s=re.sub(r'\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b',f,s);s=re.sub(r'\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})\b',f,s);s=re.sub(r'\b(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember|t)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(20\d{2})\b',f,s,flags=re.I);return s
def call(prompt):
 if not KEY:raise RuntimeError('OPENROUTER_API_KEY_MISSING')
 headers={'Authorization':f'Bearer {KEY}','Content-Type':'application/json','HTTP-Referer':'https://educationupdatehub.in','X-Title':'Education Update Hub'}
 models=[]
 for m in (MODEL,os.getenv('OPENROUTER_FALLBACK_MODEL','')):
  if m and m not in models:models.append(m)
 last=''
 for model in models:
  base={'model':model,'messages':[{'role':'system','content':'Return only one valid JSON object. No markdown.'},{'role':'user','content':prompt}],'temperature':0.2,'max_tokens':3000}
  for structured in (True,False):
   payload=dict(base)
   if structured:payload['response_format']={'type':'json_object'}
   try:
    r=requests.post(API,headers=headers,json=payload,timeout=50)
    if r.status_code==429:last='429';break
    if r.status_code==400 and structured:continue
    r.raise_for_status();data=r.json();msg=((data.get('choices') or [{}])[0].get('message') or {});c=msg.get('content')
    if isinstance(c,list):c=''.join(str(x.get('text','')) for x in c if isinstance(x,dict))
    out=parse_json(c)
    if out:return out
   except Exception as e:last=str(e)
 raise RuntimeError('OPENROUTER_UNAVAILABLE:'+last)
def extract_fields_from_text(text):
    text=clean(text); out={}
    pats={
      'vacancy':[r'(?:total\s+)?vacanc(?:y|ies)\s*[:\-]?\s*([0-9,]+)', r'no\.\s+of\s+posts?\s*[:\-]?\s*([0-9,]+)', r'number\s+of\s+posts?\s*[:\-]?\s*([0-9,]+)'],
      'salary':[r'(?:pay\s*(?:scale|level)?|salary|remuneration|stipend|emoluments?)\s*[:\-]?\s*([^.;|]{3,140})'],
      'qualification':[r'(?:educational\s+qualification|qualification|eligibility)\s*[:\-]?\s*([^.;|]{8,300})'],
      'age_limit':[r'(?:age\s*limit|upper\s+age\s*limit|maximum\s+age)\s*[:\-]?\s*([^.;|]{3,120})'],
      'application_fee':[r'(?:application\s+fee|exam\s+fee|registration\s+fee)\s*[:\-]?\s*(₹?\s*[0-9,]+[^.;|]{0,80})'],
      'selection_process':[r'(?:selection\s+process|mode\s+of\s+selection)\s*[:\-]?\s*([^.;|]{5,180})'],
      'last_date':[r'(?:last\s+date(?:\s+to\s+apply)?|application\s+(?:last\s+)?date|deadline)\s*[:\-]?\s*([^.;|]{3,60})'],
      'application_start_date':[r'(?:application\s+(?:starts?|start\s+date)|online\s+application\s+starts?)\s*[:\-]?\s*([^.;|]{3,60})'],
      'exam_date':[r'(?:exam(?:ination)?\s+date|test\s+date)\s*[:\-]?\s*([^.;|]{3,60})'],
    }
    for k,pp in pats.items():
      for pat in pp:
       m=re.search(pat,text,re.I)
       if m:
        v=clean(m.group(1) if m.lastindex else m.group(0))
        if real(v):out[k]=v;break
    return out

def local_fallback(job,source):
 title=clean(job.get('title'));typ,cat=classify(title);out=dict(job); extracted=extract_fields_from_text(source)
 def field(*keys):
  for k in keys:
   if real(job.get(k)):return clean(job.get(k))
  for k in keys:
   if real(extracted.get(k)):return clean(extracted[k])
  return ''
 out.update({'title':title,'summary':f'{title} से संबंधित आधिकारिक अपडेट को सरल भाषा में संकलित किया गया है। उम्मीदवार नीचे दी गई जानकारी को आधिकारिक स्रोत से मिलान करके आगे की प्रक्रिया पूरी करें।','intro':f'{title} के संबंध में उपलब्ध महत्वपूर्ण जानकारी नीचे दी गई है। पात्रता, तिथियों और आवेदन प्रक्रिया की अंतिम पुष्टि आधिकारिक notification से करें।','category':cat,'post_type':typ,'department':field('department','organization','source'),'vacancy':field('vacancy','posts','total_posts'),'qualification':field('qualification','eligibility'),'salary':field('salary','pay_scale','stipend'),'age_limit':field('age_limit'),'application_fee':field('application_fee','fee'),'selection_process':field('selection_process'),'exam_date':field('exam_date'),'application_start_date':field('application_start_date','start_date'),'last_date':field('last_date','deadline'),'notification_date':field('notification_date','publish_date','source_date'),'how_to':'आधिकारिक वेबसाइट या notification में दिए गए निर्देशों के अनुसार आवेदन/अगली प्रक्रिया पूरी करें।','key_points':[],'important_notes':['आवेदन या परीक्षा से पहले आधिकारिक notification पढ़ें।','तारीख और पात्रता में बदलाव के लिए आधिकारिक वेबसाइट को प्राथमिकता दें।'],'faq':[{'question':f'{title} की आधिकारिक जानकारी कहां मिलेगी?','answer':'इस पोस्ट में उपलब्ध आधिकारिक स्रोत लिंक देखें।'},{'question':'आवेदन से पहले क्या जांचना चाहिए?','answer':'पात्रता, शुल्क, महत्वपूर्ण तिथियां और दस्तावेज आधिकारिक notification से जांचें।'}]})
 if source:
  ss=[clean(x) for x in re.split(r'(?<=[.!?।])\s+',source) if len(clean(x))>40];out['key_points']=[x[:220] for x in ss[:5]]
 return out
def enrich(job):
 source=source_text(job);forced,forced_cat=classify(job.get('title'))
 prompt='''You are the human editor of Education Update Hub. Use ONLY the source text. Never invent facts. Write natural human-readable Indian-English/Hindi website content, concise and useful. Keep missing factual fields empty. Return only JSON. Create a 2-4 sentence summary, intro, 4-7 key points, how_to, important_notes and 3 FAQs. Dates must be DD-MM-YYYY.\nTITLE: %s\nURL: %s\nTYPE: %s\nSOURCE:\n%s\nJSON keys: title,summary,category,post_type,department,vacancy,qualification,salary,age_limit,application_fee,selection_process,exam_date,application_start_date,last_date,notification_date,intro,key_points,how_to,important_notes,faq.'''%(clean(job.get('title')),clean(job.get('url')),forced,source[:18000])
 try:ai=call(prompt)
 except Exception as e:log.warning('OpenRouter unavailable; local human-style fallback: %s',e);ai=local_fallback(job,source)
 out=dict(job);typ,cat=classify(ai.get('title') or job.get('title'))
 if forced in {'notice','interview','admit-card','result','answer-key','syllabus','scholarship','entrance'}:typ,cat=forced,forced_cat
 out['post_type']=typ;out['category']=cat
 for k in ('title','summary','department','vacancy','qualification','salary','age_limit','application_fee','selection_process','exam_date','application_start_date','last_date','notification_date','intro','how_to'):
  v=clean(ai.get(k));
  if v:out[k]=normalize_date(v) if k in {'exam_date','application_start_date','last_date','notification_date'} else v
 for k in ('key_points','important_notes','faq'):
  if isinstance(ai.get(k),list):out[k]=ai[k]
 for k in ('vacancy','qualification','salary','age_limit','application_fee','selection_process','exam_date','application_start_date','last_date','notification_date'):
  if not real(out.get(k)) and real(job.get(k)):out[k]=clean(job.get(k))
 out['title']=clean(out.get('title') or job.get('title'));out['summary']=clean(out.get('summary')) or f"{out['title']} से संबंधित महत्वपूर्ण आधिकारिक अपडेट नीचे दिया गया है।";out['url']=clean(job.get('url'));out['apply_link']=clean(job.get('apply_link'));out['notification_pdf']=clean(job.get('notification_pdf') or job.get('official_notification_pdf'));out['official_website']=clean(job.get('official_website')) or out['url'];out['ai_generated']=True;out['ai_model']=MODEL if KEY else 'local-human-fallback';return out

# EHU QUALITY GUARD: do not publish broken PDF/OCR glyph output as prose.
def _ehu_corrupt_text(v):
    s=str(v or '')
    if not s.strip(): return False
    if len(re.findall(r'\^',s)) >= 2 or re.search(r'(?:\^|`|~){2,}',s): return True
    if re.search(r'\b(?:ment Done|Jiw|Tfs|Tfr)\b',s,re.I): return True
    weird=len(re.findall(r"[^A-Za-z0-9\u0900-\u097F\s.,:;!?()/%₹+\-&–—/'\"\[\]]",s))
    if weird > max(5,len(s)//70): return True
    isolated=len(re.findall(r'\b[A-Za-z]\b',s))
    longwords=len(re.findall(r'\b[A-Za-z]{3,}\b',s))
    if isolated >= 5 and isolated > longwords*0.7: return True
    return False

def _ehu_safe(v):
    s=clean(v)
    return '' if _ehu_corrupt_text(s) else s

def _ehu_fallback_points(title,out):
    pts=[]
    if real(out.get('vacancy')): pts.append(f"इस भर्ती में उपलब्ध रिक्तियों की जानकारी: {clean(out['vacancy'])}।")
    if real(out.get('qualification')): pts.append(f"शैक्षणिक योग्यता: {clean(out['qualification'])}।")
    if real(out.get('salary')): pts.append(f"वेतन/मानदेय: {clean(out['salary'])}।")
    if real(out.get('age_limit')): pts.append(f"आयु सीमा: {clean(out['age_limit'])}।")
    if real(out.get('application_fee')): pts.append(f"आवेदन शुल्क: {clean(out['application_fee'])}।")
    if real(out.get('last_date')): pts.append(f"आवेदन की अंतिम तिथि: {normalize_date(out['last_date'])}।")
    return pts[:6] or ["यह अपडेट उपलब्ध आधिकारिक स्रोत के आधार पर सरल भाषा में तैयार किया गया है।","अंतिम पात्रता और तिथियों की पुष्टि आधिकारिक अधिसूचना से करें।"]

_ehu_original_enrich=enrich
def enrich(job):
    out=_ehu_original_enrich(job)
    title=_ehu_safe(out.get('title') or job.get('title')) or clean(job.get('title'))
    out['title']=title
    if _ehu_corrupt_text(out.get('summary')) or len(clean(out.get('summary'))) < 30:
        out['summary']=f"{title} के संबंध में उपलब्ध आधिकारिक जानकारी को सरल भाषा में संकलित किया गया है। पात्रता, महत्वपूर्ण तिथियां और आवेदन प्रक्रिया से जुड़े जरूरी विवरण नीचे दिए गए हैं।"
    if _ehu_corrupt_text(out.get('intro')) or len(clean(out.get('intro'))) < 30:
        out['intro']=f"{title} के लिए उम्मीदवार आवेदन करने से पहले आधिकारिक अधिसूचना ध्यान से पढ़ें। पद, योग्यता और महत्वपूर्ण तिथियों की अंतिम पुष्टि आधिकारिक स्रोत से करें।"
    for k in ('department','vacancy','qualification','salary','age_limit','application_fee','selection_process','exam_date','application_start_date','last_date','notification_date'):
        if _ehu_corrupt_text(out.get(k)): out[k]=''
    pts=out.get('key_points')
    if not isinstance(pts,list) or not pts or any(_ehu_corrupt_text(x) for x in pts): out['key_points']=_ehu_fallback_points(title,out)
    else: out['key_points']=[_ehu_safe(x) for x in pts if _ehu_safe(x)] or _ehu_fallback_points(title,out)
    notes=out.get('important_notes')
    if not isinstance(notes,list) or any(_ehu_corrupt_text(x) for x in notes):
        out['important_notes']=["आवेदन करने से पहले आधिकारिक अधिसूचना पढ़ें।","महत्वपूर्ण तिथियों और पात्रता में बदलाव के लिए आधिकारिक वेबसाइट को प्राथमिकता दें।"]
    else: out['important_notes']=[_ehu_safe(x) for x in notes if _ehu_safe(x)]
    faq=out.get('faq')
    if not isinstance(faq,list) or any(not isinstance(x,dict) or _ehu_corrupt_text(x.get('question')) or _ehu_corrupt_text(x.get('answer')) for x in faq):
        out['faq']=[{'question':f'{title} की आधिकारिक जानकारी कहां मिलेगी?','answer':'इस पोस्ट में दिए गए आधिकारिक वेबसाइट या notification link पर जानकारी की पुष्टि करें।'},{'question':'आवेदन से पहले क्या जांचना चाहिए?','answer':'पात्रता, शुल्क, महत्वपूर्ण तिथियां और आवश्यक दस्तावेज आधिकारिक अधिसूचना से जांचें।'}]
    else: out['faq']=[{'question':_ehu_safe(x.get('question')),'answer':_ehu_safe(x.get('answer'))} for x in faq if isinstance(x,dict) and _ehu_safe(x.get('question')) and _ehu_safe(x.get('answer'))]
    if _ehu_corrupt_text(out.get('how_to')) or not clean(out.get('how_to')): out['how_to']='आधिकारिक वेबसाइट/notification में दिए गए निर्देशों के अनुसार आवेदन या अगली प्रक्रिया पूरी करें।'
    return out

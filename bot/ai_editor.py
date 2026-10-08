from __future__ import annotations
import json, logging, os, re, time, requests, io
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
    s=re.sub(r'\s+',' ',s).strip()
    # Reader-friendly terminology: replace difficult/old-fashioned 'करार' wording.
    s=re.sub(r'करार\s*आधारित', 'agreement के आधार पर', s, flags=re.I)
    s=s.replace('करार', 'agreement')
    return s

def real(v): return clean(v).casefold() not in BAD

def _pdf_text(url):
    if not url: return ''
    try:
        r=requests.get(url,timeout=35,headers={'User-Agent':'Mozilla/5.0 Education Update Hub'},allow_redirects=True)
        r.raise_for_status()
        data=r.content
        text=''
        try:
            import fitz
            doc=fitz.open(stream=data,filetype='pdf')
            text='\n'.join(page.get_text('text') for page in doc[:20])
            doc.close()
        except Exception:
            try:
                from pypdf import PdfReader
                reader=PdfReader(io.BytesIO(data))
                text='\n'.join((p.extract_text() or '') for p in reader.pages[:20])
            except Exception:
                text=''
        return clean(text)[:22000]
    except Exception as e:
        log.debug('PDF source unavailable: %s',e)
        return ''

def source_text(job):
    text=clean(job.get('content') or job.get('description'))
    url=clean(job.get('url'))
    pdf=clean(job.get('notification_pdf'))
    # Prefer the official notification PDF when the scraped page is only a
    # button/title/navigation shell. This prevents AI_SOURCE_TOO_SHORT for
    # genuine recruitment notices.
    if len(text)<120 and pdf:
        pdf_text=_pdf_text(pdf)
        if len(pdf_text)>=120: return pdf_text
    if len(text)<120 and url:
        if url.lower().endswith('.pdf'):
            pdf_text=_pdf_text(url)
            if len(pdf_text)>=120: return pdf_text
        else:
            try:
                r=requests.get(url,timeout=25,headers={'User-Agent':'Mozilla/5.0 Education Update Hub'})
                r.raise_for_status(); s=BeautifulSoup(r.text,'html.parser')
                for x in s(['script','style','noscript','svg','nav','footer','header']): x.decompose()
                page_text=clean(s.get_text(' ',strip=True))
                if len(page_text)>len(text): text=page_text
                # If the page is only a short notice shell, follow its first
                # official PDF link automatically.
                if len(text)<300:
                    for a_tag in s.find_all('a', href=True):
                        href=str(a_tag.get('href') or '').strip()
                        if '.pdf' in href.lower():
                            from urllib.parse import urljoin
                            pdf_url=urljoin(url, href)
                            pdf_text=_pdf_text(pdf_url)
                            if len(pdf_text)>=120:
                                text=pdf_text
                                break
            except Exception: pass
    # Use already-extracted structured facts as a last factual context source.
    if len(text)<120:
        parts=[]
        for label,key in (('Vacancy','vacancy'),('Qualification','qualification'),('Salary','salary'),('Age','age_limit'),('Fee','application_fee'),('Selection','selection_process'),('Last date','last_date')):
            v=clean(job.get(key))
            if v: parts.append(f'{label}: {v}')
        if parts: text=clean(' | '.join(parts))
    return text[:22000]

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
    if isinstance(v, dict):
        return v
    s=clean(v)
    if not s:
        return {}
    s=re.sub(r'^\s*```(?:json)?\s*', '', s, flags=re.I)
    s=re.sub(r'\s*```\s*$', '', s).strip()
    # First try the complete response.
    try:
        return json.loads(s)
    except Exception:
        pass
    # Then locate the first balanced JSON object. This handles providers
    # that add a short sentence before/after the JSON.
    begin=s.find('{')
    if begin>=0:
        depth=0; in_str=False; esc=False
        for i in range(begin,len(s)):
            ch=s[i]
            if in_str:
                if esc:
                    esc=False
                elif ch=='\\':
                    esc=True
                elif ch=='"':
                    in_str=False
                continue
            if ch=='"':
                in_str=True
            elif ch=='{':
                depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:
                    candidate=s[begin:i+1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        # Common harmless provider formatting errors.
                        candidate=re.sub(r',\s*([}\]])', r'\1', candidate)
                        try:
                            return json.loads(candidate)
                        except Exception:
                            pass
                    break
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

def call(prompt, retry=False):
    headers={
        'Authorization':f'Bearer {KEY}',
        'Content-Type':'application/json',
        'HTTP-Referer':'https://educationupdatehub.in',
        'X-Title':'Education Update Hub'
    }
    # Keep responses compact. A shorter answer reduces truncation and free-tier
    # token usage while still carrying the complete article fields.
    base={
        'model':MODEL,
        'messages':[
            {'role':'system','content':'Return ONLY one valid compact JSON object. No markdown, no explanation, no extra text.'},
            {'role':'user','content':prompt + ('\nIMPORTANT: Keep every field concise so the JSON is complete and valid.' if retry else '')}
        ],
        'temperature':0.1,
        'max_tokens':2800
    }
    payload=dict(base)
    payload['response_format']={'type':'json_object'}
    r=requests.post(API,headers=headers,json=payload,timeout=45)
    if r.status_code==429:
        raise RuntimeError('OPENROUTER_RATE_LIMIT')
    if r.status_code==400:
        try:
            err=r.json()
            msg=str(err.get('error',{}).get('message','')).lower()
        except Exception:
            msg=''
        if 'response_format' in msg or 'json' in msg or 'unsupported' in msg:
            r=requests.post(API,headers=headers,json=base,timeout=45)
            if r.status_code==429:
                raise RuntimeError('OPENROUTER_RATE_LIMIT')
    r.raise_for_status()
    data=r.json()
    msg=((data.get('choices') or [{}])[0].get('message') or {})
    content=msg.get('content')
    if isinstance(content,list):
        content=''.join(str(x.get('text','')) for x in content if isinstance(x,dict))
    return parse_json(content)


def hindi_score(text):
    s=clean(text)
    if not s: return 0.0
    letters=re.findall(r'[A-Za-z\u0900-\u097F]',s)
    hi=len(re.findall(r'[\u0900-\u097F]',s))
    return hi/max(1,len(letters))

def quality_ok(ai, forced_type='recruitment'):
    title=clean(ai.get('title')); summary=clean(ai.get('summary')); intro=clean(ai.get('intro'))
    body=' '.join(clean(ai.get(k)) for k in ('summary','intro','how_to','important_notes'))
    combined=(title+' '+summary+' '+body).casefold()
    blocked=(
        'admit card','admit-card','hall ticket','call letter','answer key','answer-key',
        'result','results','merit list','selected candidates','selected candidate',
        'qualified candidates','shortlisted candidates','waiting list','previous year',
        'question paper','exam schedule','examination schedule','corrigendum',
        'date extension','extension of last date','extension of date','re-schedule',
        'reschedule','individual score','vice chancellor','vice-chancellor',
        'second term','re-appointed','reappointed','कुलपति','पुनः नियुक्त',
        'कार्यकाल','प्रवेश पत्र','कॉल लेटर','चयनित उम्मीदवार','प्रतीक्षा सूची',
        'उत्तर कुंजी','परिणाम','संशोधित तिथि'
    )
    if len(title)<20 or len(summary)<120 or len(intro)<100: return False
    if hindi_score(body)<0.38: return False
    if len(ai.get('key_points') or [])<4: return False
    if not isinstance(ai.get('faq'),list) or len(ai.get('faq'))<3: return False
    if re.search(r'\b(?:Government|Candidates|Important Dates|Apply Online|Job Details)\b', summary, re.I): return False
    if any(x in combined for x in blocked): return False
    # A recruitment candidate must remain a recruitment article after editing.
    if forced_type=='recruitment':
        p=clean(ai.get('post_type') or ai.get('category')).casefold()
        if p and not any(x in p for x in ('recruitment','भर्ती','vacancy','रिक्ति')):
            return False
    return True


def enrich(job):
    if not KEY: raise RuntimeError('OPENROUTER_API_KEY_MISSING')
    source=source_text(job)
    if len(source)<120: raise RuntimeError('AI_SOURCE_TOO_SHORT')
    forced,forced_cat=classify(job.get('title'))
    prompt=f'''आप Education Update Hub के वरिष्ठ हिंदी संपादक हैं। नीचे दिया गया स्रोत ही एकमात्र तथ्य-स्रोत है। स्रोत में जो नहीं है, उसका अनुमान बिल्कुल न लगाएँ।

लेखन नियम:
1) पूरा लेख स्वाभाविक, सरल और मानवीय हिंदी में लिखें। ऐसा लगे जैसे किसी अनुभवी हिंदी संपादक ने सरकारी सूचना पढ़कर पाठकों के लिए समझाकर लिखा है; शब्दशः अनुवाद, मशीन-जैसी भाषा, दोहराव और खोखले वाक्य न लिखें।
2) title को आकर्षक लेकिन तथ्यात्मक रखें। संस्था/पद/परीक्षा के आधिकारिक नाम English में रहने दे सकते हैं, लेकिन बाकी title हिंदी में रखें।
3) summary, intro, how_to और important_notes मुख्यतः हिंदी में हों। key_points और FAQ भी हिंदी में हों।
4) हर तथ्य केवल SOURCE से लें। vacancy, qualification, salary, age, fee, selection और dates में कुछ न मिले तो खाली रखें। कभी अनुमान न लगाएँ।
5) '₹500', 'Rs 29', page number, fee, application charge या navigation text को salary न मानें। Salary केवल स्पष्ट pay scale/pay level/remuneration/stipend/emoluments के प्रमाण पर दें।
6) परीक्षा कार्यक्रम, result, answer key, admit card, selected/qualified list, previous-year paper, corrigendum या केवल date-extension notice को नई recruitment न बनाएँ।
7) Recruitment तभी चुनें जब स्रोत वास्तव में vacancy/application/engagement के लिए आवेदन आमंत्रित करता हो। केवल किसी व्यक्ति की नियुक्ति, पुनर्नियुक्ति, पदस्थापना, कुलपति/अधिकारी की नियुक्ति या कार्यकाल बढ़ाने की खबर recruitment नहीं है।
8) Dates DD-MM-YYYY में रखें। URLs को न बदलें।
9) summary कम से कम 120 अक्षरों की, intro कम से कम 100 अक्षरों का, कम से कम 4 key_points, कम से कम 3 FAQ दें। Filler न लिखें।

Existing title: {clean(job.get('title'))}
URL: {clean(job.get('url'))}
Forced type: {forced}
SOURCE:
{source}

Return ONLY one valid JSON object with keys: title,summary,category,post_type,department,vacancy,qualification,salary,age_limit,application_fee,selection_process,exam_date,application_start_date,last_date,notification_date,intro,key_points,how_to,important_notes,faq. FAQ is an array of objects with question and answer.'''
    ai={}
    last_reason='AI_INVALID_JSON'
    # At most two AI requests per candidate. The previous three-attempt loop
    # consumed free-tier quota too quickly.
    for attempt in range(2):
        ai=call(prompt, retry=(attempt==1))
        if ai and quality_ok(ai, forced_type=forced): break
        if ai: last_reason='AI_QUALITY_REJECTED'
        if attempt==0: time.sleep(.5)
    if not ai: raise RuntimeError(last_reason)
    if not quality_ok(ai, forced_type=forced): raise RuntimeError('AI_QUALITY_REJECTED')
    out=dict(job); typ,cat=classify(ai.get('title') or job.get('title'))
    if forced in {'notice','interview','admit-card','result','answer-key','syllabus','scholarship','entrance'}:
        typ,cat=forced,forced_cat
    elif forced=='recruitment':
        # Never allow an AI rewrite of a recruitment source to become a notice,
        # admit card, result or other non-recruitment article.
        if typ!='recruitment':
            raise RuntimeError('AI_NON_RECRUITMENT_OUTPUT')
        typ,cat='recruitment','Recruitment'
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

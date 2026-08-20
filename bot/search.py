"""Backend search helpers used by the auto-publisher."""
import json
import re
from pathlib import Path
from difflib import SequenceMatcher

ROOT_DIR = Path(__file__).resolve().parent.parent
SEARCH_INDEX = ROOT_DIR / "search-index.json"
MAX_RESULTS = 50
MIN_QUERY = 2


def normalize(value):
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def load_index():
    if not SEARCH_INDEX.exists():
        return []
    try:
        data=json.loads(SEARCH_INDEX.read_text(encoding="utf-8"))
        return data if isinstance(data,list) else []
    except Exception:
        return []


def tokenize(query):
    return [x for x in normalize(query).split() if x]


def calculate_score(job, query):
    q=normalize(query)
    fields={k:normalize(job.get(k)) for k in ("title","category","department","state","description","keywords")}
    if isinstance(job.get("keywords"),list):
        fields["keywords"]=normalize(" ".join(map(str,job.get("keywords",[]))))
    score=0
    if fields["title"]==q: score+=150
    elif fields["title"].startswith(q): score+=100
    elif q in fields["title"]: score+=70
    for k,pts in (("category",30),("department",20),("state",20),("description",10),("keywords",15)):
        if q in fields[k]: score+=pts
    for token in tokenize(q):
        if token in fields["title"]: score+=12
        if token in fields["description"]: score+=4
    score+=int(SequenceMatcher(None,q,fields["title"]).ratio()*25)
    return score


def search(query):
    q=normalize(query)
    if len(q)<MIN_QUERY: return []
    results=[]
    for job in load_index():
        score=calculate_score(job,q)
        if score>0:
            item=dict(job); item["score"]=score; results.append(item)
    results.sort(key=lambda x:x.get("score",0), reverse=True)
    return results[:MAX_RESULTS]


def search_category(category):
    q=normalize(category)
    return [j for j in load_index() if q in normalize(j.get("category"))]


def search_department(department):
    q=normalize(department)
    return [j for j in load_index() if q in normalize(j.get("department"))]


def search_state(state):
    q=normalize(state)
    return [j for j in load_index() if q in normalize(j.get("state"))]

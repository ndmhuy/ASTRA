import json,collections
from pathlib import Path
from lib import ask,parse
L=Path(__file__).resolve().parent
p=json.loads((L/'outputs/profile.compact.json').read_text(encoding='utf-8'))
def anonymous(x):
 if isinstance(x,dict): return {k:anonymous(v) for k,v in x.items() if k not in ('evidence','refs') and not k.endswith('_refs')}
 if isinstance(x,list): return [anonymous(v) for v in x]
 return x
p=anonymous(p)
r=json.loads((L/'extract/HELDOUT_2026.json').read_text(encoding='utf-8'))['rows']
for attempt in range(2):
 try:
  text,u,c=ask((L/'prompts/COVERAGE.txt').read_text(encoding='utf-8'),json.dumps({'profile':p,'anonymous_rows':r},ensure_ascii=False))
  d=parse(text); known={(x['part'],x['idx'],x.get('sub')) for x in r}; got={(x['part'],x['idx'],x.get('sub')) for x in d['rows']}
  assert known==got and len(d['rows'])==len(r),'coverage address mismatch'
  break
 except Exception:
  if attempt==1: raise
parts={}
for part in sorted({x['part'] for x in r}):
 rows=[x for x in d['rows'] if x['part']==part]; parts[part]=dict(collections.Counter(x['match'] for x in rows))
high={(x['part'],x['idx'],x.get('sub')) for x in r if x['discrimination']=='high'}
d['summary']={'by_part':parts,'high_total':len(high),'high_same_construction':sum(x['match']=='same_construction' for x in d['rows'] if (x['part'],x['idx'],x.get('sub')) in high),'high_at_least_topic':sum(x['match']!='none' for x in d['rows'] if (x['part'],x['idx'],x.get('sub')) in high),'backend':u}
(L/'outputs/heldout-coverage.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(d['summary'],ensure_ascii=False))

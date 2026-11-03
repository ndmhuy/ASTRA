"""Experiment-only evidence checks; never a product question gate."""
import json,re,collections
from pathlib import Path
L=Path(__file__).resolve().parent
def tokens(s): return re.findall(r"[\w]+",s.casefold())
def strings(x,path=''):
 if isinstance(x,str): yield path,x
 elif isinstance(x,dict):
  for k,v in x.items():
   if k not in ('refs','evidence') and not k.endswith('_refs'): yield from strings(v,path+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x): yield from strings(v,path+'/'+str(i))
def scan():
 d=json.loads((L/'outputs/profile.compact.json').read_text(encoding='utf-8'))
 files=sorted((L/'extract').glob('p*.json'))
 counts={f.name:len(json.loads(f.read_text(encoding='utf-8'))['rows']) for f in files}
 corpus={f.stem:tokens(f.read_text(encoding='utf-8')) for f in (L/'papers').glob('p*.md')}
 hits=[]; numeric=[]
 for path,s in strings(d):
  if re.search(r'\d',s): numeric.append({'field':path,'text':s})
  t=tokens(s)
  for paper,other in corpus.items():
   grams={tuple(other[i:i+10]) for i in range(len(other)-9)}
   overlap=sorted({' '.join(t[i:i+10]) for i in range(len(t)-9) if tuple(t[i:i+10]) in grams})
   if overlap: hits.append({'field':path,'paper':paper,'overlap_10grams':overlap})
 out={'extraction_counts':counts,'heldout_excluded':all(f.name!='HELDOUT_2026.json' for f in files),'evidence':d['evidence'],'literal_number_candidates':numeric,'overlap_candidates':hits,'caveat':'Lexical scan is not a semantic fidelity verdict. Common mathematical wording can overlap.'}
 (L/'outputs/profile-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in out.items() if k not in ('literal_number_candidates','overlap_candidates')},ensure_ascii=False)); print('number candidates',len(numeric),'10gram candidates',len(hits))
if __name__=='__main__': scan()

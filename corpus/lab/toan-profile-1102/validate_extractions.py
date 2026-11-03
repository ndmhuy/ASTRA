import json,re,collections
from pathlib import Path
from prepare_blind import source_questions
L=Path(__file__).resolve().parent
def canon(s): return re.sub(r'^PHẦN\s+','',s.strip(),flags=re.I).upper()
results=[]
for f in sorted((L/'extract').glob('*.json')):
 paper=L/'papers'/f.with_suffix('.md').name
 if not paper.exists(): continue
 rows=json.loads(f.read_text(encoding='utf-8'))['rows']; expected=set()
 for q in source_questions(paper):
  subs=re.findall(r'(?m)^\s*([a-z])\s*[).]',q['text'])
  for sub in (subs or [None]): expected.add((canon(q['part']),q['idx'],sub))
 got=[(canon(r['part']),r['idx'],r.get('sub')) for r in rows]
 result={'paper':f.stem,'rows':len(rows),'unique':len(set(got)),'expected':len(expected),'missing':sorted(expected-set(got),key=str),'extra':sorted(set(got)-expected,key=str),'by_part':dict(collections.Counter(p for p,i,s in got))}
 results.append(result); print(json.dumps(result,ensure_ascii=False))
(L/'outputs/extraction-validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
if any(r['missing'] or r['extra'] or r['rows']!=r['unique'] for r in results): raise SystemExit(1)

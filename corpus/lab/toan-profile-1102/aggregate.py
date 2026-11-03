import glob,json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import ask,parse
L=os.path.dirname(os.path.abspath(__file__)); rows=[]
for f in sorted(glob.glob(L+'/extract/p*.json')):
    n=os.path.basename(f)[:-5]
    for r in json.load(open(f))['rows']:
        r['ref']=f"{n}|{r.get('part')}|{r.get('idx')}|{r.get('sub')}"; rows.append(r)
known={r['ref'] for r in rows}; print(len(rows),'rows')
for a in range(2):
    try:
        t,u,c=ask(open(L+'/prompts/AGGREGATE.txt').read(),'<<<ROWS>>>\n'+json.dumps(rows,ensure_ascii=False)+'\n<<<END ROWS>>>'); d=parse(t); break
    except Exception as e: print('retry',repr(e)[:300]); d=None
if d is None: sys.exit('STOP: aggregate failed twice')
json.dump(d,open(L+'/outputs/profile.raw.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
total_refs=sum(len(x.get('refs') or []) for group in ('patterns','discrimination_moves') for x in d[group])
bad=0
def count(x):
    global bad
    refs=[r for r in x.get('refs') or [] if r in known]; bad+=len(x.get('refs') or [])-len(refs)
    x['paper_count']=len({r.split('|')[0] for r in refs}); x['row_count']=len(refs); x.pop('refs',None)
for x in d['patterns']: count(x)
for x in d['discrimination_moves']: count(x)
d['patterns'].sort(key=lambda x:(x['part_kind'],-x['paper_count']))
d['evidence']={'papers':9,'kind':'provincial 2026, third-party copies; 2026 official held out','bad_refs_dropped':bad,'total_refs':total_refs,'source_files':[os.path.basename(f) for f in sorted(glob.glob(L+'/extract/p*.json'))]}
json.dump(d,open(L+'/outputs/profile.compact.json','w'),ensure_ascii=False,indent=1)
print('patterns',len(d['patterns']),'bad refs',bad,'chars',len(json.dumps(d,ensure_ascii=False)),u.get('output_tokens'),c)

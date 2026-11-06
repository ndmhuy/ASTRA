import glob,json,os,sys,time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(__file__))
from lib import ask,parse
L=os.path.dirname(os.path.abspath(__file__)); S=open(L+'/prompts/EXTRACT.txt').read()
def one(f):
    n=os.path.basename(f)[:-3]; out=f'{L}/extract/{n}.json'
    if os.path.exists(out): return n,'cached'
    for a in range(2):
        try:
            t,u,c=ask(S,'<<<PAPER>>>\n'+open(f).read()+'\n<<<END PAPER>>>')
            d=parse(t); assert len(d['rows'])==34, f"expected 34 slots, got {len(d['rows'])}"; json.dump({'rows':d['rows'],'usage':u,'cost':c},open(out,'w'),ensure_ascii=False,indent=1); return n,len(d['rows']),u.get('output_tokens')
        except Exception as e: err=repr(e)[:200]
    return n,'FAIL',err
for f in sorted(glob.glob(L+'/papers/*.md')):
    r=one(f); print(time.strftime('%H:%M:%S'),r,flush=True)
    if 'FAIL' in r: sys.exit(1)

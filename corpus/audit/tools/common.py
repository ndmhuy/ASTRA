import json,os,re,subprocess,time,hashlib,datetime,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MODEL='gpt-6.1-sol'
CLI='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);pending=p.parent/('.lab-write-'+str(os.getpid())+'-'+str(time.time_ns()));pending.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(pending,p)
def evidence_path(p):
 p=Path(p);original=Path('/Users/huynguyen/Lecturing_Lab/wt-agent-runner')
 if p.is_relative_to(original) and not p.exists():
  receipt=ROOT/'audit/outputs/product-snapshot-recovery.json'
  if not receipt.exists():raise FileNotFoundError(p)
  r=json.loads(receipt.read_text(encoding='utf-8'));rel=str(p.relative_to(original));candidate=Path(r['snapshot'])/rel
  if not candidate.is_file() or hashlib.sha256(candidate.read_bytes()).hexdigest()!=r['files'].get(rel):raise ValueError('PINNED_PRODUCT_SNAPSHOT_HASH '+rel)
  return candidate
 return p
def product_root():
 original=Path('/Users/huynguyen/Lecturing_Lab/wt-agent-runner/Grading_Tools')
 if original.is_dir():return original
 r=load(ROOT/'audit/outputs/product-snapshot-recovery.json')
 return Path(r['snapshot'])/'Grading_Tools'
def load(p):return json.loads(evidence_path(p).read_text(encoding='utf-8'))
def parse(s):
 s=s.strip();s=re.sub(r'^```(?:json)?\s*|\s*```$','',s);return json.loads(s[s.find('{'):s.rfind('}')+1])
def ask(tag,prompt,images=(),timeout=900,model=MODEL):
 global_stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
 if global_stop.exists() and load(global_stop).get('active',True):raise RuntimeError('MODEL_PREREQUISITE_STOPPED: see GLOBAL-MODEL-STOP.json')
 d=ROOT/'audit/outputs/calls'/tag;d.mkdir(parents=True,exist_ok=True)
 existing=list(d.glob('attempt-*.request.txt'));n=len(existing)+1
 base=d/f'attempt-{n}';base.with_suffix('.request.txt').write_text(prompt,encoding='utf-8')
 argv=[CLI,'exec','--skip-git-repo-check','--sandbox','read-only','--model',model,'--ephemeral','--output-last-message',str(base.with_suffix('.reply.txt'))]
 for im in images:argv+=['-i',str(im)]
 argv+=['-'];env={k:v for k,v in os.environ.items() if not any(a in k for a in ('API_KEY','API_KEYS'))};env['PYTHONDONTWRITEBYTECODE']='1';env['TMPDIR']=str(ROOT/'audit/work')
 t=time.time()
 try:
  r=subprocess.run(argv,input=prompt,text=True,capture_output=True,cwd=ROOT/'audit/work',env=env,timeout=timeout)
  base.with_suffix('.cli.log').write_text(r.stderr+r.stdout,encoding='utf-8');out=base.with_suffix('.reply.txt')
  dump(base.with_suffix('.meta.json'),{'model':model,'backend':'codex subscription','returncode':r.returncode,'seconds':round(time.time()-t,2),'images':[str(p) for p in images]})
  if r.returncode:
   message=r.stderr+r.stdout
   cause=next((name for name,pattern in [('quota',r'usage limit|rate limit|quota|limit reached'),('auth',r'not logged|authentication failed|unauthorized')] if re.search(pattern,message,re.I)),None)
   if cause:
    with (ROOT/'audit/work/model-prerequisite-events.lock').open('a',encoding='utf-8') as lock:
     fcntl.flock(lock,fcntl.LOCK_EX)
     fp=ROOT/'audit/outputs/model-prerequisite-failures.json';history=load(fp) if fp.exists() else [];history.append({'cause':cause,'tag':tag,'attempt':n,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});dump(fp,history)
     if sum(x['cause']==cause for x in history)>=2:dump(global_stop,{'cause':cause,'history':history,'reason':'Same subscription prerequisite failed twice; no dependent model steps can run.'})
   raise RuntimeError('CLI_EXIT_'+str(r.returncode)+': '+r.stderr[-500:])
  reply=out.read_text(encoding='utf-8')
  try:return parse(reply)
  except json.JSONDecodeError:
   clean=re.sub(r'^```(?:json)?\s*|\s*```$','',reply.strip());start=clean.find('{')
   if start<0:raise
   obj,end=json.JSONDecoder().raw_decode(clean[start:]);tail=clean[start+end:].strip()
   if isinstance(obj,dict) and tail=='}' and not clean[:start].strip():
    dump(base.with_suffix('.parse-recovery.json'),{'raw_sha256':hashlib.sha256(reply.encode('utf-8')).hexdigest(),'surplus_suffix':tail,'object_values_unchanged':True,'kind':'one surplus closing brace after complete JSON object'})
    return obj
   raise

 except subprocess.TimeoutExpired:raise RuntimeError('CLI_TIMEOUT')
def twice(tag,fn):
 previous_stop=ROOT/'audit/outputs/stops'/f'{tag}.json'
 if previous_stop.exists():
  previous=load(previous_stop)
  if previous.get('stopped') and not previous.get('resolved_by_latest_attempt') and not previous.get('retry_authorized_after_fix'):
   errors=previous.get('errors',[])
   prerequisite_only=errors and all(re.search(r'MODEL_PREREQUISITE_STOPPED|usage limit|rate limit|quota|limit reached|authentication|unauthorized|not logged',e,re.I) for e in errors)
   if not prerequisite_only:print('ALREADY_STOPPED',tag,'no third attempt for unchanged failure',flush=True);return None
 errors=[]
 for i in range(2):
  try:
   result=fn();stop=ROOT/'audit/outputs/stops'/f'{tag}.json'
   if stop.exists():
    previous=load(stop);previous['resolved_by_latest_attempt']=True;previous['resumed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(stop,previous)
   return result
  except Exception as e:
   errors.append(str(e));print('FAIL',tag,i+1,str(e)[:240],flush=True)
 dump(ROOT/'audit/outputs/stops'/f'{tag}.json',{'stage':tag,'errors':errors,'stopped':True});return None
def run(args,**kw):return subprocess.run([str(a) for a in args],check=True,capture_output=True,text=True,**kw).stdout

"""One paper through the unmodified product path; arm 'profile' adds the exam profile by monkeypatch only."""
import hashlib,json,os,sys,time
sys.path.insert(0,os.getcwd())
L='/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102'
tag,arm=sys.argv[1],sys.argv[2]; subj='Toán'
OUT=f'{L}/outputs/run-{tag}'; os.makedirs(OUT+'/calls',exist_ok=True)
def log(*a): print(time.strftime('%H:%M:%S'),*a,flush=True)
from exam_generator.agents.providers import cli as CLI
from dataclasses import replace
MODEL='gpt-6-luna'
from types import SimpleNamespace
from lib import RetainedDirectory
CLI.tempfile=SimpleNamespace(TemporaryDirectory=RetainedDirectory)
_cli=CLI.PROFILES['codex-cli']
CLI.PROFILES['codex-cli']=replace(_cli,args=('exec','--skip-git-repo-check','--sandbox','read-only','--model',MODEL,'--ephemeral','-'))
from exam_generator.agents.providers import register
register(CLI.CliProvider(CLI.PROFILES['codex-cli']))
_orig=CLI.CliProvider.generate if hasattr(CLI,'CliProvider') else None
N=[0]
import threading
_call_lock=threading.Lock()
_failures={}
def dump(self,*,model,system_prompt,user_prompt,**k):
    with _call_lock:
        N[0]+=1; call_id=N[0]
    record={'backend':'codex-cli','model':MODEL,'requested_model':model,'system':str(system_prompt),'user':str(user_prompt)}
    target=f'{OUT}/calls/{call_id:03d}.json'
    def save():
        with open(target,'w',encoding='utf-8') as f: json.dump(record,f,ensure_ascii=False,indent=1)
    save(); t0=time.time()
    try:
        r=_orig(self,model=model,system_prompt=system_prompt,user_prompt=user_prompt,**k)
    except Exception as exc:
        record.update(secs=round(time.time()-t0),error=repr(exc)); save()
        cause=type(exc).__name__+':'+str(exc)[-300:]
        with _call_lock:
            _failures[cause]=_failures.get(cause,0)+1; stop=_failures[cause]>=2
        if stop:
            log('STOP: same provider cause twice',cause)
            with open(f'{OUT}/STOP.json','w',encoding='utf-8') as f: json.dump({'cause':cause,'count':2},f,ensure_ascii=False)
            os._exit(4)
        raise
    record.update(secs=round(time.time()-t0),reply=str(r)); save(); return r
CLI.CliProvider.generate=dump
if arm=='profile':
    from exam_generator.prompt_texts import plan_v2 as T
    from exam_generator import plan_synthesis as S, plan_context as C, plan_recipe_contract as R
    prof=json.load(open(f'{L}/outputs/profile.compact.json')); blob=json.dumps(prof,ensure_ascii=False)
    T.PLAN_SYNTHESIS+=open(f'{L}/prompts/PLAN_ADDENDUM.txt').read()
    T.COMPOSER_SCOPE+=open(f'{L}/prompts/COMPOSER_ADDENDUM.txt').read()
    R.TEXT_HASHES[S.KEY]=hashlib.sha256(T.PLAN_SYNTHESIS.encode()).hexdigest()
    _rq=S.request
    def request(*a,**k):
        r=_rq(*a,**k)
        if r is not None: r['exam_profile']=prof
        return r
    S.request=request
    _db=C.data_block
    def data_block(session,part_id,role,indices=None):
        b=_db(session,part_id,role,indices)
        if role!='composer': return b
        from exam_generator.external_brief import data_block as fence
        return b+'\n\n'+fence('exam_profile',blob)
    C.data_block=data_block
from fastapi.testclient import TestClient
import web_app,launch_token
c=TestClient(web_app.app,headers={launch_token.HEADER_NAME:launch_token.token()})
name=f'LAB_{tag}'
form={'exam_type':'THPTQG','subject':subj,'de_name':name,'exam_title':'Đề kiểm tra','extra_prompt':''}
r=c.post('/api/generator/compose-drafts',json={'name':name,'form':form,'slide':'step3','artifacts':[],'matrix':{}}); did=r.json()['id']
r=c.post(f'/api/generator/compose-drafts/{did}/session'); de=r.json().get('de_name') or name; log('de',de,r.status_code)
r=c.post('/api/generator/plan-v2/prepare',json={'de_name':de}); log('prepare',r.status_code)
for i in range(360):
    p=c.get('/api/generator/plan-v2',params={'de_name':de}).json()
    if p.get('state') not in ('running','idle'): break
    time.sleep(10)
json.dump(p,open(f'{OUT}/plan.json','w'),ensure_ascii=False,indent=1); log('plan',p.get('state'),[n.get('key') for n in p.get('notices') or []])
if p.get('state')!='ready': sys.exit(2)
r=c.post('/api/generator/plan-v2/continue',json={'de_name':de,'expected':p['revisions'],'request_id':'lab-1'}); log('continue',r.status_code)
json.dump(r.json(),open(f'{OUT}/continue-response.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
if r.status_code!=200: sys.exit(3)
import jobs
last=None
for i in range(1080):
    s=c.get(f'/api/generator/session/{de}').json(); st=s.get('current_step')
    if st!=last: log(st); last=st
    if st=='DONE' or s.get('status') in ('FAILED','failed'): break
    runjobs=[j for j in jobs.list_jobs() if (j.meta or {}).get('de')==de and j.id.startswith('exam-plan-start-')]
    if runjobs and all(j.state in ('done','failed','cancelled') for j in runjobs):
        json.dump([{'id':j.id,'state':j.state,'result':j.result} for j in runjobs],open(f'{OUT}/stopped-jobs.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
        log('run stopped before DONE',[(j.state,j.result) for j in runjobs]); break
    time.sleep(10)
log('end',last,'calls',N[0])

json.dump(s,open(f'{OUT}/final-session.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
if last!='DONE': sys.exit(3)

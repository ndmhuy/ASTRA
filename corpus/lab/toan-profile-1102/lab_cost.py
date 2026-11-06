"""One real-money baseline paper: the product path, every model call sent to Anthropic directly with the owner's key.
The figure check stays on. Refuses to run twice. The key is read once and removed from the environment."""
import json,os,sys,threading,time
sys.path.insert(0,os.getcwd())
L='/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102'
tag=sys.argv[1]; DRY=os.environ.pop('LAB_COST_DRY','')=='1'
KEY=os.environ.pop('LAB_ANTHROPIC_KEY','')
CAP=float(os.environ.pop('LAB_COST_CAP_USD','5'))
if not KEY and not DRY: sys.exit('no key')
OUT=f'{L}/outputs/run-{tag}'; os.makedirs(OUT+'/calls',exist_ok=True)
LEDGER=f'{OUT}/cost.jsonl'
def log(*a): print(time.strftime('%H:%M:%S'),*a,flush=True)
from dataclasses import replace
from exam_generator.agents.providers import cli as CLI, register
from exam_generator.agents.providers.anthropic import AnthropicProvider
import model_catalog
def cost(m,u):
    row=model_catalog.price_row(m)
    if not row or not u: return None
    long=sum(u.get(x,0) for x in ('input_tokens','cache_read_input_tokens','cache_creation_input_tokens'))>row.get('long_prompt_over_tokens',10**12)
    p=lambda n: row['long_'+n] if long else row[n]
    return (u.get('input_tokens',0)*p('input')+u.get('output_tokens',0)*p('output')+u.get('cache_read_input_tokens',0)*p('cache_read')+u.get('cache_creation_input_tokens',0)*p('cache_write'))/1e6
PROFILE=os.environ.get('LECTURING_DEV_AI')
CLI.PROFILES[PROFILE]=replace(CLI.PROFILES[PROFILE],supports_images=True)
register(CLI.CliProvider(CLI.PROFILES[PROFILE]))
A=AnthropicProvider(); lock=threading.Lock(); N=[0]; TOTAL=[0.0]; fails={}
def target(model):
    low=(model or '').lower()
    return 'claude-sonnet-5-5' if 'sonnet' in low else 'claude-opus-5-5' if 'opus' in low else 'claude-haiku-5-5'
def stop(why,code=4):
    log('STOP',why); json.dump({'why':why,'usd':TOTAL[0]},open(f'{OUT}/STOP.json','w')); os._exit(code)
def generate(self,*,model,system_prompt,user_prompt,**k):
    with lock:
        N[0]+=1; cid=N[0]
        if TOTAL[0]>=CAP: stop(f'cap {CAP} reached')
    m=target(model); images=k.get('images'); usage={}
    if DRY:
        print(json.dumps({'requested':model,'sent':m,'args':sorted(k),'thinking':k.get('thinking_level'),'images':len(images or [])}),flush=True); print('price',cost(m,{'input_tokens':1000,'output_tokens':1000}),flush=True); os._exit(0)
    k.pop('api_key',None); k.pop('usage_out',None); k.pop('client_factory',None)
    rec={'id':cid,'requested':model,'model':m,'thinking':k.get('thinking_level'),'images':len(images or []),'system':str(system_prompt)[:200]}
    t0=time.time()
    try:
        r=A.generate(model=m,system_prompt=system_prompt,user_prompt=user_prompt,api_key=KEY,usage_out=usage,**k)
    except Exception as exc:
        msg=str(exc).replace(KEY,'[key]')[-300:]; rec.update(secs=round(time.time()-t0),error=type(exc).__name__+':'+msg)
        open(LEDGER,'a').write(json.dumps(rec,ensure_ascii=False)+'\n')
        with lock:
            fails[msg]=fails.get(msg,0)+1
            if fails[msg]>=3: stop('same failure three times: '+msg)
        raise
    try:
        usd=cost(m,usage)
    except Exception as exc:
        stop('cost bug '+repr(exc))
    if usd is None: stop('no usage or price for '+m)
    with lock:
        TOTAL[0]+=usd or 0
        rec.update(secs=round(time.time()-t0),usage=usage,usd=usd,total=round(TOTAL[0],4))
        open(LEDGER,'a').write(json.dumps(rec,ensure_ascii=False)+'\n')
    json.dump({**rec,'system':str(system_prompt),'user':str(user_prompt),'reply':str(r)},open(f'{OUT}/calls/{cid:03d}.json','w'),ensure_ascii=False)
    return r
CLI.CliProvider.generate=generate
from fastapi.testclient import TestClient
import web_app,launch_token,jobs
c=TestClient(web_app.app,headers={launch_token.HEADER_NAME:launch_token.token()})
name=f'LAB_{tag}'
form={'exam_type':'THPTQG','subject':'Toán','de_name':name,'exam_title':'Đề kiểm tra','extra_prompt':''}
r=c.post('/api/generator/compose-drafts',json={'name':name,'form':form,'slide':'step3','artifacts':[],'matrix':{}}); did=r.json()['id']
r=c.post(f'/api/generator/compose-drafts/{did}/session'); de=r.json().get('de_name') or name; log('de',de,r.status_code)
r=c.post('/api/generator/plan-v2/prepare',json={'de_name':de}); log('prepare',r.status_code)
for i in range(360):
    p=c.get('/api/generator/plan-v2',params={'de_name':de}).json()
    if p.get('state') not in ('running','idle'): break
    time.sleep(10)
json.dump(p,open(f'{OUT}/plan.json','w'),ensure_ascii=False,indent=1); log('plan',p.get('state'))
if p.get('state')!='ready': stop('plan not ready',2)
r=c.post('/api/generator/plan-v2/continue',json={'de_name':de,'expected':p['revisions'],'request_id':'lab-1'}); log('continue',r.status_code)
if r.status_code!=200: stop('continue refused',3)
last=None
for i in range(1080):
    s=c.get(f'/api/generator/session/{de}').json(); st=s.get('current_step')
    if st!=last: log(st); last=st
    if st=='DONE': break
    js=[j for j in jobs.list_jobs() if (j.meta or {}).get('de')==de and j.id.startswith('exam-plan-start-')]
    if js and all(j.state in ('done','failed','cancelled') for j in js): log('stopped',[(j.state,str(j.result)[:200]) for j in js]); break
    time.sleep(10)
log('end',last,'calls',N[0],'usd',round(TOTAL[0],4))
json.dump(s,open(f'{OUT}/final-session.json','w'),ensure_ascii=False)
os._exit(0 if last=='DONE' else 3)

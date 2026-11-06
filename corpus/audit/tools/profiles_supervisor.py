"""Owner-authorized continuous profile work: resume only after provider availability changes."""
from common import *
from profile_queue import checkpoint
from zoneinfo import ZoneInfo
import contextlib,io
SUBJECTS=['sinh-hoc','lich-su','toan','hoa-hoc','dia-li','vat-li','tin-hoc','gdktpl','tieng-anh','ngu-van']
STATE=ROOT/'audit/outputs/profiles-supervisor.json'

def state(status,**extra):
 dump(STATE,{'pid':os.getpid(),'state':status,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra});print(status,extra,flush=True)

def health_probe():
 d=ROOT/'audit/outputs/calls/continuous-availability-probe';d.mkdir(parents=True,exist_ok=True);n=len(list(d.glob('*.request.txt')))+1;base=d/f'attempt-{n}';prompt='Return JSON only, no tools: {"subscription_available":true}';base.with_suffix('.request.txt').write_text(prompt,encoding='utf-8');env={k:v for k,v in os.environ.items() if 'API_KEY' not in k};env['TMPDIR']=str(ROOT/'audit/work');started=time.time()
 try:
  r=subprocess.run([CLI,'exec','--skip-git-repo-check','--sandbox','read-only','--model',MODEL,'--ephemeral','--output-last-message',str(base.with_suffix('.reply.txt')),'-'],input=prompt,text=True,capture_output=True,cwd=ROOT/'audit/work',env=env,timeout=100)
 except subprocess.TimeoutExpired:return False,None,'diagnostic timeout'
 base.with_suffix('.cli.log').write_text(r.stdout+r.stderr,encoding='utf-8');dump(base.with_suffix('.meta.json'),{'model':MODEL,'backend':'codex subscription','returncode':r.returncode,'seconds':round(time.time()-started,2),'diagnostic_only':True,'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 if r.returncode==0:
  try:ok=parse(base.with_suffix('.reply.txt').read_text()).get('subscription_available') is True
  except (ValueError,OSError):ok=False
  return ok,base.with_suffix('.meta.json'),r.stderr
 return False,base.with_suffix('.meta.json'),r.stderr

def reset_deadline():
 stop=load(ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json');latest=None
 for event in stop.get('history',[]):
  for file in (ROOT/'audit/outputs/calls'/event['tag']).glob('*.cli.log'):
   if latest is None or file.stat().st_mtime>latest.stat().st_mtime:latest=file
 now=datetime.datetime.now(datetime.timezone.utc)
 if latest is None:return now+datetime.timedelta(minutes=30),False
 hint=re.search(r'try again at\s+(\d{1,2}):(\d{2})\s*(AM|PM)',latest.read_text(encoding='utf-8'),re.I)
 if not hint:return now+datetime.timedelta(minutes=30),False
 # CLI hints observed in the owner's local zone; verify with a harmless probe, never infer availability from the clock.
 local=datetime.datetime.fromtimestamp(latest.stat().st_mtime,ZoneInfo('Asia/Ho_Chi_Minh'));hour=int(hint[1])%12+(12 if hint[3].upper()=='PM' else 0);deadline=local.replace(hour=hour,minute=int(hint[2]),second=0,microsecond=0)
 if deadline<local:deadline+=datetime.timedelta(days=1)
 return deadline.astimezone(datetime.timezone.utc)+datetime.timedelta(minutes=1),True

def recover():
 stopfile=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json';stop=load(stopfile)
 if stop.get('cause')!='quota':state('needs_parent_prerequisite_recovery',cause=stop.get('cause'));return False
 for attempt in range(2):
  deadline,hint_known=reset_deadline()
  if attempt:deadline=max(deadline,datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=30))
  state('waiting_provider_availability',probe_after_utc=deadline.isoformat(),reset_hint_interpreted_as_local=hint_known)
  while datetime.datetime.now(datetime.timezone.utc)<deadline:
   if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():state('stopped_by_owner_marker');return False
   time.sleep(min(30,max(1,(deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds())))
  ok,proof,error=health_probe()
  if ok:
   archive={'reason':'Owner explicitly requested continuous work; availability probe succeeded after cooldown','probe':str(proof),'previous_stop':load(stopfile),'previous_failures':load(ROOT/'audit/outputs/model-prerequisite-failures.json')};dump(ROOT/'audit/outputs/availability-resumes'/(str(time.time_ns())+'.json'),archive);old=load(stopfile);old['active']=False;old['resolved_by_probe']=str(proof);dump(stopfile,old);dump(ROOT/'audit/outputs/model-prerequisite-failures.json',[]);state('availability_restored',probe=str(proof));return True
  state('availability_probe_failed',attempt=attempt+1,proof=str(proof),error_tail=error[-300:])
 state('needs_parent_recovery_after_two_failed_probes');return False

def main():
 with (ROOT/'audit/work/profiles-supervisor.lock').open('a',encoding='utf-8') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('Existing supervisor owns this lane')
  cycle=0
  while True:
   if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():state('stopped_by_owner_marker');return
   global_stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
   if global_stop.exists() and load(global_stop).get('active',True):
    if not recover():checkpoint();return
   cycle+=1;state('running_profiles_and_structure',cycle=cycle)
   env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');logs=[];procs=[]
   commands=[['audit/tools/profile_queue.py'],['audit/tools/profile_structures.py','--completed-only','--subjects',*SUBJECTS]]
   for idx,cmd in enumerate(commands):
    log=(ROOT/'audit/work'/f'continuous-profiles-{cycle}-{idx}.log').open('a',encoding='utf-8');logs.append(log);procs.append(subprocess.Popen([os.sys.executable,'-u',*cmd],cwd=ROOT,env=env,stdout=log,stderr=log))
   last=time.monotonic()
   while any(p.poll() is None for p in procs):
    if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():
     for p in procs:
      if p.poll() is None:p.terminate()
     state('stopped_by_owner_marker');return
    if time.monotonic()-last>=1500:checkpoint();last=time.monotonic()
    time.sleep(30)
   for log in logs:log.close()
   if global_stop.exists() and load(global_stop).get('active',True):state('profile_cycle_stopped_by_prerequisite',cycle=cycle);checkpoint();continue
   state('profiles_and_structure_ready_for_parent_QA',cycle=cycle,returncodes=[p.returncode for p in procs]);checkpoint();return
if __name__=='__main__':main()

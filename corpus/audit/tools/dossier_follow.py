"""Incremental audits, cognitive labels and original samples for completed source profiles."""
from common import *
from profile_queue import checkpoint
from prototype_coverage import coverage
from stage3 import SUBJECT_IDS
from sample_revisions import candidates as revision_candidates
import argparse,signal
STATE=ROOT/'audit/outputs/dossier-follow.json'
def state(value,**extra):dump(STATE,{'pid':os.getpid(),'state':value,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra})
def active_models():return sum('CodexCLI.app/Contents/MacOS/codex exec' in row and str(ROOT/'audit/outputs/calls') in row for row in run(['ps','-Ao','command=']).splitlines())
def stop_tree(pid):
 rows=[list(map(int,r.split())) for r in run(['ps','-Ao','pid=,ppid=']).splitlines()];owned={pid}
 while True:
  found={p for p,parent in rows if parent in owned}-owned
  if not found:break
  owned|=found
 for target in sorted(owned,reverse=True):
  try:os.kill(target,signal.SIGTERM)
  except ProcessLookupError:pass

def child(script,subject):
 log=(ROOT/'audit/work'/('dossier-'+subject+'-'+script+'.log')).open('a',encoding='utf-8');proc=subprocess.Popen([os.sys.executable,'-u','audit/tools/'+script+'.py','--subjects',subject],cwd=ROOT,stdout=log,stderr=log,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'));last=time.monotonic()
 while proc.poll() is None:
  if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():stop_tree(proc.pid);proc.wait();log.close();return -1
  if time.monotonic()-last>=1500:checkpoint();last=time.monotonic()
  time.sleep(30)
 log.close();checkpoint();return proc.returncode

def source_ready(subject):
 d=ROOT/'profiles'/subject
 if not (d/'verification.json').exists() or not (d/'profile.compact.json').exists():return False
 v=load(d/'verification.json');papers=load(d/'rows.json')['papers'];structure=load(d/'paper-structures.json') if (d/'paper-structures.json').exists() else {}
 return len(papers)>=5 and v.get('aggregate_classes_complete') and v.get('aggregate_input_current') and v.get('no_reference_inputs') and not any(v.get(k) for k in ['address_coverage_incomplete','refs_invalid','wrong_option_coverage_issues','ten_word_overlap_count','numeric_narrative_candidates']) and len(structure.get('observations',[]))==len(papers)

def pending(subject,cov):
 d=ROOT/'profiles'/subject;steps=[]
 if not (ROOT/'audit/matrices'/f'{subject}.md').exists():steps.append('stage3')
 c=next((r for r in cov['subjects'] if r['subject']==subject),None)
 if c and (c['remaining_unique'] or not (ROOT/'audit/outputs/prototype-summaries'/f'{subject}.input.json').exists()):steps.append('stage4')
 lv=load(d/'levels.json') if (d/'levels.json').exists() else {}
 if lv.get('status')!='abstract_classification_complete_pending_original_item_review':steps.append('profile_levels')
 if not steps and (d/'samples.json').exists() and revision_candidates(subject):steps.append('sample_revisions')
 if not steps and not (d/'samples.json').exists() and (ROOT/'audit/outputs/matrix-mapping'/f'{subject}.json').exists():steps.append('profile_samples')
 return steps

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--levels-pid',type=int);ap.add_argument('--wait-pid',type=int);ap.add_argument('--subjects',nargs='+',required=True);args=ap.parse_args();attempted={};holds={}
 with (ROOT/'audit/work/dossier-follow.lock').open('a',encoding='utf-8') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('Existing dossier continuation owns this lane')
  if args.wait_pid:
   while True:
    command=subprocess.run(['ps','-p',str(args.wait_pid),'-o','command='],capture_output=True,text=True).stdout
    if not any('audit/tools/'+name in command for name in ['stage4.py','profile_levels.py','profile_samples.py','sample_revisions.py']):break
    state('waiting_for_inflight_phase_to_checkpoint',inflight_pid=args.wait_pid,priority=args.subjects[0])
    if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():state('paused_by_owner');return
    time.sleep(15)
   checkpoint()
  while True:
   if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():state('paused_by_owner',holds=holds);return
   stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
   if stop.exists() and load(stop).get('active',True):
    supervisor=ROOT/'audit/outputs/profiles-supervisor.json';status=load(supervisor).get('state') if supervisor.exists() else None
    if status in ['needs_parent_recovery_after_two_failed_probes','needs_parent_prerequisite_recovery']:
     state('needs_parent_availability_recovery',holds=holds);checkpoint();return
    if status=='profiles_and_structure_ready_for_parent_QA':
     import profiles_supervisor as recovery
     recovery.STATE=ROOT/'audit/outputs/dossier-availability.json'
     state('recovering_new_quota_episode_after_source_work_finished',holds=holds)
     if not recovery.recover():state('needs_parent_availability_recovery',holds=holds);checkpoint();return
     continue
    state('waiting_for_existing_supervisor_availability_probe',holds=holds);time.sleep(30);continue
   if active_models()>=3:state('waiting_model_slot',holds=holds);time.sleep(30);continue
   cov=coverage();action=None;not_ready=[]
   for subject in args.subjects:
    if not source_ready(subject):not_ready.append(subject);continue
    digest=hashlib.sha256((ROOT/'profiles'/subject/'rows.json').read_bytes()).hexdigest()
    for step in pending(subject,cov):
     key=subject+'|'+step+'|'+digest
     if key not in attempted:action=(subject,step,key);break
    if action:break
   if not action:
    for record in cov['subjects']:
     subject=record['subject'];key=subject+'|remaining_prototype_audit'
     if subject not in args.subjects and key not in attempted and (record['remaining_unique'] or not (ROOT/'audit/outputs/prototype-summaries'/f'{subject}.input.json').exists()):
      action=(subject,'stage4',key);break
   if action:
    subject,step,key=action;state('running_'+step,subject=subject,holds=holds);rc=child(step,subject)
    if stop.exists() and load(stop).get('active',True):state('phase_saved_before_quota',subject=subject,phase=step);continue
    attempted[key]=rc;remaining=pending(subject,coverage())
    if step in remaining:holds[subject+'|'+step]={'reason':'phase returned without complete prerequisite; no unchanged third model attempt','returncode':rc}
    state('phase_returned',subject=subject,phase=step,returncode=rc,holds=holds);continue
   supervisor=ROOT/'audit/outputs/profiles-supervisor.json';status=load(supervisor).get('state') if supervisor.exists() else None
   if not_ready and status not in ['profiles_and_structure_ready_for_parent_QA','needs_parent_recovery_after_two_failed_probes','needs_parent_prerequisite_recovery']:
    state('waiting_for_source_profiles',subjects=not_ready,holds=holds);time.sleep(30);continue
   state('workload_finished_parent_QA_required_not_dossier_acceptance',source_profile_gaps=not_ready,holds=holds);checkpoint();return
if __name__=='__main__':main()

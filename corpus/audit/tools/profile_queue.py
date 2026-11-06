"""Serial, resumable profile queue. Reuses saved rows; never performs OCR."""
from common import *
from profile_progress import update
from stage3 import SUBJECT_IDS
import argparse,fcntl,signal

def _checkpoint_owned(extra_paths=()):
 # Only this research lane, no push/merge. Capture files are kept byte-for-byte.
 names=run(['git','ls-files','--modified','--others','--exclude-standard'],cwd=ROOT).splitlines()
 allowed=[n for n in names if n.startswith('profiles/') or n.startswith('audit/matrices/') or n.startswith('audit/prototypes/') or n.startswith('audit/outputs/matrix-') or n.startswith('audit/outputs/prototype-') or n.startswith('audit/outputs/topic-samples/') or n.startswith('audit/outputs/calls/extract-') or n.startswith('audit/outputs/calls/profile-levels-') or n.startswith('audit/outputs/calls/topic-samples-') or n.startswith('audit/outputs/calls/prototype-') or n.startswith('audit/outputs/calls/matrix-') or n.startswith('audit/outputs/calls/aggregate-') or n.startswith('audit/outputs/calls/paper-structure-') or n.startswith('audit/outputs/calls/continuous-availability-probe/') or n.startswith('audit/outputs/availability-resumes/') or n.startswith('audit/outputs/stops/extract-') or n.startswith('audit/outputs/stops/aggregate-') or n in ['audit/default-matrices.md','audit/proposed-matrices.json','audit/outputs/dossier-follow.json','audit/outputs/dossier-availability.json','audit/outputs/profile-progress.json','audit/outputs/profile-queue.json','audit/outputs/profiles-supervisor.json','audit/outputs/profile-publication.json','audit/outputs/data-checks.json','audit/outputs/GLOBAL-MODEL-STOP.json','audit/outputs/model-prerequisite-failures.json']]
 allowed=sorted(set(allowed)|{n for n in names if n in set(extra_paths)})
 if not allowed:return
 run(['git','add','--',*allowed],cwd=ROOT)
 staged={}
 for entry in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).split(b'\0'):
  if not entry:continue
  meta,name=entry.split(b'\t',1);staged[name.decode('utf-8')]=meta.split()[1].decode('ascii')
 sums=ROOT/'SHA256SUMS.txt';entries={}
 for line in sums.read_text(encoding='utf-8').splitlines():
  fields=line.split('  ',1)
  if len(fields)==2:entries[fields[1]]=fields[0]
 for name in allowed:
  p=ROOT/name
  if p.is_file() and name in staged:entries[name]=hashlib.sha256(subprocess.check_output(['git','cat-file','blob',staged[name]],cwd=ROOT)).hexdigest()
 sums.write_text(''.join(d+'  '+n+'\n' for n,d in sorted(entries.items())),encoding='utf-8')
 run(['git','add','--','SHA256SUMS.txt'],cwd=ROOT)
 if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:run(['git','commit','--quiet','-m','corpus: checkpoint incremental Sol profiles'],cwd=ROOT)

def checkpoint(extra_paths=()):
 with (ROOT/'audit/work/corpus-checkpoint.lock').open('a',encoding='utf-8') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  _checkpoint_owned(extra_paths)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--wait-pid',type=int);args=ap.parse_args()
 lock=(ROOT/'audit/work/profile-queue.lock').open('w',encoding='utf-8')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('Another profile queue already owns this lane')
 state=ROOT/'audit/outputs/profile-queue.json';last=time.monotonic();history=[]
 def status(stage,**kw):dump(state,{'pid':os.getpid(),'state':stage,'updated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'history':history,**kw})
 def tick():
  nonlocal last
  update()
  if time.monotonic()-last>=1500:checkpoint();last=time.monotonic()
  return (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists()
 if args.wait_pid:
  status('waiting_for_existing_subject',existing_pid=args.wait_pid,subject='sinh-hoc')
  while True:
   ps=subprocess.run(['ps','-p',str(args.wait_pid),'-o','command='],capture_output=True,text=True).stdout
   if 'stage2.py --subjects sinh-hoc' not in ps:break
   if tick():status('stopped_by_owner_marker');checkpoint();return
   time.sleep(30)
 order=['sinh-hoc','lich-su','toan','hoa-hoc','dia-li','vat-li','tin-hoc','gdktpl','tieng-anh','ngu-van']+[s for s in SUBJECT_IDS if s not in ['sinh-hoc','lich-su','toan','hoa-hoc','dia-li','vat-li','tin-hoc','gdktpl','tieng-anh','ngu-van']]
 for subject in order:
  global_stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
  if global_stop.exists() and load(global_stop).get('active',True):status('stopped_model_prerequisite',subject=subject);tick();checkpoint();return
  d=ROOT/'profiles'/subject
  if (d/'profile.compact.json').exists():
   profile=load(d/'profile.compact.json');planned=[e for e in load(ROOT/'audit/outputs/profile-inputs.json')['selected'] if e['subject']==subject];data=load(d/'rows.json');classes={p['class'] for p in data['papers']}
   if len(data['papers'])==len(planned) and set(profile.get('profiles_by_class',{}))==classes and (d/'verification.json').exists() and load(d/'verification.json').get('aggregate_input_current',True) and not load(d/'verification.json').get('address_coverage_incomplete',False):
    history.append({'subject':subject,'result':'existing_aggregate_reused'});continue
  if subject=='sinh-hoc' and args.wait_pid:
   history.append({'subject':subject,'result':'existing_run_finished; no automatic third attempt after twice-failed step'});continue
  if tick():status('stopped_by_owner_marker');checkpoint();return
  status('running_subject',subject=subject)
  with (ROOT/'audit/work'/('profile-'+subject+'.log')).open('a',encoding='utf-8') as log:
   env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');proc=subprocess.Popen([os.sys.executable,'audit/tools/stage2.py','--subjects',subject],cwd=ROOT,env=env,stdout=log,stderr=log)
   while proc.poll() is None:
    if tick():proc.terminate();proc.wait();status('stopped_by_owner_marker');checkpoint();return
    time.sleep(30)
  history.append({'subject':subject,'returncode':proc.returncode,'profile_created':(d/'profile.compact.json').exists(),'note_created':(d/'NOTE.md').exists()});tick();checkpoint();last=time.monotonic()
 status('queue_finished; inspect QA holds before accepting profiles');tick();checkpoint()
if __name__=='__main__':main()

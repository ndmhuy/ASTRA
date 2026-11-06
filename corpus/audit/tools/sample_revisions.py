"""One bounded correction of flagged synthetic samples, followed by a new blind solve."""
from common import *
from profile_samples import targets,compare
from profile_levels import definitions
from profile_verify import grams
import argparse,collections

def candidates(subject):
 d=ROOT/'profiles'/subject;path=d/'samples.json' if (d/'samples.json').exists() else d/'samples.partial.json'
 if not path.exists():return []
 data=load(path);ids={r['sample']['id'] for r in data['samples'] if not r.get('key_agreement') or not r.get('level_agreement') or r.get('independent_review',{}).get('error_flags')}
 ids|={r['id'] for r in data['issues'] if isinstance(r,dict) and r.get('id') and 'overlap' in r.get('reason','')}
 base=ROOT/'audit/outputs/sample-revisions'/subject
 return sorted(tid for tid in ids if not (base/(tid+'.accepted.json')).exists() and not (base/(tid+'.held.json')).exists())

def process(subject,ids):
 stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
 if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists() or (stop.exists() and load(stop).get('active',True)):return
 if len(ids)>4:
  for start in range(0,len(ids),4):
   stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
   if (stop.exists() and load(stop).get('active',True)) or (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():return
   process(subject,ids[start:start+4])
  return
 d=ROOT/'profiles'/subject;planned,_=targets(subject);lookup={t['id']:t for t in planned};manifest_path=d/'samples.json' if (d/'samples.json').exists() else d/'samples.partial.json';manifest=load(manifest_path);records={r['sample']['id']:r for r in manifest['samples']};work=[]
 for tid in ids:
  if any((ROOT/'audit/outputs/sample-revisions'/subject/(tid+suffix)).exists() for suffix in ['.accepted.json','.held.json']):continue
  original=None;receipt=None
  for file in (ROOT/'audit/outputs/topic-samples'/subject).glob('*.draft.json'):
   found=next((q for q in load(file)['samples'] if q['id']==tid),None)
   if found:original=found;receipt=str(file.relative_to(ROOT));break
  if original is None:continue
  prior=records.get(tid);reason={'copy_hold':any(i.get('id')==tid and 'overlap' in i.get('reason','') for i in manifest['issues'] if isinstance(i,dict)),'independent_review':prior.get('independent_review') if prior else None,'key_agreement':prior.get('key_agreement') if prior else None,'level_agreement':prior.get('level_agreement') if prior else None}
  work.append({'target':lookup[tid],'prior_synthetic_sample':original,'issue':reason,'original_receipt':receipt})
 if not work:return
 defs,codes=definitions(subject);payload={'canonical_levels':defs,'corrections':work};digest=hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest();base=ROOT/'audit/outputs/sample-revisions'/subject;draft=base/(digest+'.draft.json');proof=base/(digest+'.resolve.json');tag='sample-correction-'+subject+'-'+digest[:12];wanted={w['target']['id'] for w in work}
 instruction=(ROOT/'audit/prompts/TOPIC_SAMPLE.txt').read_text(encoding='utf-8')+'\nCORRECTION: This is ONE bounded revision of synthetic examples. Keep each target id/topic/part/shape. For a wording overlap, change the tested fact or question construction within the supported topic, not just paraphrase the sentence. For a cognitive mismatch, change the minimum cognitive action to the target level, not only the claimed label or length. Use a distinct example from the prior synthetic sample and provide full data. The subsequent solver will not see the intended key/level. Do not repair original real exams or old prototypes.\n'
 def generate():
  out=ask(tag,instruction+json.dumps(payload,ensure_ascii=False),timeout=1100)
  if {q['id'] for q in out['samples']}!=wanted or len(out['samples'])!=len(wanted):raise ValueError('REVISION_ID_COVERAGE')
  for q in out['samples']:
   t=lookup[q['id']]
   if {a['label'] for a in q['options']}!=set(t['option_labels']) or len(q['options'])!=len(t['option_labels']):raise ValueError('REVISION_OPTION_SHAPE')
   if {a['sub'] for a in q['answers']}!=set(t['slot_keys']) or len(q['answers'])!=len(t['slot_keys']):raise ValueError('REVISION_SLOT_SHAPE')
   if any(a['level'] not in codes for a in q['answers']):raise ValueError('REVISION_LEVEL_VALUE')
   if t['canonical_answer_alphabet'] and any(a['answer'] not in t['canonical_answer_alphabet'] for a in q['answers']):raise ValueError('REVISION_ANSWER_ALPHABET')
   if t['qtype']=='true_false' and ({a['sub'] for a in q['statements']}!=set(t['slot_keys']) or len(q['statements'])!=len(t['slot_keys'])):raise ValueError('REVISION_STATEMENT_SHAPE')
   if q['missing_assets'] or not q['stem'] or not q['solution']:raise ValueError('REVISION_MISSING_DATA')
   if t['option_labels']:
    wrong=set(t['option_labels'])-{q['answers'][0]['answer']}
    if {a['label'] for a in q['distractors']}!=wrong or len(q['distractors'])!=len(wrong):raise ValueError('REVISION_DISTRACTOR_COVERAGE')
  return out
 out=load(draft) if draft.exists() else twice(tag,generate)
 if out is None:return
 dump(draft,out)
 if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():return
 blind={'canonical_levels':defs,'questions':[{'id':q['id'],'qtype':lookup[q['id']]['qtype'],**{k:q[k] for k in ['stem','options','statements']}} for q in out['samples']]}
 def resolve():
  v=ask(tag+'-resolve',(ROOT/'audit/prompts/TOPIC_SAMPLE_VERIFY.txt').read_text(encoding='utf-8')+'\n'+json.dumps(blind,ensure_ascii=False),timeout=1100)
  if {r['id'] for r in v['results']}!=wanted or len(v['results'])!=len(wanted):raise ValueError('REVISION_BLIND_COVERAGE')
  for r in v['results']:
   t=lookup[r['id']]
   if {a['sub'] for a in r['answers']}!=set(t['slot_keys']) or len(r['answers'])!=len(t['slot_keys']):raise ValueError('REVISION_BLIND_SLOT_SHAPE')
   if any(a['level'] not in codes+[None] for a in r['answers']):raise ValueError('REVISION_BLIND_LEVEL')
   if r['confidence'] not in ['high','medium','low','unreadable'] or not isinstance(r['error_flags'],list):raise ValueError('REVISION_BLIND_CONFIDENCE_OR_FLAGS')
  return v
 v=load(proof) if proof.exists() else twice(tag+'-resolve',resolve)
 if v is None:return
 dump(proof,v);private=set()
 for paper in load(d/'rows.json')['papers']:private|=grams((ROOT/paper['path']).read_text(encoding='utf-8'))
 for q in out['samples']:
  t=lookup[q['id']];review=next(r for r in v['results'] if r['id']==q['id']);text=' '.join([q['stem'],q['solution']]+[a['text'] for a in q['options']+q['statements']]);overlap=private&grams(text);key={a['sub']:a['answer'] for a in q['answers']};same=all(compare(key[a['sub']],a['answer'],t['qtype']=='true_false') for a in review['answers']);levels=[a['level'] for a in review['answers']];level_ok=all(l is not None for l in levels) and max(levels,key=codes.index)==t['level'];ok=not overlap and same and level_ok and not review['error_flags'] and review['confidence'] in ['high','medium']
  record={'origin':'synthetic_not_corpus_evidence','model':MODEL,'target':t,'sample':q,'independent_review':review,'key_agreement':same,'level_agreement':level_ok,'status':'model_checks_passed_pending_teacher_review' if ok else 'bounded_revision_failed_needs_parent_review','generation_receipt':str(draft.relative_to(ROOT)),'resolve_receipt':str(proof.relative_to(ROOT)),'bounded_revision':True,'overlap_count':len(overlap),'source_rows_sha256':hashlib.sha256((d/'rows.json').read_bytes()).hexdigest()};dump(base/(q['id']+('.accepted.json' if ok else '.held.json')),record);print('REVISED',q['id'],ok,flush=True)

def reconcile(subject):
 d=ROOT/'profiles'/subject;path=d/'samples.json' if (d/'samples.json').exists() else d/'samples.partial.json'
 if not path.exists():return
 data=load(path);before=json.dumps(data,ensure_ascii=False,sort_keys=True);merged={r['sample']['id']:r for r in data['samples']};basis=hashlib.sha256((d/'rows.json').read_bytes()).hexdigest();accepted=[]
 for file in (ROOT/'audit/outputs/sample-revisions'/subject).glob('*.accepted.json'):
  r=load(file)
  if r['source_rows_sha256']!=basis:continue
  tid=r['sample']['id'];merged[tid]=r;accepted.append(tid);dump(d/'samples'/(tid+'.json'),r)
 data['samples']=sorted(merged.values(),key=lambda r:(r['target']['topic'],r['target']['part'],r['target']['level']));data['published']=len(merged);data['accepted_revision_ids']=sorted(accepted)
 for issue in data['issues']:
  if isinstance(issue,dict) and issue.get('id') in accepted:issue['resolved_by_bounded_revision']=True
 if json.dumps(data,ensure_ascii=False,sort_keys=True)!=before:
  dump(d/'samples.display.json',data)
 from profile_samples import render
 render(subject,data)
 return data

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--subject');ap.add_argument('--subjects',nargs='+');ap.add_argument('--ids',nargs='+');ap.add_argument('--reconcile-only',action='store_true');ap.add_argument('--after-pid',type=int);args=ap.parse_args();subjects=args.subjects or ([args.subject] if args.subject else [])
 if not subjects:ap.error('subject or subjects required')
 if args.after_pid:
  while True:
   ps=subprocess.run(['ps','-p',str(args.after_pid),'-o','command='],capture_output=True,text=True).stdout
   if 'audit/tools/profile_samples.py' not in ps:break
   if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():raise SystemExit('paused by owner')
   time.sleep(30)
 for subject in subjects:
  while True:
   if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():raise SystemExit('paused by owner')
   stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
   if stop.exists() and load(stop).get('active',True):time.sleep(30);continue
   final=ROOT/'profiles'/subject/'samples.json'
   if args.after_pid and not final.exists():time.sleep(30);continue
   if not args.reconcile_only:process(subject,args.ids or candidates(subject))
   reconcile(subject)
   if not (stop.exists() and load(stop).get('active',True)):break

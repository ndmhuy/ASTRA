"""Publish resumable intermediate profile receipts; never label extraction as a finished profile."""
from common import *
import collections
from stage3 import SUBJECT_IDS

def update():
 manifest=load(ROOT/'audit/outputs/profile-inputs.json');sources=collections.defaultdict(list)
 for e in manifest['selected']:sources[e['subject']].append(e)
 progress=[]
 for subject in sorted(set(sources)|set(SUBJECT_IDS)):
  entries=sources[subject]
  d=ROOT/'profiles'/subject;files=sorted((d/'rows').glob('*.json')) if d.exists() else []
  completed=[load(p) for p in files];rows=[r for x in completed for r in x.get('rows',[])];classes=collections.Counter(x.get('source',{}).get('class') for x in completed)
  final=d/'profile.compact.json';verified=d/'verification.json'
  state='aggregate_created_pending_checks' if final.exists() else 'extraction_in_progress' if completed else 'insufficient_evidence_NOTE' if (d/'NOTE.md').exists() and len(entries)<5 else 'not_started'
  if final.exists() and verified.exists():
   v=load(verified);profile=load(final);expected_classes={p['class'] for p in profile.get('evidence',{}).get('papers',[])};complete=set(profile.get('profiles_by_class',{}))==expected_classes and bool(expected_classes)
   structures=d/'paper-structures.json';observations=load(structures).get('observations',[]) if structures.exists() else [];paper_count=len(profile.get('evidence',{}).get('papers',[]))
   state='profile_created_pending_teacher_review' if complete and v.get('aggregate_input_current',True) and not v.get('address_coverage_incomplete') and not v.get('refs_invalid') and not v.get('wrong_option_coverage_issues') and not v.get('ten_word_overlap_count') and not v.get('numeric_narrative_candidates') and len(observations)>=paper_count else 'profile_created_QA_hold'
  receipt={'subject':subject,'state':state,'planned_papers':len(entries),'completed_extractions':len(completed),'rows':len(rows),'classes':dict(classes),'profile_file':str(final) if final.exists() else None}
  progress.append(receipt)
  if completed and not final.exists():
   dump(d/'progress.json',receipt)
   (d/'NOTE.md').write_text(f'# Hồ sơ {subject} — đang dựng\n\nĐã trích {len(completed)}/{len(entries)} đề, {len(rows)} slot. Chính thức: {classes["official"]}; tỉnh: {classes["provincial_third_party"]}. Model: {MODEL}.\n\nCác hàng đã xong ở rows/. Chưa có profile.compact.json tổng hợp hoàn chỉnh; không công bố tần suất hay kết luận nhiễu từ phần đang chạy. Chưa giáo viên duyệt. Trạng thái ở progress.json, receipt model ở audit/outputs/calls/.\n',encoding='utf-8')
 dump(ROOT/'audit/outputs/profile-progress.json',{'updated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'subjects':progress})
 print('\n'.join(f"{x['subject']}: {x['completed_extractions']}/{x['planned_papers']}, {x['rows']} rows, {x['state']}" for x in progress))
if __name__=='__main__':update()

"""Publish usable one-page profiles as they finish; never calls a model or OCR."""
from common import *
from profile_structures import collect
from profile_verify import verify
from profile_notes import note
from profile_topics import render
from stage3 import SUBJECT_IDS
from sample_revisions import reconcile as reconcile_samples
import contextlib,io,argparse,collections

def publish(seen):
 manifest=load(ROOT/'audit/outputs/profile-inputs.json');summaries=[]
 subjects=sorted({e['subject'] for e in manifest['selected']}|set(SUBJECT_IDS))
 for subject in subjects:
  planned=[e for e in manifest['selected'] if e['subject']==subject];d=ROOT/'profiles'/subject;rf=d/'rows.json';pf=d/'profile.compact.json';count=len(list((d/'rows').glob('*.json')));result={'subject':subject,'planned':len(planned),'extracted':count,'state':'insufficient_evidence' if len(planned)<5 else 'not_started' if not count else 'extracting_or_aggregating'}
  if rf.exists() and pf.exists():
   data=load(rf);profile=load(pf);classes={p['class'] for p in data['papers']};ready=len(data['papers'])>=5 and set(profile.get('profiles_by_class',{}))==classes and bool(classes)
   if ready:
    accepted={p['path'] for p in data['papers']};sources=[e for e in planned if e['path'] in accepted];signature=hashlib.sha256(json.dumps({'components':[(str(p),p.stat().st_mtime_ns) for p in [d/'levels.json',d/'samples.json',d/'samples.partial.json',ROOT/'audit/matrices'/f'{subject}.md',ROOT/'audit/prototypes'/f'{subject}.md'] if p.exists()],'profiles':profile['profiles_by_class'],'papers':data['papers'],'rows':len(data['rows']),'structure_inputs':[(p.name,p.stat().st_mtime_ns) for p in sorted((d/'structures').glob('*.json'))]},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    if seen.get(subject)!=signature:
     with (ROOT/'audit/work'/('profile-subject-'+subject+'.lock')).open('a',encoding='utf-8') as lock:
      try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
      except BlockingIOError:summaries.append(result);continue
      with contextlib.redirect_stdout(io.StringIO()):collect(subject,sources,completed_only=True,allow_model=False)
      verification=verify(subject);note(subject);render(subject);seen[subject]=signature
      print('PUBLISHED',subject,len(data['papers']),len(data['rows']),flush=True)
    verification=load(d/'verification.json');structure=load(d/'paper-structures.json');holds=bool(verification.get('refs_invalid') or verification.get('wrong_option_coverage_issues') or verification.get('ten_word_overlap_count') or verification.get('numeric_narrative_candidates') or verification.get('address_coverage_incomplete') or verification.get('aggregate_input_current') is False or len(structure.get('observations',[]))<len(data['papers']));result.update({'state':'profile_QA_hold' if holds else 'extraction_QA_passed_full_dossier_pending','analysed':len(data['papers']),'rows':len(data['rows']),'structure_papers':len(structure.get('observations',[]))})
  sample_view=reconcile_samples(subject) if (d/'samples.json').exists() or (d/'samples.partial.json').exists() else None
  result['matrix_audit']='Có bản chờ rà' if (ROOT/'audit/matrices'/f'{subject}.md').exists() else 'Chưa có bản'
  coverage_file=ROOT/'audit/outputs/prototype-coverage.json';coverage=load(coverage_file).get('subjects',[]) if coverage_file.exists() else [];cov=next((r for r in coverage if r['subject']==subject),None)
  result['prototype_audit']=(str(cov['graded_unique'])+'/'+str(cov['expected_unique'])+' bản đã chấm; '+('chờ rà' if (ROOT/'audit/outputs/prototype-summaries'/f'{subject}.json').exists() else 'thiếu tổng hợp')) if cov else 'Chưa có bản'
  lv=load(d/'levels.json') if (d/'levels.json').exists() else {};level_count=len(lv.get('assignments',[]));row_count=len(load(rf).get('rows',[])) if rf.exists() else 0
  result['cognitive_levels']=f'{level_count}/{row_count} đã xét; '+str(sum(a.get('level') is None for a in lv.get('assignments',[])))+' chưa rõ; chờ rà nguồn' if level_count else 'Chưa có nhãn; đang bổ sung'
  sample_file=d/'samples.json' if (d/'samples.json').exists() else d/'samples.partial.json';sample_count=sample_view.get('published',0) if sample_view else load(sample_file).get('published',0) if sample_file.exists() else 0;result['samples']=str(sample_count)+' mẫu, chờ rà' if sample_count else 'Chưa có mẫu'
  result['dossier_status']='incomplete_pending_component_QA'
  summaries.append(result)
 priority_file=ROOT/'audit/outputs/owner-priority.json';priority=load(priority_file).get('priority') if priority_file.exists() else None
 summaries.sort(key=lambda s:(s['subject']!=priority,(0 if s.get('analysed') else 1 if s['extracted'] else 2 if s['planned']>=5 else 3,s['subject'])))
 lines=['# Tiến độ hồ sơ theo môn','','Đây là tiến độ trích xuất. Hồ sơ ra đề đầy đủ còn cần audit ma trận/prototype, mức NB/TH/VD và câu mẫu mới. Qua kiểm kỹ thuật không đồng nghĩa sẵn sàng plug in. Đầu vào ở bảng chỉ đếm nguồn được chấp nhận cho nội dung; nguồn chỉ tham khảo hình thức hoặc thiếu trang không được cộng vào mẫu số này. Đề chính thức và tỉnh/trường luôn tách trong từng hồ sơ.','','| Môn | Đề đã trích / đầu vào | Ma trận | Prototype | NB/TH/VD | Câu mẫu | Hồ sơ |','|---|---:|---|---|---|---|---|']
 for s in summaries:
  path=ROOT/'profiles'/s['subject']/'NOTE.md';link=f'[{s["subject"]}]({path})' if path.exists() else 'đang làm';lines.append(f'| {s["subject"]} | {s["extracted"]}/{s["planned"]} | {s.get("matrix_audit","Đang làm")} | {s.get("prototype_audit","Đang làm")} | {s.get("cognitive_levels","Đang làm")} | {s.get("samples","Đang làm")} | {link} |')
 lines+=['','Tệp hàng/cấu trúc/kiểm định ở thư mục từng môn. Trạng thái chi tiết nguồn: [audit/STATUS.md]('+str(ROOT/'audit/STATUS.md')+').',''];(ROOT/'profiles/README.md').write_text('\n'.join(lines),encoding='utf-8');dump(ROOT/'audit/outputs/profile-publication.json',{'pid':os.getpid(),'updated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'subjects':summaries});return summaries

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--follow',action='store_true');args=ap.parse_args();seen={}
 with (ROOT/'audit/work/profile-publish.lock').open('a',encoding='utf-8') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('Publisher already running')
  while True:
   if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():print('Publisher paused by owner',flush=True);return
   publish(seen)
   if not args.follow:return
   q=ROOT/'audit/outputs/profile-queue.json'
   follow=ROOT/'audit/outputs/dossier-follow.json';follow_done=follow.exists() and load(follow).get('state','').startswith('workload_finished_parent_QA_required')
   if q.exists() and load(q).get('state','').startswith('queue_finished') and follow_done:return
   time.sleep(30)
if __name__=='__main__':main()

"""Original topic samples with blind re-solve; synthetic content never enters corpus evidence."""
from common import *
from profile_levels import definitions
from profile_verify import grams
from stage3 import SUBJECT_IDS
from registry_shape import all_shapes
import collections,argparse,math,fractions,types

def targets(subject):
 d=ROOT/'profiles'/subject;topics=load(d/'topics.json')['topics'];rows={r['ref']:r for r in load(d/'rows.json')['rows']};levels=load(d/'levels.json');labels={a['ref']:a for a in levels['assignments'] if a['level'] is not None and a['confidence'] in ['high','medium']};default=load(ROOT/'audit/outputs/defaults-snapshot.json')['subjects'][SUBJECT_IDS[subject]];shapes,resolver=all_shapes();parts=shapes['THPTQG'][SUBJECT_IDS[subject]];out=[]
 for topic in topics:
  refs=topic['support_refs'];cells=collections.defaultdict(list)
  for ref in refs:
   if ref in labels:cells[(rows[ref]['part'],labels[ref]['level'])].append(rows[ref])
  for (part,level),support in sorted(cells.items()):
   spec=next(p for p in default['parts'] if p['part_id']==part);definition=parts[part];definition=types.SimpleNamespace(**vars(definition));definition.group_size=collections.Counter(spec['slots_per_question']).most_common(1)[0][0];keys=resolver.sub_keys(definition);tid=hashlib.sha256(json.dumps([subject,topic['topic'],part,level],ensure_ascii=False).encode()).hexdigest()[:16];support.sort(key=lambda r:(r['evidence_class']!='official',r['ref']));out.append({'id':tid,'topic':topic['topic'],'part':part,'level':level,'qtype':spec['qtype'],'option_labels':list(resolver.option_labels(definition)),'slot_keys':keys,'canonical_answer_alphabet':sorted(resolver.single_char_alphabet(definition) or []),'abstract_observations':[{k:r.get(k) for k in ['given','task','reasoning','combines','difficulty_source','evidence_uncertainty','evidence_class']} for r in support[:4]],'support_refs':[r['ref'] for r in support],'official_anchor_available':any(r['evidence_class']=='official' for r in support)})
 return out,levels

def compare(a,b,tf=False):
 from file_matching import ascii_fold
 if tf:return ascii_fold(str(a)).strip().upper()==ascii_fold(str(b)).strip().upper()
 if str(a).strip().casefold()==str(b).strip().casefold():return True
 try:return math.isclose(float(fractions.Fraction(str(a).strip().replace(',','.'))),float(fractions.Fraction(str(b).strip().replace(',','.'))),rel_tol=1e-8,abs_tol=1e-8)
 except (ValueError,ZeroDivisionError):return False

def process(subject):
 d=ROOT/'profiles'/subject;planned,level_data=targets(subject);defs,codes=definitions(subject);private=set()
 for paper in load(d/'rows.json')['papers']:private|=grams((ROOT/paper['path']).read_text(encoding='utf-8'))
 published=[];issues=[];completed_phase=True
 for start in range(0,len(planned),4):
  if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():completed_phase=False;break
  stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
  if stop.exists() and load(stop).get('active',True):issues.append('model prerequisite stopped');completed_phase=False;break
  batch=planned[start:start+4];payload={'canonical_levels':defs,'targets':batch};digest=hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest();base=ROOT/'audit/outputs/topic-samples'/subject;draft=base/(digest+'.draft.json');proof=base/(digest+'.resolve.json');tag='topic-samples-'+subject+'-'+digest[:12];wanted={t['id'] for t in batch}
  def generate():
   x=ask(tag,(ROOT/'audit/prompts/TOPIC_SAMPLE.txt').read_text(encoding='utf-8')+'\n'+json.dumps(payload,ensure_ascii=False),timeout=1100)
   if {q['id'] for q in x['samples']}!=wanted or len(x['samples'])!=len(wanted):raise ValueError('SAMPLE_TARGET_COVERAGE')
   for q in x['samples']:
    t=next(t for t in batch if t['id']==q['id']);keys=[a.get('sub') for a in q['answers']]
    if len(keys)!=len(t['slot_keys']) or set(keys)!=set(t['slot_keys']):raise ValueError('SAMPLE_SLOT_SHAPE')
    if {a['label'] for a in q['options']}!=set(t['option_labels']) or len(q['options'])!=len(t['option_labels']):raise ValueError('SAMPLE_OPTION_SHAPE')
    if q.get('missing_assets') or not q.get('stem') or not q.get('solution'):raise ValueError('SAMPLE_INCOMPLETE')
    if any(a['level'] not in codes for a in q['answers']):raise ValueError('SAMPLE_LEVEL_VALUE')
    if t['qtype']=='true_false' and ({a['sub'] for a in q['statements']}!=set(t['slot_keys']) or len(q['statements'])!=len(t['slot_keys'])):raise ValueError('SAMPLE_STATEMENT_SHAPE')
    if t['canonical_answer_alphabet'] and any(a['answer'] not in t['canonical_answer_alphabet'] for a in q['answers']):raise ValueError('SAMPLE_ANSWER_ALPHABET')
    if t['option_labels']:
     key=q['answers'][0]['answer'];wrong=set(t['option_labels'])-{key}
     if {a['label'] for a in q['distractors']}!=wrong or len(q['distractors'])!=len(wrong):raise ValueError('SAMPLE_DISTRACTOR_COVERAGE')
   return x
  x=load(draft) if draft.exists() else twice(tag,generate)
  if x is None:issues.append({'batch':digest,'reason':'generation failed twice'});continue
  dump(draft,x);blind={'canonical_levels':defs,'questions':[{'id':q['id'],'qtype':next(t['qtype'] for t in batch if t['id']==q['id']),**{k:q[k] for k in ['stem','options','statements']}} for q in x['samples']]}
  def resolve():
   v=ask(tag+'-resolve',(ROOT/'audit/prompts/TOPIC_SAMPLE_VERIFY.txt').read_text(encoding='utf-8')+'\n'+json.dumps(blind,ensure_ascii=False),timeout=1100)
   if {r['id'] for r in v['results']}!=wanted or len(v['results'])!=len(wanted):raise ValueError('SAMPLE_BLIND_ID_COVERAGE')
   for r in v['results']:
    t=next(t for t in batch if t['id']==r['id']);keys=[a.get('sub') for a in r['answers']]
    if set(keys)!=set(t['slot_keys']) or len(keys)!=len(t['slot_keys']):raise ValueError('SAMPLE_BLIND_SLOT_COVERAGE')
    if r['confidence'] not in ['high','medium','low','unreadable'] or any(a['level'] not in codes+[None] for a in r['answers']):raise ValueError('SAMPLE_BLIND_VALUE')
   return v
  v=load(proof) if proof.exists() else twice(tag+'-resolve',resolve)
  if v is None:issues.append({'batch':digest,'reason':'blind resolve failed twice'});continue
  dump(proof,v)
  for q in x['samples']:
   t=next(t for t in batch if t['id']==q['id']);review=next(r for r in v['results'] if r['id']==q['id']);text=' '.join([q['stem'],q['solution']]+[a['text'] for a in q['options']+q['statements']]);overlap=private&grams(text)
   if overlap:issues.append({'id':q['id'],'reason':'source ten-word overlap; draft withheld from profile','overlap_count':len(overlap)});continue
   expected={a['sub']:a['answer'] for a in q['answers']};agreement=all(compare(expected[a['sub']],a['answer'],t['qtype']=='true_false') for a in review['answers']);observed=[a['level'] for a in review['answers']];level_ok=all(l is not None for l in observed) and max(observed,key=codes.index)==t['level'];hold=not agreement or not level_ok or bool(review['error_flags']) or review['confidence'] not in ['high','medium'] or t['qtype'] in ['text_answer','essay']
   record={'origin':'synthetic_not_corpus_evidence','model':MODEL,'target':t,'sample':q,'independent_review':review,'key_agreement':agreement,'level_agreement':level_ok,'status':'needs_teacher_review_with_flags' if hold else 'model_checks_passed_pending_teacher_review','generation_receipt':str(draft.relative_to(ROOT)),'resolve_receipt':str(proof.relative_to(ROOT))};dump(d/'samples'/(q['id']+'.json'),record);published.append(record)
  print('SAMPLES',subject,len(published),'/',len(planned),flush=True)
  dump(d/'samples-progress.json',{'subject':subject,'planned':len(planned),'published':len(published),'status':'in_progress_pending_teacher_review','sample_files':[str((d/'samples'/(r['sample']['id']+'.json')).relative_to(ROOT)) for r in published]})
  publish(subject,planned,level_data,published,issues,False)
 publish(subject,planned,level_data,published,issues,completed_phase)

def publish(subject,planned,level_data,published,issues,phase_complete):
 d=ROOT/'profiles'/subject
 result={'schema_version':'topic-samples-v1','origin':'synthetic_not_corpus_evidence','status':'sample_library_pending_teacher_review_and_archetype_coverage','planned_cells':len(planned),'published':len(published),'cognitive_evidence_status':level_data['status'],'coverage_unit':'One example per topic/part/high-or-medium-confidence cognitive level. Multiple archetypes within a cell are not all covered; unknown levels remain a gap.','samples':published,'issues':issues};result['generation_phase_complete']=phase_complete;dump(d/('samples.json' if phase_complete else 'samples.partial.json'),result)
 render(subject,result)

def render(subject,result):
 d=ROOT/'profiles'/subject;published=result['samples'];issues=result['issues'];planned=[None]*result['planned_cells']
 lines=['# Câu mẫu mới — '+subject,'','Câu do Sol viết mới, không phải đề thật hoặc bằng chứng tần suất. Chưa giáo viên duyệt. Nhãn mục tiêu dựa trên phân loại khái quát; xem LEVELS.md. Một mẫu cho mỗi ô chủ đề/phần/mức có căn cứ, chưa bảo đảm phủ mọi dạng trong cùng ô.','',f'Đã xuất {len(published)}/{len(planned)} mẫu dự kiến; các mẫu có cờ không được coi là sẵn dùng.','']
 for record in published:
  q=record['sample'];t=record['target'];status_label={'model_checks_passed_pending_teacher_review':'Đã qua kiểm bằng model; chờ giáo viên rà.','needs_teacher_review_with_flags':'Còn cờ cần rà; chưa dùng làm mẫu chuẩn.','bounded_revision_failed_needs_parent_review':'Lượt sửa vẫn còn cờ; cần rà trước khi sử dụng.'}.get(record['status'],record['status']);lines+=['## '+t['topic']+' / '+t['part']+' / '+t['level'],'',status_label,'',q['stem'],'']+['- '+a['label']+'. '+a['text'] for a in q['options']]+['- '+a['sub']+') '+a['text'] for a in q['statements']]+['','Đáp án: '+'; '.join((a['sub']+') ' if a['sub'] else '')+a['answer'] for a in q['answers']),'','Lời giải: '+q['solution'],'','Lỗi tạo nhiễu:']+['- '+str(a.get('label') or a.get('sub'))+': '+a['mistake']+' — '+a['why_plausible'] for a in q['distractors']]+['','Mức dự kiến: '+q['level_reason'],'','Tiên quyết: '+'; '.join(q['prerequisites']),'','Biến thể: '+q['variation_guidance'],'','Đối chiếu khóa: '+('khớp' if record['key_agreement'] else 'còn bất đồng')+'. Đối chiếu mức: '+('khớp' if record['level_agreement'] else 'còn khác mức mục tiêu')+'.','', 'Mức do lượt tự giải nhận định: '+'; '.join((str(a.get('sub'))+': ' if a.get('sub') else '')+str(a.get('level')) for a in record['independent_review']['answers'])+'. '+record['independent_review'].get('level_reason',''),'','Cờ lượt tự giải: '+('; '.join(record['independent_review']['error_flags']) or 'không có cờ nội dung; xem riêng đối chiếu mức ở trên'),'']
 lines+=['## Khoảng thiếu và giới hạn','',json.dumps(issues,ensure_ascii=False),''];(d/'SAMPLES.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--subjects',nargs='+',required=True);args=ap.parse_args()
 for subject in args.subjects:
  if not (ROOT/'profiles'/subject/'levels.json').exists():print('SKIP',subject,'cognitive labels not ready');continue
  with (ROOT/'audit/work'/('profile-samples-'+subject+'.lock')).open('a',encoding='utf-8') as lock:
   try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:continue
   process(subject)
   stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
   if not (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists() and not (stop.exists() and load(stop).get('active',True)):
    from sample_revisions import candidates,process as revise,reconcile
    revise(subject,candidates(subject));reconcile(subject)
    if stop.exists() and load(stop).get('active',True) and (ROOT/'profiles'/subject/'samples.json').exists():
     final=ROOT/'profiles'/subject/'samples.json';pending=ROOT/'profiles'/subject/'samples.partial.json';state=load(final);state['generation_phase_complete']=False;state['correction_phase_status']='waiting_subscription_after_cached_generation';dump(pending,state);final.unlink()

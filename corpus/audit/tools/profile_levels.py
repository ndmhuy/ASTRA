"""Independent cognitive labels on abstract evidence; never equate them to discrimination."""
from common import *
from stage3 import SUBJECT_IDS
import collections,argparse

def definitions(subject):
 snap=load(ROOT/'audit/outputs/level-scheme-snapshot.json');files=snap['files'];scheme=next(v['data'] for p,v in files.items() if p.endswith('/default.json'));layer=next((v['data'] for p,v in files.items() if p.endswith('/subjects/'+subject+'.json') and v['data'].get('status')=='APPROVED'),None)
 approved=[r for r in scheme['levels'] if r.get('status')=='APPROVED'];codes=[r['code'] for r in approved]
 return {'revision':snap['product_revision'],'scheme_id':scheme['id'],'scheme_version':scheme['version'],'preamble':scheme.get('preamble_en'),'levels':approved,'subject_layer':layer},codes

def process(subject):
 d=ROOT/'profiles'/subject;data=load(d/'rows.json');profile=load(d/'profile.compact.json');verification=load(d/'verification.json')
 if len(data['papers'])<5 or not verification.get('aggregate_classes_complete') or not verification.get('aggregate_input_current'):raise ValueError('Profile prerequisite not accepted')
 defs,codes=definitions(subject);rows=data['rows'];assignments=[];issues=[]
 for n in range(0,len(rows),40):
  if (ROOT/'audit/outputs/PROFILE-QUEUE-STOP').exists():return
  stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
  if stop.exists() and load(stop).get('active',True):issues.append('model prerequisite stopped');break
  chunk=rows[n:n+40];targets=[{k:r.get(k) for k in ['ref','part','idx','sub','topic','grade','given','task','reasoning','combines','cue_use','evidence_uncertainty']} for r in chunk];payload={'canonical_levels':defs,'evidence_basis':'abstract extracted descriptions, not original full questions','items':targets};digest=hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest();path=d/'levels'/(str(n//40)+'-'+digest[:12]+'.json');tag='profile-levels-'+subject+'-'+digest[:12]
  def classify():
   out=ask(tag,(ROOT/'audit/prompts/PROFILE_LEVELS.txt').read_text(encoding='utf-8')+'\n'+json.dumps(payload,ensure_ascii=False),timeout=1000);want={r['ref'] for r in chunk};got=[a['ref'] for a in out['assignments']]
   if set(got)!=want or len(got)!=len(want):raise ValueError('COGNITIVE_LEVEL_REF_COVERAGE')
   for a in out['assignments']:
    if a['level'] not in codes+[None] or a['confidence'] not in ['high','medium','low','insufficient']:raise ValueError('COGNITIVE_LEVEL_VALUE')
    if a['confidence']=='insufficient' and a['level'] is not None:raise ValueError('COGNITIVE_INSUFFICIENT_NEEDS_NULL')
    if not a.get('justification') or not a.get('decisive_demand'):raise ValueError('COGNITIVE_LEVEL_EXPLANATION')
   return {'input_sha256':digest,'model':MODEL,'assignments':out['assignments']}
  out=load(path) if path.exists() else twice(tag,classify)
  if out is None:issues.append(tag+' failed twice');continue
  if out['input_sha256']!=digest:raise ValueError('COGNITIVE_LEVEL_STALE_INPUT')
  dump(path,out);assignments+=out['assignments'];print('LEVELS',subject,len(assignments),'/',len(rows),flush=True)
  dump(d/'levels-progress.json',{'subject':subject,'classified':len(assignments),'total':len(rows),'status':'classification_in_progress','evidence_basis':'abstract extraction, not original-item validation'})
 lookup={a['ref']:a for a in assignments};mp=ROOT/'audit/outputs/matrix-mapping'/f'{subject}.json';mapping={m['input_topic']:m.get('default_topic') or m['family_topic'] for m in load(mp)['topic_mapping']} if mp.exists() else {};by=collections.defaultdict(collections.Counter);per_question=collections.defaultdict(list)
 for r in rows:
  level=lookup.get(r['ref'],{}).get('level');cls=r['evidence_class'];topic=mapping.get(r['topic'],r['topic']);by[(cls,r['part'],topic)][level]+=1;per_question[(cls,r['paper_id'],r['part'],r['idx'])].append(level)
 question_counts=collections.defaultdict(collections.Counter)
 for (cls,pid,part,idx),levels in per_question.items():
  level=None if any(l is None for l in levels) else max(levels,key=codes.index);question_counts[(cls,part)][level]+=1
 summary=[{'class':k[0],'part':k[1],'topic':k[2],'counts':{str(l):c for l,c in v.items()}} for k,v in sorted(by.items())];complete=len(lookup)==len(rows)
 result={'schema_version':'profile-cognitive-levels-v1','model':MODEL,'status':'abstract_classification_complete_pending_original_item_review' if complete else 'partial','evidence_basis':'abstract extraction only; no claim of original-item or teacher validation','definition_snapshot':defs,'assignments':assignments,'topic_level_counts':summary,'question_level_counts':[{'class':k[0],'part':k[1],'counts':{str(l):c for l,c in v.items()}} for k,v in sorted(question_counts.items())],'question_count_policy':'Maximum level of all observed statement labels; any unknown statement makes question unknown. This is an explicit analytical proxy, not a printed exam declaration.','issues':issues};dump(d/'levels.json',result)
 den=collections.Counter(p['class'] for p in data['papers']);defaults=load(ROOT/'audit/outputs/defaults-snapshot.json')['subjects'][SUBJECT_IDS[subject]];lines=['# Mức nhận thức theo ma trận — '+subject,'','Nhãn mới do Sol gán theo định nghĩa canonical, dựa trên khái quát đã trích. Chưa kiểm lại toàn bộ đề gốc; không thay nhãn giáo viên. Không quy đổi từ nhãn phân hóa. Chỗ không đủ thông tin giữ chưa rõ.','',f'Đã phân loại {len(lookup)}/{len(rows)} câu/ý.','', '| Nguồn / phần | NB | TH | VD | Chưa rõ |','|---|---:|---:|---:|---:|']
 for (cls,part),ct in sorted(question_counts.items()):lines.append('| '+cls+' / '+part+' | '+' | '.join(str(ct[l]) for l in codes+[None])+' |')
 lines+=['','Bảng trên đếm câu phân biệt, lấy mức cao nhất của các ý chỉ khi mọi ý đã rõ; đây là proxy cần rà. Các nhánh tự chọn cùng được thống kê theo tập câu in, không giả định học sinh làm cả hai.','', '## Theo chủ đề — đơn vị câu/ý','', '| Nguồn / phần / chủ đề | NB | TH | VD | Chưa rõ |','|---|---:|---:|---:|---:|']
 for r in summary:lines.append('| '+r['class']+' / '+r['part']+' / '+r['topic']+' | '+' | '.join(str(r['counts'].get(str(l),0)) for l in codes+[None])+' |')
 lines+=['','## Ma trận mặc định — đơn vị slot câu','', '| Phần | Chủ đề | Mức | Số slot |','|---|---|---|---:|']
 for r in defaults['rows']:lines.append(f'| {r["part_id"]} | {r["topic"]} | {r["level"]} | {r["count"]} |')
 lines+=['','Đơn vị câu/ý của bảng chủ đề không được so trực tiếp với slot câu của default TF; một câu tích hợp có thể hiện diện nhiều chủ đề. Official và tỉnh không gộp; mẫu số đề lần lượt '+str(den['official'])+' và '+str(den['provincial_third_party'])+'. Xem levels.json để truy ref, nhận định và bất định.',''];(d/'LEVELS.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--subjects',nargs='+',required=True);args=ap.parse_args()
 for subject in args.subjects:
  with (ROOT/'audit/work'/('profile-enrich-'+subject+'.lock')).open('a',encoding='utf-8') as lock:
   try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:continue
   process(subject)

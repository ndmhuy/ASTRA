from common import *
from addresses import *
from catalog_context import catalog_context
from profile_verify import verify as verify_saved_profile
from profile_inputs import matched_key, source_images, source_content_issues
from stage3 import SUBJECT_IDS
import csv,collections
P=ROOT/'audit/prompts'
def topic_counts(rows):
 grouped=collections.defaultdict(set);gradepapers=collections.defaultdict(set);high=[];distr=collections.defaultdict(lambda:collections.Counter());facts=collections.defaultdict(collections.Counter)
 for x in rows:
  kind=x['evidence_class'];paper=x['paper_id'];part=x['part'];grade=str(x.get('grade'));topic=x['topic'];grouped[(kind,part,grade,topic)].add(paper);gradepapers[(kind,part,grade)].add(paper)
  if x.get('discrimination')=='high':high.append({k:x.get(k) for k in ['ref','evidence_class','topic','grade','task','reasoning','steps','combines','difficulty_source','evidence_uncertainty']})
  facts[kind][x.get('cue_use','unknown')]+=1
  for d in x.get('wrong_option_details') or []:
   val=d.get('identifiable_error');distr[kind]['identifiable' if val is True else 'not_identifiable' if val is False else 'unverified']+=1
   if val is True:distr[kind]['kind:'+str(d.get('mistake_kind'))]+=1
 for cls,part in {(x['evidence_class'],x['part']) for x in rows}:
  for grade in ['10','11','12','None']:gradepapers.setdefault((cls,part,grade),set())
 return {'grade_uncertainty_note':'Zero means no such grade label among analysed rows, not proof of absence when unknown-grade rows exist.', 'optional_path_rows':[{'ref':x['ref'],'path':x.get('optional_path')} for x in rows if x.get('optional_path')], 'topic_distribution':[{'class':k[0],'part':k[1],'grade':k[2],'topic':k[3],'distinct_papers':len(v),'paper_ids':sorted(v)} for k,v in sorted(grouped.items())], 'grade_presence':[{'class':k[0],'part':k[1],'grade':k[2],'distinct_papers':len(v)} for k,v in sorted(gradepapers.items())],'high_discrimination_rows':high,'distractors':{k:{**dict(v),'share_identifiable_among_judged':v['identifiable']/(v['identifiable']+v['not_identifiable']) if v['identifiable']+v['not_identifiable'] else None} for k,v in distr.items()},'fact_use_counts':dict(facts)}
def references(x,known,bad):
 if isinstance(x,dict):
  for k,v in x.items():
   if k=='refs' or k.endswith('_refs'):
    for ref in v:
     if ref not in known:bad.append(ref)
   else:references(v,known,bad)
 elif isinstance(x,list):
  for v in x:references(v,known,bad)
def validated_profile(tag,prompt,known):
 x=ask(tag,prompt,timeout=1000);bad=[]
 if any(k not in x for k in ['patterns','discrimination_moves','easy_vs_hard','fact_use','anti_patterns']):raise ValueError('PROFILE_SCHEMA')
 references(x,known,bad)
 if bad:raise ValueError('PROFILE_INVALID_REFS '+str(bad[:5]))
 return x

def annotate_counts(x):
 if isinstance(x,dict):
  if isinstance(x.get('refs'),list):
   refs=set(x['refs']);x['paper_count']=len({r.split('|')[0] for r in refs});x['row_count']=len(refs)
  for v in list(x.values()):annotate_counts(v)
 elif isinstance(x,list):
  for v in x:annotate_counts(v)

def aggregate_batched(subject,cls,rows):
 chunks=[];current=[];chars=0
 for row in rows:
  size=len(json.dumps(row,ensure_ascii=False))
  if current and chars+size>90000:chunks.append(current);current=[];chars=0
  current.append(row);chars+=size
 if current:chunks.append(current)
 partials=[]
 for i,rs in enumerate(chunks):
  p=ROOT/'profiles'/subject/f'aggregate-{cls}-chunk{i}.json';tag=f'aggregate-{subject}-{cls}-chunk{i}'
  x=load(p) if p.exists() else twice(tag,lambda:validated_profile(tag,(P/'AGGREGATE.txt').read_text(encoding='utf-8')+'\nEVIDENCE CLASS: '+cls+'; single-paper observations are not recurrence.\nROWS:\n'+json.dumps(rs,ensure_ascii=False),{r['ref'] for r in rs}))
  if x is None:return None
  dump(p,x);partials.append(x)
 round_no=0
 while len(partials)>1:
  groups=[];current=[];chars=0
  for partial in partials:
   size=len(json.dumps(partial,ensure_ascii=False))
   if current and chars+size>110000:groups.append(current);current=[];chars=0
   current.append(partial);chars+=size
  if current:groups.append(current)
  if all(len(g)==1 for g in groups):groups=[partials[i:i+2] for i in range(0,len(partials),2)]
  merged=[]
  for i,group in enumerate(groups):
   if len(group)==1:merged.append(group[0]);continue
   tag=f'aggregate-merge-{subject}-{cls}-r{round_no}-g{i}';path=ROOT/'profiles'/subject/(tag+'.json')
   x=load(path) if path.exists() else twice(tag,lambda:validated_profile(tag,(P/'MERGE_PROFILES.txt').read_text(encoding='utf-8')+'\n'+json.dumps(group,ensure_ascii=False),{r['ref'] for r in rows}))
   if x is None:return None
   dump(path,x);merged.append(x)
  partials=merged;round_no+=1
 return partials[0]

def process(subject,entries):
 d=ROOT/'profiles'/subject;d.mkdir(parents=True,exist_ok=True);allrows=[];usable=[];issues=[]
 if len(entries)<5:
  sources=[{'path':e['path'],'class':e['class'],'year':e.get('year'),'model':None} for e in entries]
  dump(d/'rows.json',{'extraction_model':None,'papers':sources,'rows':[],'issues':['Below minimum paper count; no EXTRACT/aggregate model calls made.']})
  dump(d/'distributions.json',{'status':'insufficient_evidence','paper_count':len(entries),'no_frequency_claim':True})
  (d/'NOTE.md').write_text(f'# {subject}\n\nChưa đủ bằng chứng: {len(entries)} đề đủ điều kiện, ít hơn năm. Không chạy EXTRACT/aggregate để tạo hồ sơ hoặc công bố tần suất. Nguồn thật đã có vẫn được giữ cho kiểm hình thức của mẫu mới nếu phù hợp; không biến một đề thành quy luật.\n',encoding='utf-8')
  return
 for ent in entries:
  prerequisite=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
  if prerequisite.exists() and load(prerequisite).get('active',True):issues.append({'reason':'Model prerequisite stopped; remaining papers not attempted'});break
  source=ROOT/ent['path'];pid=hashlib.sha256(ent['path'].encode()).hexdigest()[:12];out=d/'rows'/(pid+'.json');md=source.read_text(encoding='utf-8');structure=load(source.with_name('structure.json')) if source.with_name('structure.json').exists() else {};ex=expected(md,structure.get('parts'))
  content_issues=source_content_issues(source)
  if content_issues:issues.append({'source':ent['path'],'reason':'Incomplete statement shape; no model call','details':content_issues});continue
  if not ex:issues.append({'source':ent['path'],'reason':'Không đọc được địa chỉ câu bằng bộ đọc tổng quát'});continue
  key,key_status=matched_key(source,ent)
  images,image_status=source_images(source)
  official_rows=sorted([r for r in allrows if r['evidence_class']=='official'],key=lambda r:str(r.get('year','')),reverse=True)
  selected_anchors=[r for r in official_rows if r.get('discrimination')=='high'][:8]+[r for r in official_rows if r.get('discrimination')!='high'][:8]
  anchors=[{k:r.get(k) for k in ['part','topic','task','reasoning','steps','discrimination','difficulty_source','evidence_uncertainty']} for r in selected_anchors]
  def extract(target_addresses=None,call_tag=None):
   target_ex=ex if target_addresses is None else target_addresses
   scope='\nSCOPE: Only return the listed expected addresses; other paper items provide context only.\n' if target_addresses is not None else ''
   x=ask(call_tag or 'extract-'+subject+'-'+pid,(P/'EXTRACT.txt').read_text(encoding='utf-8')+scope+'\nPAPER_META:\n'+json.dumps({k:ent.get(k) for k in ['subject','year','class']},ensure_ascii=False)+'\nCURRICULUM_METADATA_REFERENCE:\n'+json.dumps(catalog_context(subject),ensure_ascii=False)+'\nOFFICIAL_CALIBRATION_ABSTRACT_ONLY:\n'+json.dumps(anchors,ensure_ascii=False)+'\nPRINTED_TO_LOCAL_ADDRESS_MAP:\n'+json.dumps([{k:q[k] for k in ['part','printed_idx','idx']} for q in indexed_questions(md,structure.get('parts'))])+'\nEXPECTED_ADDRESSES:\n'+json.dumps(sorted(target_ex,key=str))+'\nKEY_STATUS: '+key_status+'; if null, do not derive which options are wrong from keys visible in source images.\nIMAGE_STATUS: '+image_status+'\nMATCHED_KEY_OR_NULL:\n'+json.dumps(key,ensure_ascii=False)+'\nPAPER:\n'+md,images=images,timeout=1000)
   required={'part','idx','sub','topic','grade','given','task','reasoning','steps','combines','wrong_options','cue_use','difficulty_source','discrimination','wrong_option_details'}
   for row in x['rows']:
    if not required.issubset(row):raise ValueError('EXTRACT_FIELDS_MISSING '+str(sorted(required-set(row))))
    if isinstance(row.get('grade'),str) and row['grade'] in ['10','11','12']:row['grade']=int(row['grade'])
    if row.get('grade') not in [10,11,12,None]:raise ValueError('EXTRACT_GRADE')
    if isinstance(row.get('steps'),str) and row['steps'].isdigit():row['steps']=int(row['steps'])
    if row.get('steps') is not None and (type(row['steps']) is not int or row['steps']<1):raise ValueError('EXTRACT_STEPS')
    if row.get('discrimination')=='unknown':row['discrimination']=None
    if row.get('discrimination') not in ['low','medium','high',None]:raise ValueError('EXTRACT_DISCRIMINATION')
    if not isinstance(row.get('combines'),list) or not row.get('topic'):raise ValueError('EXTRACT_TOPIC_OR_COMBINES')
    if row.get('wrong_option_details') is None and row.get('wrong_options') is None:row['wrong_option_details']=[]
    if not isinstance(row.get('wrong_option_details'),list):raise ValueError('EXTRACT_OPTION_DETAILS')
    for opt in row['wrong_option_details']:
     if opt.get('identifiable_error') is not None and type(opt.get('identifiable_error')) is not bool:raise ValueError('EXTRACT_OPTION_BOOLEAN')
   got=[(canon(r['part']),int(r['idx']),r.get('sub')) for r in x['rows']]
   if set(got)!=target_ex or len(got)!=len(target_ex):raise ValueError('ADDRESS_MISMATCH '+str({'expected':len(target_ex),'got':len(got),'missing':sorted(target_ex-set(got),key=str),'extra':sorted(set(got)-target_ex,key=str)}))
   if key is None:
    for row in x['rows']:
     for opt in row.get('wrong_option_details') or []:
      if opt.get('identifiable_error') is not None:raise ValueError('UNVERIFIED_KEY_OPTION_JUDGEMENT')
   return x
  if out.exists():
   x=load(out);before=json.dumps(x,ensure_ascii=False,sort_keys=True)
   mapping={(q['part'],q['printed_idx']):q['idx'] for q in indexed_questions(md,structure.get('parts'))};kept=[];superseded=[]
   for row in x['rows']:
    printed=row.get('printed_idx',row['idx']);part=canon(row['part']);idx=mapping.get((part,int(printed)),int(row['idx']));row['printed_idx']=int(printed);row['part']=part;row['idx']=idx
    if (part,idx,row.get('sub')) in ex:kept.append(row)
    else:superseded.append({'part':part,'idx':idx,'sub':row.get('sub'),'reason':'cached address no longer scored after source-boundary/parser correction'})
   if json.dumps(x,ensure_ascii=False,sort_keys=True)!=before or superseded:
    archive=ROOT/'audit/outputs/cache-address-reconciliation'/subject/(pid+'.before.json')
    if not archive.exists():dump(archive,load(out))
   x['rows']=kept
   if superseded:x['superseded_address_records']=superseded
   missing=ex-{(r['part'],r['idx'],r.get('sub')) for r in kept}
   if missing:
    tag='extract-supplement-'+subject+'-'+pid+'-'+hashlib.sha256(str(sorted(missing,key=str)).encode()).hexdigest()[:8]
    extra=twice(tag,lambda:extract(missing,tag))
    if extra is None:issues.append({'source':ent['path'],'reason':'Missing-address supplement failed twice; source omitted from accepted profile rows'});continue
    x['rows']+=extra['rows'];x.setdefault('supplement_receipts',[]).append(tag)
  else:x=twice('extract-'+subject+'-'+pid,extract)
  if x is None:issues.append({'source':ent['path'],'reason':'Trích thất bại hai lần; xem stops'});continue
  for r in x['rows']:
   r['part']=canon(r['part']);r['idx']=int(r['idx']);r['paper_id']=pid;r['year']=ent.get('year');r['evidence_class']=ent['class'];r['ref']=f"{pid}|{r['part']}|{r['idx']}|{r.get('sub')}"
  x['source']={**x.get('source',{}),'path':ent['path'],'class':ent['class'],'year':ent.get('year'),'model':MODEL,'has_matched_key':key is not None,'key_status':key_status,'image_status':x.get('source',{}).get('image_status',image_status),'supplement_image_status':image_status if x.get('supplement_receipts') else None,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()};dump(out,x);allrows+=x['rows'];usable.append(x['source'])
 dump(d/'rows.json',{'model':MODEL,'papers':usable,'rows':allrows,'issues':issues})
 stats=topic_counts(allrows)
 if len(usable)>=5:dump(d/'distributions.json',stats)
 else:dump(d/'distributions.json',{'status':'insufficient_evidence','paper_count':len(usable),'no_frequency_claim':True})
 if len(usable)<5:
  (d/'NOTE.md').write_text(f'# {subject}\n\nChưa đủ bằng chứng: {len(usable)} đề đọc được; cần ít nhất 5 đề không tham khảo. Không công bố tần suất, không đề xuất ma trận.\n\nModel: {MODEL}; nhãn do model ước lượng, chưa giáo viên duyệt.\n',encoding='utf-8');return
 prerequisite=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
 if prerequisite.exists() and load(prerequisite).get('active',True):
  (d/'NOTE.md').write_text(f'# Hồ sơ {subject} — tạm dừng\n\nĐã trích {len(usable)}/{len(entries)} đề, {len(allrows)} slot. Subscription báo lỗi hai lần; các bước còn lại và aggregate chưa chạy tiếp. Giữ hàng đã xong để nối sau khi có probe thành công. Không coi compact cũ là kết quả của toàn bộ đầu vào mới.\n',encoding='utf-8');return
 # official and provincial never enter the same aggregate call.
 combined={};known={r['ref'] for r in allrows};bad=[]
 for cls in sorted({x['evidence_class'] for x in allrows}):
  rs=[r for r in allrows if r['evidence_class']==cls];path=d/f'profile.{cls}.json'
  x=load(path) if path.exists() else aggregate_batched(subject,cls,rs)
  if x is not None:references(x,{r['ref'] for r in rs},bad);annotate_counts(x);dump(path,x);combined[cls]=x
 dump(d/'profile.compact.json',{'status':'complete_pending_teacher_review' if set(combined)=={r['evidence_class'] for r in allrows} else 'partial_aggregation','subject':subject,'extraction_model':MODEL,'evidence':{'papers':usable,'classes_separate':True},'profiles_by_class':combined,'code_derived':stats})
 audit=verify_saved_profile(subject);bad=audit['refs_invalid'];overlap=range(audit['ten_word_overlap_count']);numbers=audit['numeric_narrative_candidates']
 byclass=collections.Counter(e['class'] for e in usable)
 note=f'# Hồ sơ {subject}\n\nAggregate hoàn thành cho {len(combined)}/{len({r["evidence_class"] for r in allrows})} lớp bằng chứng; chỉ đọc như hồ sơ đầy đủ khi hai số khớp.\n\nĐề chính thức: {byclass["official"]}; đề tỉnh: {byclass["provincial_third_party"]}. Hai lớp bằng chứng được tổng hợp riêng; không cộng tần suất. {len(allrows)} ý/câu được gắn nhãn. Model trích duy nhất: {MODEL}.\n\nTệp `distributions.json` đếm số đề phân biệt có từng chủ đề theo phần và lớp; lớp 10, 11 giữ riêng, lớp chưa rõ là null. Một câu có nhiều ý chỉ tính một lần cho hiện diện chủ đề/đề.\n\nNhãn phân hoá và lỗi nhiễu là nhận định model, không phải số liệu học sinh. Chỉ tỷ lệ trong các phương án được xác định khóa và được phán đoán; chưa kiểm được giữ riêng. Chi tiết ở `distributions.json`.\n\nKiểm refs sai: {len(bad)}; trùng mười từ: {len(overlap)}; chuỗi có chữ số cần xem: {len(numbers)}. Kiểm chuỗi không chứng minh không sao chép ý nghĩa. Nguồn ảnh/hình mô tả còn hạn chế; mọi kết luận cần giáo viên rà. Xem rows.json để truy nguyên.\n'
 (d/'NOTE.md').write_text(note,encoding='utf-8')
 print('PROFILE',subject,len(usable),len(allrows),'refs_bad',len(bad),flush=True)
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--subjects',nargs='*');args=ap.parse_args()
 manifest=load(ROOT/'audit/outputs/profile-inputs.json');entries=manifest['selected']
 subjects=args.subjects or sorted({x['subject'] for x in entries}|set(SUBJECT_IDS))
 for subject in subjects:
  stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
  if stop.exists() and load(stop).get('active',True):print('STOP_MODEL_PREREQUISITE',flush=True);break
  es=[x for x in entries if x['subject']==subject]
  for e in es:
   if hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()!=e['source_sha256']:raise ValueError('FROZEN_SOURCE_CHANGED '+e['path'])
  with (ROOT/'audit/work'/('profile-subject-'+subject+'.lock')).open('a',encoding='utf-8') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   process(subject,es)

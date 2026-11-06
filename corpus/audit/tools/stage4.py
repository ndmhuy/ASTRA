from common import *
from addresses import *
from option_measure import source_options
from prototype_summary import summarise
from prototype_quality import attach as attach_quality
import secrets,collections,math
from stage3 import ALIASES,SUBJECT_IDS
from registry_shape import option_labels_for, product_root
os.sys.path.insert(0,str(product_root()))
from file_matching import ascii_fold

def textonly(s):
 s=re.sub(r'\\(?:textbf|textit|mathrm|text|mathbf|operatorname)\{([^{}]*)\}',r'\1',s)
 s=re.sub(r'\\[a-zA-Z]+(?:\[[^]]*\])?', ' ',s);s=re.sub(r'[{}$\\]',' ',s);return re.sub(r'\s+',' ',s).strip()
def metric(rows,keys):
 lengths=[];options=collections.Counter();keydist=collections.Counter();tf=collections.Counter();correct=[]
 for q in rows:
  part=q['part'];idx=q['idx'];key=keys.get((part,idx)) or {};alts=q.get('alternatives') or []
  if alts:
   lens={a['label']:len(re.findall(r'\S+',textonly(a['text']))) for a in alts} if q.get('option_texts_from_source') else {};ans=key.get(None);keydist[str(ans)]+=1
   if ans in lens:
    mx=max(lens.values());charlens={a['label']:len(textonly(a['text'])) for a in alts};cmx=max(charlens.values());lengths.append({'part':part,'idx':idx,'key':ans,'lengths_words':lens,'lengths_characters':charlens,'key_tied_longest_characters':charlens[ans]==cmx,'key_unique_longest_characters':charlens[ans]==cmx and list(charlens.values()).count(cmx)==1,'key_tied_longest':lens[ans]==mx,'key_unique_longest':lens[ans]==mx and list(lens.values()).count(mx)==1,'max_min_ratio':mx/min(lens.values()) if min(lens.values()) else None})
   for a in alts:
    if ans is None or a['label']==ans:continue
    options['wrong_total']+=1;v=a.get('identifiable_error') if q.get('solved_answer')==ans and q.get('confidence') in ['high','medium'] else None;options['identifiable' if v is True else 'not_identifiable' if v is False else 'unverified']+=1
    if a.get('extreme_words'):options['wrong_extreme']+=1
    if a.get('wording_eliminable'):options['wording_eliminable']+=1
   if ans is not None and any(a.get('extreme_words') for a in alts) and not any(a.get('extreme_words') and a['label']==ans for a in alts):options['mcq_extremes_only_wrong']+=1
  for st in q.get('statements') or []:tf[st.get('falsehood_kind','unverified')]+=1
  # Compare an independent answer to the published key only after the model answered.
  if q.get('solved_statements'):
   for sub,ans in q['solved_statements'].items():
    if key.get(sub) is not None:correct.append({'part':part,'idx':idx,'sub':sub,'published':key[sub],'independent':ans,'same_literal':str(ans).strip().upper()==str(key[sub]).strip().upper(),'confidence':q['confidence']})
  elif key.get(None) is not None and q.get('solved_answer') is not None:
   # Literal inequality in prose/numerical notation is only a review candidate, never automatically wrong.
   ans=q['solved_answer'];ref=key[None];is_letter=bool(re.fullmatch('[A-Z]',str(ref)))
   def number(s):
    try:return float(str(s).strip().replace(',','.'))
    except ValueError:return None
   a,b=number(ans),number(ref);equal=str(ans).strip().casefold()==str(ref).strip().casefold()
   if a is not None and b is not None:equal=math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-8)
   correct.append({'part':part,'idx':idx,'sub':None,'published':ref,'independent':ans,'same_literal':equal,'comparable':is_letter or (a is not None and b is not None),'confidence':q['confidence']})
 n=options['identifiable']+options['not_identifiable'];return {'mcq_length_metrics':lengths,'key_tied_longest':sum(x['key_tied_longest'] for x in lengths),'key_unique_longest':sum(x['key_unique_longest'] for x in lengths),'key_tied_longest_characters':sum(x['key_tied_longest_characters'] for x in lengths),'key_unique_longest_characters':sum(x['key_unique_longest_characters'] for x in lengths),'mcq_with_key_and_options':len(lengths),'wrong_options':dict(options),'identifiable_share_among_judged':options['identifiable']/n if n else None,'key_distribution':dict(keydist),'tf_falsehoods':dict(tf),'answer_comparisons':correct,'high_discrimination_count':sum(q.get('discrimination')=='high' for q in rows),'routine_count':sum(q.get('routine') is True for q in rows),'direct_recall_count':sum(q.get('direct_recall') is True for q in rows),'error_flag_count':sum(len(q.get('error_flags') or []) for q in rows),'unverified_count':sum(q.get('confidence') in ['low','unreadable'] for q in rows)}
def grading_profile(path):
 if not path.exists():return {'status':'no_subject_profile'}
 x=load(path);stats=x.get('code_derived',{});structure=x.get('paper_structure',{});high=stats.get('high_discrimination_rows',[])
 return {'subject':x.get('subject'),'status':x.get('status'),'extraction_model':x.get('extraction_model'),'evidence_counts':dict(collections.Counter(p['class'] for p in x.get('evidence',{}).get('papers',[]))),'profiles_by_class':x.get('profiles_by_class',{}),'grade_presence':stats.get('grade_presence',[]),'high_examples_by_class':{cls:[r for r in high if r['evidence_class']==cls][:8] for cls in ['official','provincial_third_party']},'structure_summary':{k:structure.get(k) for k in ['part_order_observations','shared_group_presence','limits']},'projection_note':'Profile evidence classes kept separate; full distributions and per-paper structure are compared in code outside this judgement prompt.'}

def process(item,mapping):
 source=evidence_path(item['path']);sid=hashlib.sha256(source.read_bytes()+(evidence_path(item['key']).read_bytes() if item.get('key') else b'')).hexdigest();subject=ALIASES.get(item['subject'],item['subject']);pid=mapping.setdefault(sid,'P'+secrets.token_hex(5));out=ROOT/'audit/outputs/prototype-grades'/f'{pid}.json'
 if out.exists():
  cached=load(out)
  for c in cached.get('metrics',{}).get('answer_comparisons',[]):
   c['same_answer']=ascii_fold(str(c['published'])).strip().upper()==ascii_fold(str(c['independent'])).strip().upper() if c.get('sub') is not None else c['same_literal']
  cached['comparison_note']='TF D and Đ compared using canonical file_matching.ascii_fold; same_literal retains original spelling comparison.'
  attach_quality(cached);dump(out,cached);return cached
 if source.suffix=='.pdf':full=run(['pdftotext','-layout',source,'-'])
 else:full=source.read_text(encoding='utf-8')
 keydata=load(item['key']) if item.get('key') else {}
 registered_labels=lambda part:option_labels_for(keydata.get('exam_type'),SUBJECT_IDS.get(subject,subject),part)
 packet=load(item['packet']) if item.get('packet') else None
 if packet:full=packet['paper_md']
 qs=[dict(q) for q in packet['questions']] if packet else questions(full)
 if item.get('key'):
  canonical=load(item['key']).get('questions',[]);by_part=collections.defaultdict(list)
  for k in canonical:by_part[k['part']].append(k['idx'])
  observed=collections.Counter(q['part'] for q in qs);positions=collections.Counter()
  for q in qs:
   part=q['part']
   if observed[part]==len(by_part[part]):
    q['printed_idx']=q['idx'];q['idx']=sorted(by_part[part])[positions[part]];positions[part]+=1
 # V-ACT parts are explicit LECTURING-PART labels; our generic reader accepts all part ids.
 if not qs:
  dump(ROOT/'audit/outputs/stops'/('prototype-'+pid+'.json'),{'reason':'No question headings parsed','source':str(source)});return None
 labelmatches=list(re.finditer(r'%\s*LECTURING-MATRIX:[^\n]*level=(\w+)',full));labels={}
 # Labels are located by per-question slice before stripping.
 rawms=list(re.finditer(r'\\textbf\{(?:Câu|Question)\s+\d+\s*[:.]',full))
 for i,q in enumerate(qs):
  if i<len(rawms):
   segment=full[rawms[i].start():rawms[i+1].start() if i+1<len(rawms) else len(full)];lab=re.search(r'LECTURING-MATRIX:[^\n]*level=(\w+)',segment)
   if lab:labels[(q['part'],q['idx'])]=lab[1]
 sanitized=re.sub(r'(?m)(?<!\\)%[^\n]*','',full);sanitized=re.sub(r'PROTO_[\w-]+','PAPER',sanitized);targets=[{'qid':f'q{i+1:03d}','part':q['part'],'idx':q['idx'],'text':q['text']} for i,q in enumerate(qs)]
 structure_file=ROOT/'audit/outputs/block-structure-audit.json';structural=load(structure_file) if structure_file.exists() else {};registered_structure=[r for r in structural.get('registry',[]) if r['format']==keydata.get('exam_type') and r['subject'] in (SUBJECT_IDS.get(subject,subject),'')];observed_structure=next(({k:r[k] for k in ['expected_part_order','observed_part_order','part_order_matches','parts']} for r in structural.get('prototype_probes',[]) if r['source']==item['path']),None)
 profile=ROOT/'profiles'/subject/'profile.compact.json';context=grading_profile(profile);rows=[];limits=[]
 for n in range(0,len(targets),20):
  ts=targets[n:n+20];want={q['qid'] for q in ts};chunk=out.with_name(pid+f'-chunk{n//20}.json')
  image_pages=sorted({p for i,q in enumerate(qs,1) if f'q{i:03d}' in want for p in q.get('figure_pages',[])}) if packet else []
  image_files=[packet['rendered_paper_pages'][int(p)-1] for p in image_pages if 1<=int(p)<=len(packet['rendered_paper_pages'])] if packet else []
  def judge():
   x=ask('prototype-'+pid+f'-chunk{n//20}',(ROOT/'audit/prompts/PROTOTYPE_GRADE.txt').read_text()+'\n'+json.dumps({'blind_code':pid,'profile':context,'registered_structure':registered_structure,'observed_structure':observed_structure,'structure_caution':'Canonical order differences alone do not prove a defect; language exam codes may permute blocks.','full_document':sanitized,'target_qids':ts,'attached_paper_page_numbers':image_pages},ensure_ascii=False),images=image_files,timeout=1000)
   if {r['qid'] for r in x['rows']}!=want or len(x['rows'])!=len(want):raise ValueError('PROTOTYPE_QID_MISMATCH')
   for r in x['rows']:
    q=next(t for t in ts if t['qid']==r['qid']);r['part']=q['part'];r['idx']=q['idx']
    letters=registered_labels(q['part'])
    if letters and r.get('confidence')!='unreadable' and {a['label'] for a in r.get('alternatives',[])}!=set(letters):raise ValueError('PROTOTYPE_ALTERNATIVE_LABELS')
   return x
  x=load(chunk) if chunk.exists() else twice('prototype-'+pid+f'-chunk{n//20}',judge)
  if x is None:return None
  dump(chunk,x);rows+=x['rows'];limits+=x.get('calibration_limits',[])
 keys={}
 if item.get('key'):
  kd=load(item['key'])
  for q in kd.get('questions',[]):keys[(q['part'],q['idx'])]={s.get('sub'):s['answer'] for s in q['slots']}
 for r in rows:
  alts=r.get('alternatives') or []
  if alts:
   q=next(q for q in qs if q['part']==r['part'] and q['idx']==r['idx']);letters=registered_labels(r['part']);original=source_options(q['text'],letters) if letters else None;r['option_texts_from_source']=original is not None
   if original:
    for a in alts:a['text']=original[a['label']]
 metrics=metric(rows,keys);metrics['VD_but_routine_count']=sum(labels.get((r['part'],r['idx']))=='VD' and r.get('routine') is True for r in rows)
 result={'blind_code':pid,'source_sha256':sid,'subject':subject,'model':MODEL,'rows':rows,'metrics':metrics,'calibration_limits':limits,'blind_limits':'Model did not see filename, level tags or key. Same model supplies profile and judges; not teacher validation. Original labels joined only after grading.'};attach_quality(result);dump(out,result);return result

def stage4(subjects=None):
 inv=load(ROOT/'audit/outputs/prototype-inventory.json');mp=ROOT/'audit/outputs/prototype-blind-mapping.json';mapping=load(mp) if mp.exists() else {};saved=ROOT/'audit/outputs/prototype-results.json';results=[x for x in load(saved) if x['output']['subject'] not in subjects] if subjects and saved.exists() else []
 for item in inv:
  if subjects and ALIASES.get(item['subject'],item['subject']) not in subjects:continue
  if not evidence_path(item['path']).exists():
   dump(ROOT/'audit/outputs/stops'/('prototype-source-'+hashlib.sha256(item['path'].encode()).hexdigest()[:12]+'.json'),{'reason':'Frozen prototype source is missing; not graded or reconstructed','path':item['path']});continue
  # Byte-identical corpus/product copies are graded once and reported at both paths.
  result=process(item,mapping);dump(mp,mapping)
  if result is not None:results.append({'input':item,'output':result});dump(ROOT/'audit/outputs/prototype-results.json',results)
 dump(ROOT/'audit/outputs/prototype-results.json',results)
 grouped=collections.defaultdict(list)
 for x in results:grouped[x['output']['subject']].append(x)
 ranking_path=ROOT/'audit/outputs/prototype-ranking.json';rank=[r for r in load(ranking_path) if r['subject'] not in subjects] if subjects and ranking_path.exists() else []
 for subject,items in grouped.items():
  if subjects and subject not in subjects:continue
  unique={x['output']['blind_code']:x for x in items};docs=['# Audit prototype '+subject,'','Chấm bởi model, chưa giáo viên duyệt. Đề do app sinh chỉ là đối tượng kiểm định, không là bằng chứng thật. Nhận định phân hoá không phải thống kê kết quả học sinh.','']
  for x in unique.values():
   r=x['output'];m=r['metrics'];bad=[c for c in m['answer_comparisons'] if not c['same_literal'] and not (c.get('sub') is not None and ascii_fold(str(c['published'])).strip().upper()==ascii_fold(str(c['independent'])).strip().upper()) and c.get('comparable',True) and c['confidence']=='high'];docs += ['## '+r['blind_code'],'',f'Nguồn: {x["input"]["path"]}', '',f'- Khóa dài nhất (kể hòa): {m["key_tied_longest"]}/{m["mcq_with_key_and_options"]}; dài nhất duy nhất: {m["key_unique_longest"]}.',f'- Nhiễu có lỗi xác định: {m["wrong_options"].get("identifiable",0)}/{m["wrong_options"].get("identifiable",0)+m["wrong_options"].get("not_identifiable",0)} phương án đã phán đoán; chưa kiểm: {m["wrong_options"].get("unverified",0)}.',f'- Phân hoá cao: {m["high_discrimination_count"]}; thường quy: {m["routine_count"]}; gắn VD nhưng thường quy: {m["VD_but_routine_count"]}.',f'- Bất đồng khóa tự giải cần giáo viên: {len(bad)}; cờ khoa học/lịch sử/mơ hồ: {m["error_flag_count"]}.','', '| Phần/câu | Chủ đề/lớp | Phân hoá | Nhiễu và nghi vấn |','|---|---|---|---|']
   for q in r['rows']:
    opts='; '.join(a['label']+': '+(a.get('mistake_kind') or 'không rõ lỗi') for a in q.get('alternatives',[]) if a.get('is_independent_key') is not True);flags='; '.join(re.sub(r'\d+(?:[.,/-]\d+)*','[chi tiết trong receipt]',e['reason']) for e in q.get('error_flags') or [])
    docs.append(f'| {q["part"]}/{q["idx"]} | {q["topic"]}; lớp {q.get("grade")} | {q["discrimination"]} | {opts}; {flags} |')
   quality=m.get('distractor_quality',{});docs+=['',f'Nhiễu liên hệ được lỗi và không bị đánh dấu tự lộ qua lời văn: {quality.get("qualified",0)}/{quality.get("judged",0)}; chưa kiểm {quality.get("unverified",0)}. Có {quality.get("linked_but_wording_eliminable",0)} phương án liên hệ được lỗi nhưng vẫn dễ loại qua lời văn. Đây là nhận định model, chưa phải lỗi phổ biến đo từ học sinh.','', 'Giới hạn: '+'; '.join(r.get('calibration_limits') or []),'']
   quality=m['distractor_quality'];denom=quality.get('judged',0);share=quality.get('qualified_share_among_judged');risk=len(bad)*100+m['error_flag_count']*10+(1-(share if share is not None else 0))*20+(m['key_unique_longest']/m['mcq_with_key_and_options']*10 if m['mcq_with_key_and_options'] else 0)
   rank.append({'subject':subject,'code':r['blind_code'],'risk_sort_score':risk,'key_disagreements_review':len(bad),'flags':m['error_flag_count'],'distractor_identifiable':quality.get('qualified',0),'distractor_judged':denom,'share':share,'high_count':m['high_discrimination_count'],'source':x['input']['path']})
  docs+=summarise(subject,items);p=ROOT/'audit/prototypes'/f'{subject}.md';p.parent.mkdir(exist_ok=True,parents=True);p.write_text('\n'.join(docs),encoding='utf-8')
 rank.sort(key=lambda x:-x['risk_sort_score']);dump(ROOT/'audit/outputs/prototype-ranking.json',rank);lines=['# Xếp thứ tự prototype cần rà trước','','Tỷ lệ nhiễu ở đây yêu cầu vừa liên hệ được lỗi vừa không tự lộ qua lời văn, theo model. Thứ tự ưu tiên nội bộ dựa trên cờ cần rà, bất đồng khóa và tỷ lệ nhiễu; không phải điểm chuẩn hoá giữa môn. Bất đồng tự giải của model chưa khẳng định khóa sai. Các bản sao byte giống chỉ chấm một lần.','','| Môn | Mã mù | Bất đồng khóa cần rà | Cờ | Nhiễu có lỗi, không tự lộ / đã xét | Phân hoá cao (ước lượng) |','|---|---|---:|---:|---:|---:|']
 for x in rank:lines.append(f'| {x["subject"]} | {x["code"]} | {x["key_disagreements_review"]} | {x["flags"]} | {x["distractor_identifiable"]}/{x["distractor_judged"]} | {x["high_count"]} |')
 (ROOT/'audit/prototypes/SUMMARY.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--subjects',nargs='*');args=ap.parse_args();stage4(args.subjects)

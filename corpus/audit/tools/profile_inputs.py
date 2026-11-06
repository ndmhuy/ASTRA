"""Freeze profile sources before model judgements; no subject-specific extraction rules."""
from common import *
from addresses import questions
import csv,collections

def audit_for(source):
 p=source.with_name('AUDIT-20261102.json')
 return load(p) if p.exists() else {}

def source_content_issues(source):
 from addresses import indexed_questions,canon,expected
 from stage3 import SUBJECT_IDS
 subject=source.relative_to(ROOT).parts[1];snap=ROOT/'audit/outputs/defaults-snapshot.json';stp=source.with_name('structure.json')
 if not snap.exists() or not stp.exists():return []
 st=load(stp);shape=load(snap)['subjects'].get(SUBJECT_IDS.get(subject,''),{});md=source.read_text(encoding='utf-8');addresses=expected(md,st.get('parts'));issues=[]
 for part in shape.get('parts',[]):
  if part['qtype']!='true_false':continue
  widths=part.get('slots_per_question',[]);unique=set(widths)
  for q in indexed_questions(md,st.get('parts')):
   if q['part']!=part['part_id']:continue
   width=next(iter(unique)) if len(unique)==1 else widths[q['idx']-1] if 0<q['idx']<=len(widths) else None
   actual=len({sub for p,i,sub in addresses if p==q['part'] and i==q['idx'] and sub is not None})
   if width is not None and actual!=width:issues.append({'part':q['part'],'idx':q['idx'],'printed_idx':q['printed_idx'],'expected_statement_count_from_registered_shape':width,'observed_statement_count':actual})
 return issues

def matched_key(source,ent):
 a=audit_for(source)
 if a.get('qa_key_failures'):return None,'unresolved_key_QA'
 p=source.with_name('key.json');key=load(p) if p.exists() else None
 if isinstance(key,dict):return key,'local_key'
 stp=source.with_name('structure.json');st=load(stp) if stp.exists() else {};code=st.get('ma_de') or st.get('code') or st.get('exam_code')
 year=str(ent.get('year') or '')
 p=source.parents[1]/(year+'-answer')/'key.json'
 if p.exists() and code:
  data=load(p)
  for field in ['ma_de','codes','answers','keys']:
   codes=data.get(field)
   if isinstance(codes,dict) and str(code) in codes:return codes[str(code)],'exact_year_code_external_key'
 return None,'no_confirmed_matching_key'

def source_images(source):
 # Use complete original paper pages when available: a crop's presence does not prove its bounds.
 a=audit_for(source);call=a.get('calls')
 # Reuse original official page images already in the corpus; no OCR/model call.
 parts=source.relative_to(ROOT).parts
 if len(parts)>=4 and re.fullmatch(r'20\d\d-paper',parts[2]):
  folder=ROOT/'official'/(parts[2][:4]+'-papers')/parts[1]
  originals=sorted(p for p in folder.glob('*') if p.suffix.lower() in ['.jpg','.jpeg','.png']) if folder.exists() else []
  if originals:return originals,'original_official_pages'
 if call:
  cp=Path(call);metas=sorted(cp.glob('attempt-*.meta.json'),key=lambda p:int(p.name.split('-')[1].split('.')[0]),reverse=True)
  for p in metas:
   m=load(p)
   if m.get('returncode')==0 and m.get('images') and all(Path(i).is_file() for i in m['images']):return [Path(i) for i in m['images']],'original_OCR_pages'
 md=source.read_text(encoding='utf-8');ps=[source.parent/x for x in re.findall(r'!\[[^]]*\]\(([^)]+)\)',md)]
 return [p for p in ps if p.is_file()],'transcription_crops_only_bounds_not_independently_verified'

def freeze():
 rows=list(csv.DictReader((ROOT/'registry/papers.csv').open(encoding='utf-8')))
 selected=[];excluded=[];seen={};fingerprints=[]
 for e in sorted(rows,key=lambda x:(x['subject'],x['class'],x['path'])):
  if e['usable_as_content_evidence'].lower()!='true' or e['class'] not in ['official','provincial_third_party'] or 'reference' in e['path']:continue
  source=ROOT/e['path'];md=source.read_text(encoding='utf-8');qs=questions(md)
  # Order-independent exact-content detection. Near duplicates remain a stated limitation.
  bodies=sorted(re.sub(r'\s+',' ',re.sub(r'!\[[^]]*\]\([^)]+\)','',q['text'])).strip() for q in qs)
  digest=hashlib.sha256(json.dumps(bodies,ensure_ascii=False).encode()).hexdigest()
  if bodies and (e['subject'],digest) in seen:
   excluded.append({'path':e['path'],'reason':'same_question_body_multiset','duplicate_of':seen[(e['subject'],digest)]});continue
  seen[(e['subject'],digest)]=e['path'];key,reason=matched_key(source,e)
  e={**e,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'question_body_multiset_sha256':digest,'has_confirmed_matching_key':key is not None,'key_status':reason}
  selected.append(e)
 # Owner explicitly caps the math study at twenty provincial papers. Choose by prior key QA then path, before EXTRACT.
 math=[e for e in selected if e['subject']=='toan' and e['class']=='provincial_third_party']
 keep={e['path'] for e in sorted(math,key=lambda e:(not e['has_confirmed_matching_key'],e['path']))[:20]}
 for e in list(selected):
  if e in math and e['path'] not in keep:selected.remove(e);excluded.append({'path':e['path'],'reason':'owner_twenty_math_cap; preanalysis_key_QA_then_lexical_path'})
 manifest={'selection_rule':'Registry content-eligible official/provincial only; exact body-multiset dedup; math provincial cap twenty, key-QA priority then path. No model outcomes used.','near_duplicate_detection_exhaustive':False,'selected':selected,'excluded':excluded}
 dump(ROOT/'audit/outputs/profile-inputs.json',manifest)
 return manifest
if __name__=='__main__':
 m=freeze();c=collections.Counter((e['subject'],e['class']) for e in m['selected'])
 for s in sorted({k[0] for k in c}):print(s,c[(s,'official')],c[(s,'provincial_third_party')])
 print('excluded',len(m['excluded']))

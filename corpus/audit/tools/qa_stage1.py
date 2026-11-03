from common import *
from addresses import *
import collections,argparse
results=[]
def normalized_key(value, allow_tf_ds=False):
 if isinstance(value,list):return [normalized_key(x,allow_tf_ds) for x in value]
 if isinstance(value,dict):return {k:normalized_key(v,allow_tf_ds) for k,v in value.items()}
 if isinstance(value,str):
  token=value.strip().casefold()
  if token=='đúng':return 'Đ'
  if token=='sai':return 'S'
  if allow_tf_ds and token in {'d','đ'}:return 'Đ'
 return value
def compare_printed_keys(first,second,parts,supplemental=None):
 mismatches=[];incomplete=[];format_normalizations=[]
 if second is None:
  second={}
 second={k:(list(v) if isinstance(v,list) else v) for k,v in second.items()} if isinstance(second,dict) else {}
 if isinstance(supplemental,dict):
  for name,values in supplemental.items():
   if not isinstance(values,list):continue
   current=second.setdefault(name,[])
   if not isinstance(current,list):current=[];second[name]=current
   while len(current)<len(values):current.append(None)
   part_index=int(name[4:])-1 if name.startswith('part') and name[4:].isdigit() else -1
   allow_tf_ds=0<=part_index<len(parts) and str(parts[part_index].get('type','')).casefold() in {'true_false','tf'}
   for j,value in enumerate(values):
    if value is not None:
     if current[j] is None:current[j]=value
     elif normalized_key(current[j],allow_tf_ds)!=normalized_key(value,allow_tf_ds):mismatches.append(f'{name}.{j+1} (verified reads differ)')
 if not second:incomplete.append('Không có khóa độc lập được chép từ ảnh')
 for i,part in enumerate(parts,1):
  name='part'+str(i);expected=int(part.get('count',0));allow_tf_ds=str(part.get('type','')).casefold() in {'true_false','tf'}
  left=first.get(name) if isinstance(first,dict) else None
  right=second.get(name) if isinstance(second,dict) else None
  if right is None:
   if expected:incomplete.append(f'{name}: lượt hai không thấy khóa in')
   continue
  if not isinstance(right,list):
   incomplete.append(f'{name}: khóa lượt hai không có dạng danh sách')
   continue
  if len(right)<expected:incomplete.append(f'{name}: lượt hai đọc được {len(right)}/{expected} câu')
  if not isinstance(left,list):
   if right:incomplete.append(f'{name}: lượt đầu không có dữ liệu để so với khóa in')
   continue
  for j,(a,b) in enumerate(zip(left,right),1):
   if a is None or b is None:incomplete.append(f'{name}.{j}: ô khóa chưa đọc được');continue
   na=normalized_key(a,allow_tf_ds);nb=normalized_key(b,allow_tf_ds)
   if na!=nb:mismatches.append(f'{name}.{j}')
   elif allow_tf_ds and a!=b and {str(a).strip().casefold(),str(b).strip().casefold()}=={'d','đ'}:format_normalizations.append({'cell':f'{name}.{j}','raw_first':a,'raw_second':b,'normalized':'Đ','basis':'D/S printed shorthand in true_false part; glyph retained in raw key provenance'})
 return mismatches,incomplete,format_normalizations

def qa_questions(text):
 return questions(text)
def verified_key_resolution(d,st,key,r,label):
 if not isinstance(r,dict):return None,label+' not recorded'
 code=str(st.get('ma_de') or '')
 if not code or str(r.get('exact_code') or '')!=code:return None,'exact_code does not match structure.ma_de'
 if not isinstance(r.get('key'),dict):return None,'resolution key missing'
 images=r.get('source_images')
 if not isinstance(images,list) or not images:return None,'source_images missing'
 verified=[]
 for item in images:
  if not isinstance(item,dict) or not item.get('path') or not item.get('sha256'):
   return None,'source image provenance incomplete'
  raw=Path(item['path']);candidates=[raw] if raw.is_absolute() else [ROOT/raw,d/raw]
  path=next((x for x in candidates if x.is_file()),None)
  if path is None:return None,'source image missing: '+str(item['path'])
  digest=hashlib.sha256(path.read_bytes()).hexdigest()
  if digest.lower()!=str(item['sha256']).lower():return None,'source image SHA256 mismatch: '+str(item['path'])
  verified.append({'path':str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),'sha256':digest})
 effective=r['key']
 if json.dumps(normalized_key(key),ensure_ascii=False,sort_keys=True)!=json.dumps(normalized_key(effective),ensure_ascii=False,sort_keys=True):
  return None,'key.json differs from image-reviewed source_key_resolution.key'
 return {'key':effective,'exact_code':code,'reviewer':r.get('reviewer'),'source_images':verified,'basis':label},None

def qa_paper(p):
 a=load(p);d=p.parent;st=load(d/'structure.json');md=(d/'de.md').read_text(encoding='utf-8');expected_questions=st.get('total_cau');qs=qa_questions(md);fail=[]
 if len(qs)!=expected_questions:fail.append('Số câu parser không khớp cấu trúc')
 if len({(q['part'],q['idx']) for q in qs})!=len(qs):fail.append('Địa chỉ câu trùng')
 refs=re.findall(r'!\[[^]]*\]\(([^)]+)\)',md)
 for r in refs:
  if not (d/r).is_file():fail.append('Thiếu crop '+r)
 if len(refs)!=st.get('figure_count'):fail.append('Số hình tham chiếu không khớp structure')
 content_failures=list(fail)
 key=load(d/'key.json') if (d/'key.json').exists() else None
 if key is None and a['input']['kind']=='paper':
  kp=ROOT/'transcriptions'/a['input']['subject']/(str(a['input']['year'])+'-answer')/'key.json';code=st.get('ma_de')
  if kp.exists() and code:
   kd=load(kp);matched=(kd.get('ma_de') or {}).get(str(code))
   if matched:
    key=matched;dump(d/'key.json',key);a['matched_key_source']={'path':str(kp),'exact_code':str(code),'note':'Existing official answer table; not solved or inferred.'}
 if key:
  for i,part in enumerate(st['parts'],1):
   k='part'+str(i)
   if len(key.get(k,[]))!=part['count']:fail.append('Khóa '+k+' lệch số câu')
  independent=a['verification'].get('independent_key')
  supplemental=a.get('supplemental_visual_key_review',{}).get('key')
  audit=load(d/'AUDIT-20261102.json')
  sr=audit.get('source_key_resolution')
  vr=audit.get('supplemental_visual_key_review')
  resolution,resolution_error=verified_key_resolution(d,st,key,sr,'source_key_resolution') if sr else verified_key_resolution(d,st,key,vr,'supplemental_visual_key_review')
  imported=a.get('matched_key_source') or {};imported_valid=False
  if imported.get('path') and str(imported.get('exact_code'))==str(st.get('ma_de')):
   ip=Path(imported['path']);expected_ip=ROOT/'transcriptions'/a['input']['subject']/(str(a['input']['year'])+'-answer')/'key.json'
   if ip.resolve()==expected_ip.resolve() and ip.is_file():
    imported_key=(load(ip).get('ma_de') or {}).get(str(st.get('ma_de')))
    imported_valid=imported_key==key
  if imported_valid:
   a['key_coverage']={'mismatches':[],'incomplete':[],'basis':'exact year/code join to existing official-answer transcription','source':imported,'new_independent_key_read':False}
  elif resolution:
   hist_mismatches,hist_incomplete,hist_normalizations=compare_printed_keys(key,independent,st.get('parts',[]),supplemental)
   a['key_coverage']={'mismatches':[],'incomplete':[],'historical_independent_mismatches':hist_mismatches,'historical_independent_incomplete':hist_incomplete,'format_normalizations':hist_normalizations,'verified_visual_key_resolution':resolution,'supplemental_visual_pages':a.get('supplemental_visual_key_review',{}).get('pages',[])}
  else:
   mismatches,incomplete,format_normalizations=compare_printed_keys(key,independent,st.get('parts',[]),supplemental)
   a['key_coverage']={'mismatches':mismatches,'incomplete':incomplete,'source_resolution_error':resolution_error,'format_normalizations':format_normalizations,'supplemental_visual_pages':a.get('supplemental_visual_key_review',{}).get('pages',[])}
   if mismatches:fail.append('Khóa hai lượt khác nhau tại '+', '.join(mismatches)+'; cần xem lại ảnh, không tự chọn khóa')
   if incomplete:fail.append('Khóa in chưa đủ để xác nhận toàn bộ bài: '+'; '.join(incomplete))
 else:fail.append('Không có khóa khớp mã được xác nhận')
 # Do not present intentionally omitted solutions as missing exam pages.
 a['qa_failures']=fail;a['qa_content_failures']=content_failures;a['qa_key_failures']=fail[len(content_failures):];dump(p,a)
 status_path=d/'STATUS.md';status=status_path.read_text(encoding='utf-8');marker='\n## QA STOPPED / incomplete\n'
 if marker in status:status=status.split(marker,1)[0].rstrip()+'\n'
 if fail:status+='\n## QA STOPPED / incomplete\n'+'\n'.join('- '+x for x in fail)+'\n'
 status_path.write_text(status,encoding='utf-8')
 results.append({'path':str(d.relative_to(ROOT)),'question_count':len(qs),'figure_refs':len(refs),'has_key':key is not None,'key_second_pass_structured':a['verification'].get('independent_key') is not None,'verification_pass':a['verification'].get('pass'),'failures':fail,'content_failures':content_failures,'key_failures':fail[len(content_failures):],'initial_failures':a.get('failures',[])})

def main(subjects=None):
 papers=sorted((ROOT/'transcriptions').glob('*/*/*/AUDIT-20261102.json'))+sorted((ROOT/'transcriptions').glob('*/*/AUDIT-20261102.json'))
 if subjects is not None:papers=[p for p in papers if any(p.is_relative_to(ROOT/'transcriptions'/subject/'2026-provincial') for subject in subjects)]
 results.clear()
 for p in papers:qa_paper(p)
 out=ROOT/'audit/outputs/stage1-qa.json'
 if subjects is not None and out.exists():
  old=load(out);paths={x['path'] for x in results};results[:]=[x for x in old if x.get('path') not in paths]+results
 dump(out,results);print('QA papers',len(papers),'failures',sum(bool(x['failures']) for x in results if subjects is None or any(x.get('path','').startswith(f'transcriptions/{s}/2026-provincial/') for s in subjects)))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--subjects',nargs='+');main(parser.parse_args().subjects)

"""Coverage by frozen prototype paper+key identity; aliases never inflate completion."""
from common import *
from stage3 import ALIASES
import collections

def coverage():
 inv=load(ROOT/'audit/outputs/prototype-inventory.json');mp=ROOT/'audit/outputs/prototype-blind-mapping.json';mapping=load(mp) if mp.exists() else {};records=[]
 for item in inv:
  source=evidence_path(item['path']);keypath=Path(item['key']) if item.get('key') else None
  if keypath and not keypath.is_absolute():keypath=ROOT/keypath
  try:
   raw=source.read_bytes();key=evidence_path(keypath).read_bytes() if keypath else b''
  except FileNotFoundError:
   records.append({'subject':ALIASES.get(item['subject'],item['subject']),'source':item['path'],'status':'missing_frozen_source_or_key'});continue
  identity=hashlib.sha256(raw+key).hexdigest();code=mapping.get(identity);gradefile=ROOT/'audit/outputs/prototype-grades'/f'{code}.json' if code else None;record={'subject':ALIASES.get(item['subject'],item['subject']),'source':item['path'],'identity':identity,'blind_code':code,'status':'not_graded'}
  if gradefile and gradefile.exists():
   grade=load(gradefile);kd=load(keypath) if keypath else {};expected={(q['part'],q['idx']) for q in kd.get('questions',[])};found={(q['part'],q['idx']) for q in grade['rows']};ok=grade['source_sha256']==identity and (not expected or (found==expected and len(grade['rows'])==len(expected)));record.update({'status':'graded_pending_teacher_review' if ok else 'grade_coverage_hold','questions':len(grade['rows'])})
  elif code and list((ROOT/'audit/outputs/prototype-grades').glob(code+'-chunk*.json')):record['status']='partial_chunks_saved'
  records.append(record)
 by=collections.defaultdict(dict)
 for r in records:by[r['subject']][r.get('identity',r['source'])]=r
 summary=[{'subject':s,'expected_unique':len(v),'graded_unique':sum(r['status']=='graded_pending_teacher_review' for r in v.values()),'remaining_unique':sum(r['status']!='graded_pending_teacher_review' for r in v.values())} for s,v in sorted(by.items())]
 result={'path_count':len(records),'unique_count':sum(r['expected_unique'] for r in summary),'graded_unique':sum(r['graded_unique'] for r in summary),'all_grades_teacher_pending':True,'subjects':summary,'paths':records};dump(ROOT/'audit/outputs/prototype-coverage.json',result);return result
if __name__=='__main__':
 x=coverage();print('prototype coverage',x['graded_unique'],'/',x['unique_count'],'unique papers at',x['path_count'],'paths')

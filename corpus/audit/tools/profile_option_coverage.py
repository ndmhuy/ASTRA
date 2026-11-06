"""MCQ label coverage against matched corpus keys; no model or content judgement."""
from common import *
from profile_inputs import matched_key
from stage3 import SUBJECT_IDS

def check(subject):
 manifest=load(ROOT/'audit/outputs/profile-inputs.json')['selected'];shapes=load(ROOT/'audit/outputs/registry-option-labels.json');result={'subject':subject,'matched_key_mcq_rows':0,'unknown_key_mcq_rows':0,'issues':[]}
 for file in sorted((ROOT/'profiles'/subject/'rows').glob('*.json')):
  data=load(file);source=data['source']['path'];entry=next(e for e in manifest if e['path']==source);key,reason=matched_key(ROOT/source,entry)
  for row in data['rows']:
   if row.get('sub') is not None:continue
   shape=next((s for s in shapes if s['format']=='THPTQG' and s['subject']==SUBJECT_IDS[subject] and s['part']==row['part']),None)
   labels=shape['option_labels'] if shape else []
   if not labels:continue
   if key is None:result['unknown_key_mcq_rows']+=1;continue
   seq=key.get('part'+re.search(r'\d+',row['part'])[0],[]);idx=int(row['idx'])-1;answer=seq[idx] if 0<=idx<len(seq) else None
   if answer not in labels:result['issues'].append({'paper':source,'part':row['part'],'idx':row['idx'],'kind':'key_not_in_labels'});continue
   result['matched_key_mcq_rows']+=1;want=set(labels)-{answer};got=[d.get('label') for d in row.get('wrong_option_details',[])]
   if set(got)!=want or len(got)!=len(want):result['issues'].append({'paper':source,'part':row['part'],'idx':row['idx'],'missing':sorted(want-set(got)),'unexpected':sorted(set(got)-want),'expected_count':len(want),'observed_count':len(got)})
 return result

if __name__=='__main__':
 import sys
 subjects=sys.argv[1:] or sorted({p.name for p in (ROOT/'profiles').iterdir() if (p/'rows').is_dir()})
 results=[check(s) for s in subjects];dump(ROOT/'audit/outputs/distractor-label-coverage.json',{'scope':'MCQ labels only, confirmed matching keys; no content judgement or TF validation','results':results})
 for r in results:print(r['subject'],'checked',r['matched_key_mcq_rows'],'unknown-key',r['unknown_key_mcq_rows'],'issues',len(r['issues']))

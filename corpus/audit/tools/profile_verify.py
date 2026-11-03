"""Verify profile references and each narrative leaf; metadata is not source narrative."""
from common import *
from addresses import expected
META={'refs','ref','paper_ids','source','papers','paper_id','part','idx','sub','grade','steps','typical_steps','year','label','row_count','paper_count','parts_in_order','order','stimulus_id','id','model','origin','source_sha256','issues'}
def narrative_leaves(value,path=()):
 if isinstance(value,dict):
  for key,child in value.items():
   if key not in META and not key.endswith('_refs') and not key.endswith('_sha256'):yield from narrative_leaves(child,path+(key,))
 elif isinstance(value,list):
  for i,child in enumerate(value):yield from narrative_leaves(child,path+(str(i),))
 elif isinstance(value,str):yield '.'.join(path),value

def invalid_refs(value,known,path=()):
 bad=[]
 if isinstance(value,dict):
  for key,child in value.items():
   if key=='refs' or key.endswith('_refs'):
    if not isinstance(child,list):bad.append({'path':'.'.join(path+(key,)),'reason':'refs_not_list'})
    else:
     for ref in child:
      if ref not in known:bad.append({'path':'.'.join(path+(key,)),'ref':ref})
   else:bad+=invalid_refs(child,known,path+(key,))
 elif isinstance(value,list):
  for i,child in enumerate(value):bad+=invalid_refs(child,known,path+(str(i),))
 return bad

def grams(text):
 words=re.findall(r'\w+',text.lower());return {' '.join(words[i:i+10]) for i in range(len(words)-9)}

def verify(subject):
 d=ROOT/'profiles'/subject;data=load(d/'rows.json');p=d/'profile.compact.json';profile=load(p) if p.exists() else {};combined=profile.get('profiles_by_class',{});known={r['ref'] for r in data['rows']};private=set()
 for paper in data['papers']:private|=grams((ROOT/paper['path']).read_text(encoding='utf-8'))
 overlaps=[];numeric=[];bad=[]
 for cls,value in combined.items():bad+=invalid_refs(value,{r['ref'] for r in data['rows'] if r['evidence_class']==cls})
 for section,value in [('aggregate',combined),('rows',data['rows']),('paper_structure',profile.get('paper_structure',{}))]:
  for loc,text in narrative_leaves(value):
   common=private&grams(text)
   if common:overlaps.append({'section':section,'location':loc,'count':len(common),'text_sha256':hashlib.sha256(text.encode()).hexdigest()})
   if re.search(r'\d',re.sub(r'\bP\d+\b','',text)):numeric.append({'section':section,'location':loc,'text':text})
 coverage=[]
 for paper in data['papers']:
  source=ROOT/paper['path'];st=load(source.with_name('structure.json')) if source.with_name('structure.json').exists() else {};want=expected(source.read_text(encoding='utf-8'),st.get('parts'));pid=hashlib.sha256(paper['path'].encode()).hexdigest()[:12];got={(r['part'],int(r['idx']),r.get('sub')) for r in data['rows'] if r['paper_id']==pid}
  if got!=want:coverage.append({'path':paper['path'],'missing':sorted(want-got,key=str),'extra':sorted(got-want,key=str)})
 data_sources=sorted((p['path'],p.get('source_sha256')) for p in data['papers']);profile_sources=sorted((p['path'],p.get('source_sha256')) for p in profile.get('evidence',{}).get('papers',[]));source_hash_mismatches=[p['path'] for p in data['papers'] if p.get('source_sha256') and hashlib.sha256((ROOT/p['path']).read_bytes()).hexdigest()!=p['source_sha256']]
 result={'source_hash_mismatches':source_hash_mismatches,'aggregate_input_current':data_sources==profile_sources and not source_hash_mismatches,'address_coverage_incomplete':bool(coverage),'address_coverage_issues':coverage,'refs_invalid':bad,'ten_word_overlap_count':sum(x['count'] for x in overlaps),'overlap_locations':overlaps,'numeric_narrative_candidates':numeric,'no_reference_inputs':all('reference' not in p['path'] for p in data['papers']),'model':data.get('model') or data.get('extraction_model'),'semantic_noncopying_proved':False,'scanner':'per-narrative-leaf v2; metadata year/ref and all *_refs excluded; both easy_refs/hard_refs validated','aggregate_classes_complete':set(combined)=={p['class'] for p in data['papers']} and bool(data['papers'])}
 from profile_option_coverage import check
 option_coverage=check(subject);result['wrong_option_label_coverage']=option_coverage;result['wrong_option_coverage_issues']=option_coverage['issues']
 dump(d/'verification.json',result)
 return result
if __name__=='__main__':
 import sys
 for s in sys.argv[1:]:
  v=verify(s);print(s,'refs_invalid',len(v['refs_invalid']),'overlap_ngrams',v['ten_word_overlap_count'],'numeric_leaves',len(v['numeric_narrative_candidates']),'aggregate_complete',v['aggregate_classes_complete'])

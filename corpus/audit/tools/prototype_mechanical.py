"""Preflight source-derived option lengths only. No model call or quality verdict."""
from common import *
from addresses import questions
from registry_shape import option_labels_for
from option_measure import source_options
from stage3 import SUBJECT_IDS,ALIASES
from stage4 import metric
import collections

def main():
 inv=load(ROOT/'audit/outputs/prototype-inventory.json');results=[];seen={}
 for item in inv:
  source=evidence_path(item['path']);kd=load(item['key']) if item.get('key') else {};sid=hashlib.sha256(source.read_bytes()+(evidence_path(item['key']).read_bytes() if item.get('key') else b'')).hexdigest();subject=ALIASES.get(item['subject'],item['subject'])
  if sid in seen:results.append({'source':str(source),'duplicate_of':seen[sid],'subject':subject});continue
  seen[sid]=str(source);packet=load(item['packet']) if item.get('packet') else None;qs=[dict(q) for q in packet['questions']] if packet else questions(source.read_text(encoding='utf-8'));by_part=collections.defaultdict(list);keys={}
  for q in kd.get('questions',[]):by_part[q['part']].append(q['idx']);keys[(q['part'],q['idx'])]={s.get('sub'):s['answer'] for s in q['slots']}
  counts=collections.Counter(q['part'] for q in qs);position=collections.Counter();rows=[];unparsed=[];mcq=0
  for q in qs:
   part=q['part'];idx=q['idx']
   if counts[part]==len(by_part[part]):idx=sorted(by_part[part])[position[part]];position[part]+=1
   labels=option_labels_for(kd.get('exam_type'),SUBJECT_IDS.get(subject,subject),part)
   if not labels:continue
   mcq+=1;opts=source_options(q['text'],labels)
   if opts is None:unparsed.append({'part':part,'idx':idx,'reason':'Source option layout not parsed; no model text substituted'});continue
   rows.append({'part':part,'idx':idx,'alternatives':[{'label':a,'text':t} for a,t in opts.items()],'option_texts_from_source':True,'confidence':'unreadable'})
  m=metric(rows,keys);results.append({'source':str(source),'subject':subject,'paper_and_key_sha256':sid,'inventory_source_hash_matches':hashlib.sha256(source.read_bytes()).hexdigest()==item.get('sha256'),'mcq_expected_from_shape':mcq,'unparsed':unparsed,**{k:m[k] for k in ['mcq_length_metrics','mcq_with_key_and_options','key_tied_longest','key_unique_longest','key_tied_longest_characters','key_unique_longest_characters','key_distribution']}})
 dump(ROOT/'audit/outputs/prototype-mechanical.json',{'status':'mechanical_preflight_only_not_quality_audit','model_calls':0,'measurement':'Whitespace words and Unicode characters after removing TeX layout; not visual line width. Ties and unique maxima reported separately.','unassessed':['correctness','misconception plausibility','extreme wording','discrimination','recall','coverage'],'papers':results})
 for x in results:
  if 'duplicate_of' in x:continue
  print(x['subject'],Path(x['source']).name,'parsed',x['mcq_with_key_and_options'],'/',x['mcq_expected_from_shape'],'key_tied_longest_words',x['key_tied_longest'],'unique',x['key_unique_longest'],'unparsed',len(x['unparsed']))
if __name__=='__main__':main()

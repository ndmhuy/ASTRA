"""Observe paper-level grouping/order, reusing inline EXTRACT results whenever present."""
from common import *
from addresses import indexed_questions
from profile_inputs import source_images
import collections,argparse

def validate(structure,source):
 st=load(source.with_name('structure.json'));qs=indexed_questions(source.read_text(encoding='utf-8'),st.get('parts'));known={(q['part'],q['idx']) for q in qs};order=list(dict.fromkeys(q['part'] for q in qs))
 for field in ['parts_in_order','blocks_in_order','shared_stimuli','optional_paths','limits']:
  if not isinstance(structure.get(field),list):raise ValueError('STRUCTURE_FIELD '+field)
 if structure['parts_in_order']!=order:raise ValueError('STRUCTURE_PART_ORDER')
 ids=[]
 for group in structure['shared_stimuli']:
  ids.append(group['id']);members=[(m['part'],int(m['idx'])) for m in group['members']]
  if not members or len(set(members))!=len(members) or not set(members)<=known:raise ValueError('STRUCTURE_GROUP_ADDRESS')
  if group['scope'] not in ['cross_parts','multiple_questions','statements_within_question'] or group['support'] not in ['explicit_instruction','layout_observation','uncertain']:raise ValueError('STRUCTURE_SCOPE_OR_SUPPORT')
  if group['scope']=='cross_parts' and len({p for p,i in members})<2:raise ValueError('STRUCTURE_CROSS_PART')
  if group['scope']=='multiple_questions' and len(members)<2:raise ValueError('STRUCTURE_SINGLE_IS_NOT_CLUSTER')
  if group['scope']=='statements_within_question' and len(members)!=1:raise ValueError('STRUCTURE_INTERNAL_STATEMENTS')
 if len(ids)!=len(set(ids)):raise ValueError('STRUCTURE_DUPLICATE_ID')
 for block in structure['blocks_in_order']:
  if not block['question_indices'] or not {(block['part'],int(i)) for i in block['question_indices']}<=known:raise ValueError('STRUCTURE_BLOCK_ADDRESS')
  if block['shares_content'] is not None and type(block['shares_content']) is not bool:raise ValueError('STRUCTURE_SHARED_BOOL')
  if block.get('stimulus_id') and block['stimulus_id'] not in ids:raise ValueError('STRUCTURE_STIMULUS_UNKNOWN')
 flattened=[(b['part'],int(i)) for b in structure['blocks_in_order'] for i in b['question_indices']]
 if flattened!=[(q['part'],q['idx']) for q in qs]:raise ValueError('STRUCTURE_BLOCK_COVERAGE_OR_ORDER')
 for path in structure['optional_paths']:
  if not {(m['part'],int(m['idx'])) for m in path['members']}<=known:raise ValueError('STRUCTURE_OPTIONAL_ADDRESS')
 return structure

def collect(subject,entries,completed_only=False,allow_model=True):
 d=ROOT/'profiles'/subject;observations=[];issues=[]
 for ent in entries:
  source=ROOT/ent['path'];pid=hashlib.sha256(ent['path'].encode()).hexdigest()[:12];cache=d/'rows'/(pid+'.json');out=d/'structures'/(pid+'.json');source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
  if ent.get('source_sha256') and source_sha!=ent['source_sha256']:issues.append({'source':ent['path'],'reason':'frozen source changed; no model call'});continue
  if completed_only and not cache.exists():continue
  if out.exists() and load(out)['source_sha256']==source_sha:
   cached=load(out)
   try:validate(cached['structure'],source)
   except (ValueError,KeyError,TypeError):pass
   else:observations.append(cached);continue
  x=load(cache) if cache.exists() else {};inline=x.get('paper_structure');origin='inline_EXTRACT';st=load(source.with_name('structure.json'))
  if inline is not None:
   try:structure=validate(inline,source)
   except (ValueError,KeyError,TypeError):inline=None
  if inline is None and not allow_model:issues.append({'source':ent['path'],'reason':'Structure supplement pending; topic profiling retains priority'});continue
  if inline is None:
   stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
   if stop.exists() and load(stop).get('active',True):issues.append({'source':ent['path'],'reason':'model prerequisite stopped'});break
   mapping=[{k:q[k] for k in ['part','idx','printed_idx']} for q in indexed_questions(source.read_text(encoding='utf-8'),st.get('parts'))];images,image_status=source_images(source);origin='structure_only_supplement_no_reOCR';tag='paper-structure-'+subject+'-'+pid
   def call():
    answer=ask(tag,(ROOT/'audit/prompts/PAPER_STRUCTURE.txt').read_text(encoding='utf-8')+'\nQUESTION_ADDRESS_MAP:\n'+json.dumps(mapping)+'\nPAPER:\n'+source.read_text(encoding='utf-8'),images=images,timeout=900)
    return validate(answer['paper_structure'],source)
   structure=twice(tag,call)
   if structure is None:issues.append({'source':ent['path'],'reason':'structure extraction failed twice'});continue
  record={'paper_id':pid,'source':ent['path'],'source_sha256':source_sha,'class':ent['class'],'year':ent['year'],'model':MODEL,'origin':origin,'structure':structure};dump(out,record);observations.append(record)
  print('STRUCTURE',subject,pid,len(structure['shared_stimuli']),flush=True)
 orders=collections.defaultdict(set);groups=collections.defaultdict(set)
 for paper in observations:
  cls=paper['class'];pid=paper['paper_id'];s=paper['structure'];orders[(cls,tuple(s['parts_in_order']))].add(pid)
  for g in s['shared_stimuli']:
   for part in {m['part'] for m in g['members']}:
    size=len({m['idx'] for m in g['members'] if m['part']==part});groups[(cls,part,g['kind'],g['scope'],size)].add(pid)
 result={'model':MODEL,'observations':observations,'issues':issues,'part_order_observations':[{'class':k[0],'order':k[1],'distinct_papers':len(v)} for k,v in sorted(orders.items())],'shared_group_presence':[{'class':k[0],'part':k[1],'kind':k[2],'scope':k[3],'questions_in_part':k[4],'distinct_papers':len(v)} for k,v in sorted(groups.items())],'limits':['Observed order is not proof of universal fixed order.','Multiple codes of the same paper are not independent papers.','Internal TF statements are not multi-question clusters.','Structure observations and topic-profile completion counts may differ; see per-paper provenance.']}
 dump(d/'paper-structures.json',result)
 compact=d/'profile.compact.json'
 if compact.exists():
  p=load(compact);p['paper_structure']=result;dump(compact,p)
 return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--subjects',nargs='*');ap.add_argument('--completed-only',action='store_true');args=ap.parse_args();entries=load(ROOT/'audit/outputs/profile-inputs.json')['selected'];subjects=args.subjects or sorted({e['subject'] for e in entries})
 for subject in subjects:
  with (ROOT/'audit/work'/('profile-subject-'+subject+'.lock')).open('a',encoding='utf-8') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   collect(subject,[e for e in entries if e['subject']==subject],args.completed_only)

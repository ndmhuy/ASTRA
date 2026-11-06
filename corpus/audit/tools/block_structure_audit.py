"""Read-only registry/real-artifact probes for part order, block order and shared text."""
from common import *
from registry_shape import all_shapes,PROD
from addresses import questions
from stage3 import SUBJECT_IDS,ALIASES
import importlib,collections

def main():
 formats,resolver=all_shapes();blocks=importlib.import_module('exam_formats.blocks');layoutmod=importlib.import_module('exam_formats.layout');registered=[]
 for fid,subjects in formats.items():
  for sid,parts in subjects.items():
   for pid in parts:
    specs=blocks.blocks_for(fid,sid or None,pid);rule=blocks.block_shape_rule(fid,sid or None,pid)
    registered.append({'format':fid,'subject':sid,'part':pid,'blocks':blocks.block_list(fid,sid or None,pid),'canonical_order':[{'kind':b.kind,'count':b.count} for b in specs],'random_position_rule':rule})
 cross=[]
 for fid,layouts in resolver._LAYOUTS_BY_FORMAT.items():
  for sid,layout in layouts.items():
   for stimulus in layout.stimuli:
    members=[{'part':p.part_id,'idx':idx} for p in layout.parts for idx,q in enumerate(p.questions(),1) if q.stimulus==stimulus.stimulus_id]
    cross.append({'format':fid,'subject':sid,'stimulus_id':stimulus.stimulus_id,'parts':layout.parts_using(stimulus.stimulus_id),'members':members})
 outputs=[];seen=set()
 for item in load(ROOT/'audit/outputs/prototype-inventory.json'):
  source=Path(item['path'])
  if source.suffix!='.tex':continue
  digest=hashlib.sha256(source.read_bytes()).hexdigest()
  if digest in seen:continue
  seen.add(digest);text=source.read_text(encoding='utf-8');kd=load(item['key']);fid=kd['exam_type'];subject=ALIASES.get(item['subject'],item['subject']);sid=SUBJECT_IDS.get(subject,subject);parts=formats.get(fid,{}).get(sid) or formats.get(fid,{}).get('') or {};qs=questions(text);observed_order=list(dict.fromkeys(q['part'] for q in qs));partmarkers=list(re.finditer(r'(?m)^\s*%\s*LECTURING-PART:\s*(\w+)',text));actual=collections.defaultdict(list)
  for b in blocks.find_blocks(text):
   prior=[m for m in partmarkers if m.start()<b['start']];pid=prior[-1][1] if prior else next(iter(parts)) if len(parts)==1 else None
   if pid:actual[pid].append({'kind':b['kind'],'count':len(b['numbers']),'printed_numbers':b['numbers'],'stimulus_present':bool(b['stimulus'])})
  comparison=[]
  for pid in parts:
   specs=blocks.blocks_for(fid,sid,pid);want=[(b.kind,b.count) for b in specs];got=[(b['kind'],b['count']) for b in actual[pid]];rule=blocks.block_shape_rule(fid,sid,pid);explicit=[]
   # Explicit Vietnamese span headers reveal clusters even without LECTURING-BLOCK markers.
   for m in re.finditer(r'(?:trả\s+lời|trả\s+lời\s+các)\s+câu\s+(\d+)\s+(?:đến|[–-])\s+(?:câu\s+)?(\d+)',text,re.I):
    prior=[h for h in partmarkers if h.start()<m.start()];part=prior[-1][1] if prior else next(iter(parts)) if len(parts)==1 else None
    if part==pid:explicit.append({'first_printed':int(m[1]),'last_printed':int(m[2]),'count':int(m[2])-int(m[1])+1})
   comparison.append({'part':pid,'registry_blocks':want,'observed_blocks':actual[pid],'exact_canonical_order':got==want if want else None,'same_block_multiset':collections.Counter(got)==collections.Counter(want) if want else None,'random_position_rule':rule,'explicit_shared_spans':explicit,'explicit_shape_accepted':blocks.block_shape_accepts(fid,sid,pid,[g['count'] for g in explicit]) if rule and explicit else None})
  outputs.append({'source':str(source),'source_sha256':digest,'format':fid,'subject':subject,'expected_part_order':list(parts),'observed_part_order':observed_order,'part_order_matches':observed_order==list(parts),'parts':comparison})
 result={'scope':'Static code plus pure registry/artifact probes; no product model run or UI acceptance','product_revision':run(['git','rev-parse','HEAD'],cwd=PROD.parent).strip(),'registry':registered,'cross_part_stimuli':cross,'prototype_probes':outputs,'cautions':['Canonical order differs from universal fixed order: registered language comments explicitly document code permutations.','No block marker is not proof of absent grouping; explicit shared-span headers are also inspected.','A structural slot/options gate does not by itself verify block order, stimulus availability or dependency.']};dump(ROOT/'audit/outputs/block-structure-audit.json',result)
 for p in outputs:
  for part in p['parts']:
   if part['registry_blocks'] or part['random_position_rule']:print(p['subject'],part['part'],'canonical',part['exact_canonical_order'],'multiset',part['same_block_multiset'],'span_sizes',[x['count'] for x in part['explicit_shared_spans']],'shape_ok',part['explicit_shape_accepted'])
if __name__=='__main__':main()

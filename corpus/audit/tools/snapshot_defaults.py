"""Read pure product data modules without importing the app registry or writing there."""
from common import *
import sys,types,importlib,collections,ast
prod=product_root()
sys.path.insert(0,str(prod))
parser_data=types.ModuleType('parsers')
for node in ast.parse((prod/'parsers.py').read_text(encoding='utf-8')).body:
 if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id=='LADDER_BY_CORRECT':parser_data.LADDER_BY_CORRECT=ast.literal_eval(node.value)
sys.modules['parsers']=parser_data
pkg=types.ModuleType('exam_formats');pkg.__path__=[str(prod/'exam_formats')];sys.modules['exam_formats']=pkg
layoutmod=importlib.import_module('exam_formats.thptqg_2026');blockmod=importlib.import_module('exam_formats.blocks');resolver=importlib.import_module('exam_formats.resolver');format_id=next(fid for fid,layouts in resolver._LAYOUTS_BY_FORMAT.items() if layouts is layoutmod.LAYOUTS);dm=importlib.import_module('exam_formats.default_matrices')
items={}
for sid,layout in layoutmod.LAYOUTS.items():
 parts=[];rows=[]
 for part in layout.parts:
  qs=part.questions();qtype=qs[0].qtype.value;n=len(qs);topics=dm.THPTQG_PART_TOPICS.get((sid,part.part_id)) or dm.THPTQG_TOPICS.get(sid)
  if not topics:continue
  parts.append({'part_id':part.part_id,'qtype':qtype,'count':n,'slots_per_question':[len(q.slots) for q in qs],'stimulus_ids':list(dict.fromkeys(q.stimulus for q in qs if q.stimulus)),'topics':topics,'block_rule':blockmod.block_shape_rule(format_id,sid,part.part_id),'blocks':[{'kind':b.kind,'count':b.count,'titled':b.titled,'inferred':b.inferred,'shares_content':blockmod.block_list(format_id,sid,part.part_id)[i]['shares_content']} for i,b in enumerate(part.blocks)]})
 shares=dm.fixed_splits([(p['part_id'],p['qtype'],p['count'],p['slots_per_question'][0]) for p in parts])
 for p in parts:
  split=None if p['qtype']=='true_false' else shares.get(p['part_id'])
  rows+=dm._rows_for_part(p['part_id'],p['qtype'],p['count'],p['topics'],balanced=False,official=split)
 counts=collections.Counter()
 for row in rows:counts[(row['part_id'],row['topic'])]+=row.get('count') or 0
 label=layout.question_label or blockmod.label_for('vi')
 items[sid]={'question_label':{'word':label.word,'end':label.end,'space':label.space,'example':label.render(1)},'display_name':layout.display_name,'duration_minutes':layout.duration_minutes,'parts':parts,'rows':rows,'topic_counts':[{'part':k[0],'topic':k[1],'count':v,'unit':'câu'} for k,v in counts.items()]}
dump(ROOT/'audit/outputs/defaults-snapshot.json',{'source':str(prod/'exam_formats/default_matrices.py'),'sha256':hashlib.sha256((prod/'exam_formats/default_matrices.py').read_bytes()).hexdigest(),'layouts_source':str(prod/'exam_formats/thptqg_2026.py'),'subjects':items})
print('snapshot',len(items),'subjects')

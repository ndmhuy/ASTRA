"""Read product format shapes without booting its mutable registry or application."""
from common import *
import ast,types,sys,importlib,functools
PROD=product_root()
@functools.lru_cache(maxsize=1)
def all_shapes():
 if str(PROD) not in sys.path:sys.path.insert(0,str(PROD))
 if 'exam_formats' not in sys.modules:
  pkg=types.ModuleType('exam_formats');pkg.__path__=[str(PROD/'exam_formats')];sys.modules['exam_formats']=pkg
 if 'parsers' not in sys.modules:
  stub=types.ModuleType('parsers')
  for node in ast.parse((PROD/'parsers.py').read_text(encoding='utf-8')).body:
   if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id=='LADDER_BY_CORRECT':stub.LADDER_BY_CORRECT=ast.literal_eval(node.value)
  sys.modules['parsers']=stub
 resolver=importlib.import_module('exam_formats.resolver');qt=importlib.import_module('exam_formats.question_types').QuestionType;formats={}
 # Format ids and special-answer alphabets are read from builtin definitions, never guessed.
 for file in sorted((PROD/'exam_formats').glob('builtin_*.py')):
  assignments={}
  for node in ast.parse(file.read_text(encoding='utf-8')).body:
   if not isinstance(node,ast.Assign):continue
   value=node.value
   if isinstance(value,ast.List) and value.elts and all(isinstance(e,ast.Call) and isinstance(e.func,ast.Name) and e.func.id=='PartDefinition' for e in value.elts):
    parts=[]
    for item in value.elts:
     vals={}
     for kw in item.keywords:
      if kw.arg=='question_type' and isinstance(kw.value,ast.Attribute):vals[kw.arg]=getattr(qt,kw.value.attr)
      else:
       try:vals[kw.arg]=ast.literal_eval(kw.value)
       except (ValueError,TypeError):pass
     parts.append(types.SimpleNamespace(**vals))
    for target in node.targets:
     if isinstance(target,ast.Name):assignments[target.id]=parts
   if isinstance(value,ast.Call) and isinstance(value.func,ast.Name) and value.func.id=='ExamFormatDefinition':
    kw={k.arg:k.value for k in value.keywords};fid=ast.literal_eval(kw['format_id']);partvar=kw.get('default_parts')
    if isinstance(partvar,ast.Name) and partvar.id in assignments:formats.setdefault(fid,{})['']={p.part_id:p for p in assignments[partvar.id]}
 for fid,layouts in resolver._LAYOUTS_BY_FORMAT.items():
  for sid,layout in layouts.items():
   parts={}
   for part in layout.parts:
    kinds={q.qtype for q in part.questions()}
    if len(kinds)==1:parts[part.part_id]=types.SimpleNamespace(part_id=part.part_id,question_type=next(iter(kinds)),valid_answers=[],options_count=None)
   formats.setdefault(fid,{})[sid]=parts
 return formats,resolver

def option_labels_for(exam_type,subject,part):
 formats,resolver=all_shapes();choices=formats.get(exam_type,{})
 parts=choices.get(subject) or choices.get('') or {};p=parts.get(part)
 return tuple(resolver.option_labels(p)) if p is not None else None

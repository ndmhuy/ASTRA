"""Read the product's layout-token grammar; measure existing prototype choices only."""
from common import *
import ast
source=product_root()/'exam_generator/agents/composer.py';tree=ast.parse(source.read_text(encoding='utf-8'));env={'re':re}
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_OPTION_LAYOUT_TAIL' for t in node.targets):env['_OPTION_LAYOUT_TAIL']=eval(compile(ast.Expression(node.value),str(source),'eval'),env)
 if isinstance(node,ast.FunctionDef) and node.name=='_option_block_re':
  node.decorator_list=[];exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),env)
def braced_value(text,start):
 if start>=len(text) or text[start]!='{':return None,start
 depth=1;i=start+1
 while i<len(text):
  if text[i]=='\\':i+=2;continue
  if text[i]=='{':depth+=1
  if text[i]=='}':
   depth-=1
   if depth==0:return text[start+1:i],i+1
  i+=1
 return None,start

def source_options(body,letters):
 letters=tuple(sorted(letters));embedded={}
 for mark in re.finditer(r'\\errorpart\s*',body):
  label,end=braced_value(body,mark.end());value,end=braced_value(body,end)
  if label in letters and value is not None:
   if label in embedded:return None
   embedded[label]=value
 if embedded:return embedded if set(embedded)==set(letters) else None
 m=env['_option_block_re'](letters).search(body)
 if not m:return None
 block=m.group(0);marks=[]
 for mark in re.finditer(r'(?<![A-Za-z])('+ '|'.join(re.escape(x) for x in letters)+r')\.',block):
  if len(marks)<len(letters) and mark[1]==letters[len(marks)]:marks.append(mark)
 if len(marks)!=len(letters):return None
 out={}
 for i,m in enumerate(marks):
  s=block[m.end():marks[i+1].start() if i+1<len(marks) else len(block)].strip()
  while True:
   before=s
   for p in env['_OPTION_LAYOUT_TAIL']:s=p.sub('',s).strip()
   if s.endswith('}') and s.count('{')<s.count('}'):s=s[:-1].strip()
   if s==before:break
  out[m[1]]=s
 return out

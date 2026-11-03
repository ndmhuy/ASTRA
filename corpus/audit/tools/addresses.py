from common import *
def canon(p):
 s=str(p).upper().strip();s=re.sub(r'^(?:PHẦN|PHAN|PART)\s*','',s);return {'I':'P1','II':'P2','III':'P3','1':'P1','2':'P2','3':'P3','IV':'P4','V':'P5'}.get(s,s)
def questions(text,strip_tex_comments=None):
 if strip_tex_comments is None:strip_tex_comments=bool(re.search(r'\\documentclass|\\begin\{document\}',text))
 partmarkers=list(re.finditer(r'(?im)(?:^\s*(?:#{1,4}\s*)?(?:\*\*)?(?:PHẦN|PART)\s+(III|II|I|\d+)\b|LECTURING-PART:\s*([A-Z][A-Z0-9_]*)|^\s*(?:#{1,4}\s*)?(III|II|I)\.\s+(?:PHẦN\s+)?(?:ĐỌC|VIẾT|READING|WRITING)\b|^\s*(?:#{1,4}\s*)?(III|II|I)\.\s*$)',text))
 ms=list(re.finditer(r'(?im)(?:^\s*(?:#{1,5}\s*)?(?:\*\*)?(?:Câu|Question|Задание|Вопрос|問)\s*(\d+)(?=[ \t]*(?:[:.(]|$))|\\textbf\{(?:Câu|Question|Задание|Вопрос|問)\s*(\d+)\s*[:.])',text));out=[]
 # Bare numeric headings are common in language papers and essay sections.
 # Add them only in a declared part region with no Câu/Question headings.
 bounds=[0]+[h.start() for h in partmarkers]+[len(text)]
 numeric=list(re.finditer(r'(?m)^\s*(?:#{1,5}\s*)?(?:\*\*)?(\d+)\s*[.)](?:\*\*)?\s+',text))
 for left,right in zip(bounds,bounds[1:]):
  if not any(left<=m.start()<right for m in ms):ms.extend(m for m in numeric if left<=m.start()<right)
 ms.extend(m for m in re.finditer(r'(?m)^\s*\\noindent\s*\\textbf\{\s*(\d+)\s*[.:]\s*\}',text) if not any(old.start()==m.start() for old in ms))
 ms.sort(key=lambda m:m.start())
 for j,m in enumerate(ms):
  heads=[h for h in partmarkers if h.start()<m.start()];part=canon(next((g for g in heads[-1].groups() if g), 'P1')) if heads else 'P1'
  end=ms[j+1].start() if j+1<len(ms) else len(text)
  nxt=[h.start() for h in partmarkers if m.end()<h.start()<end and canon(next(g for g in h.groups() if g))!=part]
  if nxt:end=min(nxt)
  body=text[m.end():end]
  if strip_tex_comments:body=re.sub(r'(?m)(?<!\\)%[^\n]*','',body)
  body=re.sub(r'\\end\{document\}.*','',body,flags=re.S)
  out.append({'part':part,'idx':int(next(g for g in m.groups() if g)),'text':body.strip()})
 return out

def indexed_questions(text,parts=None):
 qs=questions(text)
 if parts is not None and len(parts)==1:
  for q in qs:q['part']=canon(parts[0]['part'])
 groups={}
 for q in qs:groups.setdefault(q['part'],[]).append(q)
 for part,items in groups.items():
  continuous=items[0]['idx']>1
  for ordinal,q in enumerate(items,1):
   q['printed_idx']=q['idx']
   if continuous:q['idx']=ordinal
 return qs

def expected(text,parts=None):
 result=set();tfparts=None
 if parts is not None:tfparts={canon(x['part']) for x in parts if str(x.get('type','')).lower().replace('-','_') in ['tf','true_false','đúng/sai']}
 only_part=canon(parts[0]['part']) if parts is not None and len(parts)==1 else None
 for q in indexed_questions(text,parts):
  if only_part:q['part']=only_part
  subs=re.findall(r'(?m)^\s*(?:\*\*)?\(?([a-d])\s*[).]',q['text']) if tfparts is None or q['part'] in tfparts else []
  if not subs and (tfparts is None or q['part'] in tfparts):subs=re.findall(r'\\item\[([a-d])\)',q['text'])
  for s in dict.fromkeys(subs or [None]):result.add((q['part'],q['idx'],s))
 return result

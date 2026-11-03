"""Manifest-driven local blind packets; all source/address metadata stays outside grader inputs."""
import json,re,secrets
from pathlib import Path
from grade import call_json,write,read
L=Path(__file__).resolve().parent

def clean(s):
 s=re.sub(r'(?m)(?<!\\)%[^\n]*','',s)
 s=re.sub(r'(?im)^.*(?:LECTURING-|LAB_[AB][12]|run-[AB][12]).*$','',s)
 s=re.sub(r'(?im)^\s*PHẦN\s+(?:III|II|I)\b[^\n]*','',s)
 s=re.sub(r'(?im)^\s*Câu\s+\d+\s*[:.]\s*','',s)
 return s.strip()

def source_questions(path):
 t=Path(path).read_text(encoding='utf-8'); qs=[]
 heads=list(re.finditer(r'(?im)^\s*PHẦN\s+(III|II|I)\b[^\n]*',t))
 markers=list(re.finditer(r'(?im)^\s*Câu\s+(\d+)\s*[:.]',t))
 for i,m in enumerate(markers):
  preceding=[h for h in heads if h.start()<m.start()]
  assert preceding,'source question lacks part'
  h=preceding[-1]; end=markers[i+1].start() if i+1<len(markers) else len(t)
  nextheads=[h.start() for h in heads if m.end()<h.start()<end]
  if nextheads: end=min(nextheads)
  qs.append({'part':h.group(1),'idx':int(m.group(1)),'text':clean(t[m.end():end])})
 return qs

def prepare(manifest):
 mapping_path=L/'outputs/blind-mapping.json'
 mapping=read(mapping_path) if mapping_path.exists() else {}
 for item in manifest:
  label=item['label']
  if label not in mapping:
   mapping[label]={'code':'P'+secrets.token_hex(4).upper()}
   write(mapping_path,mapping)
  code=mapping[label]['code']
  # Pre-parsed question manifest is produced locally from canonical parser for generated tex.
  qs=item.get('questions') or source_questions(item['source'])
  payload={'questions':[{'qid':f'q{i:03d}','text':clean(q['text'])} for i,q in enumerate(qs,1)]}
  expected={q['qid'] for q in payload['questions']}
  def valid(d):
   assert len(d['questions'])==len(qs) and {q['qid'] for q in d['questions']}==expected,'normalizer question count mismatch'
   for q in d['questions']:
    assert isinstance(q['text'],str) and isinstance(q['options'],dict) and isinstance(q['statements'],dict)
  normalized=call_json((L/'prompts/NORMALIZE.txt').read_text(encoding='utf-8'),payload,L/f'outputs/normalized/{code}.json',valid)
  keys=item['keys']; addresses={}; packet={'code':code,'questions':[]}
  normalized_by_id={q['qid']:q for q in normalized['questions']}
  for i,q in enumerate(qs,1):
   qid=f'q{i:03d}'; addresses[qid]={'part':q['part'],'idx':q['idx']}
   entry=dict(normalized_by_id[qid]); entry['key']=keys[q['part']][str(q['idx'])]; packet['questions'].append(entry)
  write(L/f'outputs/blind-packets/{code}.json',packet)
  mapping[label].update(addresses=addresses,source=item['source']); write(mapping_path,mapping)
  print(code,len(qs),'questions normalized',flush=True)
if __name__=='__main__':
 prepare(read(L/'outputs/evaluation-inputs.json'))

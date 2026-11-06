"""Blind evaluation runner. Input packets contain only code/questions/keys.
Mapping/address joins are a separate analysis step; never sent to ask().
No experiment metric is a product content gate.
"""
import argparse,collections,json,re,statistics
from pathlib import Path
from lib import ask,parse
L=Path(__file__).resolve().parent

def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def call_json(prompt,payload,out,validate):
 if Path(out).exists():
  d=read(out); validate(d); return d
 for attempt in range(2):
  try:
   text,usage,_=ask(prompt,json.dumps(payload,ensure_ascii=False))
   d=parse(text); validate(d); d['_backend']=usage; write(out,d); return d
  except Exception:
   if attempt==1: raise

def grade(packet_path):
 packet=read(packet_path); code=packet['code']
 # This whitelist prevents file paths, mapping fields, or provenance from entering grader input.
 payload={'code':code,'questions':[{k:q[k] for k in ('qid','text','options','statements','key') if k in q} for q in packet['questions']]}
 assert not re.search(r'LECTURING|LAB_[AB][12]|run-[AB][12]',json.dumps(payload)), 'unblinded packet'
 expected={q['qid'] for q in packet['questions']}
 def valid(d):
  got={q['qid'] for q in d['questions']}; assert got==expected and len(d['questions'])==len(expected),'grader question mismatch'
  for q in d['questions']:
   source=next(x for x in packet['questions'] if x['qid']==q['qid'])
   wanted=set(source.get('statements') or [None]); actual={s.get('sub') for s in q['slots']}
   assert wanted==actual and len(q['slots'])==len(wanted),'grader scored slot mismatch'
   for s in q['slots']:
    assert 1<=s['score']<=5 and isinstance(s['reasoning_steps'],int)
    assert s['key_status'] in ('correct','wrong','unverified') and s['math_status'] in ('correct','wrong','unverified')
 return call_json((L/'prompts/GRADE.txt').read_text(encoding='utf-8'),payload,L/f'outputs/blind-grades/{code}.json',valid)

def norm(s): return re.findall(r'\w+',str(s).casefold())
def ngrams(s,n=3):
 t=norm(s); return {tuple(t[i:i+n]) for i in range(max(0,len(t)-n+1))}
def similarity(a,b):
 x,y=ngrams(a),ngrams(b); return len(x&y)/len(x|y) if x|y else 0.0

def metrics(packet,grade_result,addresses,extraction,source_questions):
 graded={q['qid']:q['slots'] for q in grade_result['questions']}; bypart=collections.defaultdict(list)
 for q in packet['questions']: bypart[addresses[q['qid']]['part']].append(q)
 result={}
 for part,qs in bypart.items():
  slots=[s for q in qs for s in graded[q['qid']]]; ratios=[]; strict=ties=longest=0; key_letters=collections.Counter(); tf=[]; nearest=[]
  for q in qs:
   opts=q.get('options') or {}; key=q.get('key'); lengths={k:len(' '.join(norm(v))) for k,v in opts.items()}
   if lengths:
    mx=max(lengths.values()); winners=[k for k,v in lengths.items() if v==mx]
    ratios.append(mx/statistics.mean(lengths.values()) if sum(lengths.values()) else 0)
    key_letters[str(key)]+=1
    if key in winners:
     longest+=1; strict+=len(winners)==1; ties+=len(winners)>1
   if q.get('statements'): tf.append(key)
   matches=[(similarity(q['text'],s['text']),s['source_id']) for s in source_questions]
   nearest.append({'qid':q['qid'],'similarity':max(matches)[0] if matches else None,'source':max(matches)[1] if matches else None})
  rows=[r for r in extraction['rows'] if re.sub(r'^PHẦN\s+','',str(r['part']).strip(),flags=re.I).upper()==re.sub(r'^PHẦN\s+','',str(part).strip(),flags=re.I).upper()]
  topics=collections.Counter(' '.join(norm(r['topic'])) for r in rows)
  construction_pairs=sum(similarity(a.get('given','')+' '+a.get('task',''),b.get('given','')+' '+b.get('task',''))>=.65 for i,a in enumerate(rows) for b in rows[i+1:])
  result[part]={'question_count':len(qs),'slot_count':len(slots),'mean_score':statistics.mean(s['score'] for s in slots),'mcq_n':len(ratios),'key_longest_share_including_ties':longest/len(ratios) if ratios else None,'key_strictly_longest_share':strict/len(ratios) if ratios else None,'key_longest_ties':ties,'longest_mean_option_ratio':statistics.mean(ratios) if ratios else None,'key_letters':dict(key_letters),'true_false_patterns':tf,'mean_reasoning_steps':statistics.mean(s['reasoning_steps'] for s in slots),'separating_slots':sum(s['separates_strong_average'] is True for s in slots),'extracted_high_slots':sum(r['discrimination']=='high' for r in rows),'grade_spread':dict(collections.Counter(str(r['grade']) for r in rows)),'repeated_topic_extra_slots':sum(n-1 for n in topics.values()),'repeated_construction_pairs_jaccard_ge_065':construction_pairs,'nearest_source_per_question':nearest,'wrong_keys':sum(s['key_status']=='wrong' for s in slots),'wrong_math':sum(s['math_status']=='wrong' for s in slots),'unverified_keys':sum(s['key_status']=='unverified' for s in slots),'unverified_math':sum(s['math_status']=='unverified' for s in slots)}
 return result

def main():
 a=argparse.ArgumentParser(); a.add_argument('packets',nargs='+'); ns=a.parse_args()
 for f in ns.packets:
  result=grade(f); print(Path(f).name,'graded',len(result['questions']),flush=True)
if __name__=='__main__': main()

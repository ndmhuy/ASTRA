"""Focused corpus validation, never imports or runs the app test suite."""
from common import *
from addresses import *
import ast,csv,collections
checks=[]
def record(name,ok,detail):checks.append({'case':name,'pass':bool(ok),'detail':detail})
for p in (ROOT/'audit/tools').glob('*.py'):
 try:ast.parse(p.read_text(encoding='utf-8'));record('syntax:'+p.name,True,'AST parse')
 except SyntaxError as e:record('syntax:'+p.name,False,str(e))
inv=load(ROOT/'audit/outputs/prototype-inventory.json')
for x in inv:
 if x['path'].endswith('.tex') and x.get('key'):
  qs=questions(evidence_path(x['path']).read_text(encoding='utf-8'));ks=load(x['key'])['questions'];record('prototype-address-count:'+x['path'],len(qs)==len(ks),{'parsed':len(qs),'key_questions':len(ks)})
registry=list(csv.DictReader((ROOT/'registry/papers.csv').open(encoding='utf-8')))
record('registry:no-non-subjects',not any(x['subject'].endswith(('.md','.json')) for x in registry),'Rows must be papers only')
record('registry:no-app-generated',not any('provincial-toan-unverified' in x['path'] for x in registry),'Generated sources excluded')
record('registry:references-excluded',not any(x['class']=='format_only' and x['usable_as_content_evidence']=='True' for x in registry),'Format-only never content evidence')
for d in (ROOT/'profiles').glob('*') if (ROOT/'profiles').exists() else []:
 f=d/'rows.json'
 if not f.exists():continue
 data=load(f);record('profile:one-model:'+d.name,len({p['model'] for p in data['papers']})<=1,{'models':sorted({p['model'] for p in data['papers']})})
 record('profile:no-reference:'+d.name,not any('reference' in p['path'] for p in data['papers']),'All source paths checked')
 refs=[r['ref'] for r in data['rows']];record('profile:unique-refs:'+d.name,len(refs)==len(set(refs)),{'rows':len(refs),'unique':len(set(refs))})
 if (d/'verification.json').exists():
  v=load(d/'verification.json');record('profile:address-coverage:'+d.name,not v.get('address_coverage_incomplete'),v.get('address_coverage_issues',[]));record('profile:refs-resolve:'+d.name,not v['refs_invalid'],{'invalid':v['refs_invalid']});record('profile:no-ten-word-copy:'+d.name,v['ten_word_overlap_count']==0,{'overlaps':v['ten_word_overlap_count']})

record('parser:repeated-part-heading-keeps-subitems',expected('PHẦN II\nCâu 1: stem\na) x\nPHẦN II (tiếp)\nb) y\nc) z\nd) w',[{'part':'P2','type':'true_false'}])=={('P2',1,s) for s in 'abcd'},'A repeated heading on the next page must not truncate statements')

from option_measure import source_options
from registry_shape import option_labels_for
labels=option_labels_for('THPTQG','SinhHoc','P1')
opts=source_options(r"\noindent A. alpha \hfill B. beta \hfill C. gamma \hfill D. Z, Y, A.\\",labels)
record('options:literal-label-inside-last-choice',opts is not None and 'Z, Y, A.' in opts[labels[-1]],'Trailing gene/point label must remain part of the last option')
opts=source_options(r"x \errorpart{A}{\textbf{who} goes} \errorpart{B}{has} \errorpart{C}{increased} \errorpart{D}{recently}",labels)
record('options:embedded-choice-markers',opts is not None and len(opts)==len(labels) and opts[labels[0]]==r'\textbf{who} goes','Error-identification spans are actual alternatives, including nested TeX')
record('parser:markdown-percent-preserved','remainder' in questions('Câu 1: value 40% remainder')[0]['text'],'A percentage in Markdown is not a TeX comment')
record('parser:tex-comment-excluded','hidden answer' not in questions(r'\documentclass{article}'+'\n'+r'\textbf{Câu 1:} stem % hidden answer')[0]['text'],'Real TeX comments must not leak into blind body text')
from prototype_quality import attach as attach_quality
probe={'rows':[],'metrics':{'answer_comparisons':[{'part':'P2','idx':1,'sub':'a','published':'D','independent':'Đ','same_literal':False}]}}
attach_quality(probe)
record('audit:tf-spelling-not-key-disagreement',probe['metrics']['answer_comparisons'][0]['same_answer'] and not probe['metrics']['answer_comparisons'][0]['same_literal'],'D and Đ are semantically equal while raw spelling comparison remains available')
probe={'rows':[{'part':'P1','idx':1,'alternatives':[{'label':'A','identifiable_error':False,'wording_eliminable':False},{'label':'B','identifiable_error':True,'wording_eliminable':True},{'label':'C','identifiable_error':True,'wording_eliminable':False}]}],'metrics':{'answer_comparisons':[{'part':'P1','idx':1,'sub':None,'published':'A','independent':'A','same_literal':True,'confidence':'high'}]}}
attach_quality(probe);q=probe['metrics']['distractor_quality']
record('audit:linked-error-can-still-be-wording-giveaway',q['qualified']==1 and q['judged']==2 and q['linked_but_wording_eliminable']==1,'Naming a misconception alone must not qualify an easily eliminated distractor')
dump(ROOT/'audit/outputs/data-checks.json',{'checks':checks,'passed':sum(c['pass'] for c in checks),'failed':sum(not c['pass'] for c in checks)})
print('checks',len(checks),'failed',sum(not c['pass'] for c in checks))

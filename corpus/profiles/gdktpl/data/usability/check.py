"""Read-only reproducible verification for the scoped GDKTPL usability decision."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import json,hashlib,subprocess,csv,io
P=Path(__file__).resolve().parents[2]
ROOT=P.parents[1]
def read(rel):return json.loads((P/rel).read_text(encoding='utf-8'))
def h(obj):return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
bank=read('data/samples-current.json');samples=bank['samples'];byid={s['id']:s for s in samples};receipt=read('USABILITY-REVIEW.json');checks={};errors=[]
def check(name,value):
 checks[name]=bool(value)
 if not value:errors.append(name)
check('73_unique_samples',len(samples)==len(byid)==73)
check('157_atomic_answers',sum(len(s['answers']) for s in samples)==157)
check('canonical_banks_equal',samples==read('data/scoped-final-bank.json')['samples'])
for s in samples:
 sid=s['id'];ans=s['answers'];opts=s.get('options',{});stat=s.get('statements',[])
 if s['qtype']=='mcq':check(sid+'_shape',set(opts)==set('ABCD') and len(ans)==1 and ans[0]['value'] in opts and not stat)
 else:check(sid+'_shape',not opts and [a['sub'] for a in ans]==list('abcd') and [a['sub'] for a in stat]==list('abcd') and all(a['value'] in ('D','Đ','S') for a in ans))
 check(sid+'_decision',s['status']=='agent_reviewed_for_use' and s['usability_review']['teacher_approved'] is False and not s['usability_review']['teacher_review_required_for_this_release'])
 check(sid+'_variation_conditions',s['variation_guidance']==bank['usability_conditions'])
 page=(P/'samples'/f'{sid}.md').read_text(encoding='utf-8')
 check(sid+'_page_stem_sync',s['stem'] in page)
 r=next(r for r in receipt['samples'] if r['id']==sid)
 check(sid+'_receipt_content_hash',r['content_sha256']==h({k:s[k] for k in ('stem','options','statements','answers')}))
cov=read('data/coverage-current.json');covered=0;missing=[]
for cell in cov['cells']:
 valid=[sid for sid in cell['sample_ids'] if sid in byid and byid[sid]['part']==cell['part'] and byid[sid]['topic_id']==cell['topic_id'] and any(a['level']==cell['level'] for a in byid[sid]['answers'])]
 if valid:covered+=1
 else:missing.append(cell['id'])
check('76_of77_cells_at_actual_level',len(cov['cells'])==77 and covered==76 and missing==['CELL-266deb41151a'])
check('F031_remains_usable_TH',byid['KT-F-031']['answers'][0]['level']=='TH')
# Independently reproducible numerical checks, not a model call or a substitute for the narrative reread.
A_after=Fraction(1452*100,110)/110;B_before=Fraction(1800,200);B_after=Fraction(2376*100,110)/220
check('F025_effect10percent',A_after/(10*(B_after/B_before))-1==Fraction(1,10))
check('F025_poverty_count',100000*Fraction(12,100)==12000 and 110000*Fraction(11,100)==12100)
check('F027_financing',12+4-8-7+3+12-5==11 and 12-8-4+3+12-3==12)
check('F028_difference_in_differences',((32-20)-(25-18))-4==1 and (((32-20)-(22-18))-4)-1==3)
check('F029_proportional_counterfactual',100*Fraction(64,80)-70==10)
check('F031_cash_balances',21+12-10-8==15 and 15+10-10==15 and 21+12-10-3==20 and 20+10-10-6==14)
check('F032_bridge_training',6>=6 and 8-6==2 and 3<6 and 0<6 and 4<6)
base=receipt['base_commit'];changed=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only',base,'--','transcriptions/gdktpl','profiles/gdktpl/rows.json','profiles/gdktpl/evidence'],text=True).strip()
check('source_transcriptions_rows_evidence_unchanged',not changed)
for artifact,meta in read('prototype-revised/verification.json')['artifacts'].items():
 q=P/'prototype-revised'/meta['path'];check('prototype_'+artifact+'_unchanged',hashlib.sha256(q.read_bytes()).hexdigest()==meta['sha256'])
check('all21_guides',len(list((P/'topics').glob('T*.md')))==21)
for q in (P/'topics').glob('T*.md'):
 text=q.read_text(encoding='utf-8');check(q.stem+'_no_linear_TF_default','theo rubric nghiên cứu 0,25/ý' not in text)
print(json.dumps({'subject':'gdktpl','checks':len(checks),'passed':sum(checks.values()),'failed':errors,'samples':len(samples),'atomic_answers':157,'covered_cells':covered,'target_cells':77,'missing_proposed_cells':missing},ensure_ascii=False))
raise SystemExit(bool(errors))

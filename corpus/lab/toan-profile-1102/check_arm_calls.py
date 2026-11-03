"""Validate experimental treatment delivery from captured real calls."""
import json,sys
from pathlib import Path
L=Path(__file__).resolve().parent
plan_add=(L/'prompts/PLAN_ADDENDUM.txt').read_text(encoding='utf-8').strip()
compose_add=(L/'prompts/COMPOSER_ADDENDUM.txt').read_text(encoding='utf-8').strip()
def check(tag,arm):
 out=L/f'outputs/run-{tag}'; calls=[json.loads(f.read_text(encoding='utf-8'))|{'file':str(f)} for f in sorted((out/'calls').glob('*.json'))]
 plan=[c for c in calls if "You are helping a Vietnamese teacher plan an exam paper" in c['system']]
 composer=[c for c in calls if compose_add in c['system'] or ('Use only the accepted part scope' in c['system'])]
 details=[]
 for role,subset,add in [('PLAN_SYNTHESIS',plan,plan_add),('composer',composer,compose_add)]:
  for c in subset:
   details.append({'role':role,'file':c['file'],'profile_in_input':'exam_profile' in c['user'],'addendum_in_system':add in c['system'],'answered':'reply' in c,'backend':c.get('backend'),'model':c.get('model')})
 expected=arm=='profile'
 passed=bool(plan and composer) and all(d['profile_in_input']==expected and d['addendum_in_system']==expected and d['answered'] for d in details)
 final=out/'final-session.json'; done=final.exists() and json.loads(final.read_text(encoding='utf-8')).get('current_step')=='DONE'
 result={'tag':tag,'arm':arm,'treatment_verified':passed,'DONE':done,'calls':details}
 (out/'treatment-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(tag,'verified',passed,'DONE',done,'PLAN',len(plan),'composer',len(composer))
 return passed and done
if __name__=='__main__': sys.exit(0 if check(*sys.argv[1:]) else 1)

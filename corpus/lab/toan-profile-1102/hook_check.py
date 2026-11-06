import hashlib,json,os,sys
sys.path.insert(0,os.getcwd())
from exam_generator.prompt_texts import plan_v2 as T
from exam_generator import plan_synthesis as S, plan_recipe_contract as R, plan_clients as PC, prompt_text_gate as G
print('hash before matches',hashlib.sha256(T.PLAN_SYNTHESIS.encode()).hexdigest()==R.TEXT_HASHES[S.KEY])
T.PLAN_SYNTHESIS+='X'; R.TEXT_HASHES[S.KEY]=hashlib.sha256(T.PLAN_SYNTHESIS.encode()).hexdigest()
t=G.text('plan_v2','PLAN_SYNTHESIS'); print('gate sees patched',t.endswith('X'), hashlib.sha256(t.encode()).hexdigest()==PC.TEXT_HASHES[S.KEY])
T.COMPOSER_SCOPE+='Y'; print('reader sees',G.reader('plan_v2')('COMPOSER_SCOPE').endswith('Y'))
from exam_generator import plan_context as C, pipeline as P
print('pipeline uses module attr',"plan_context.data_block" in open(P.__file__).read())

import json,os,re,subprocess,tempfile,datetime
from pathlib import Path
L=Path(__file__).resolve().parent
BACKEND='codex-cli'
MODEL='gpt-6.1-sol'
class RetainedDirectory:
    def __init__(self,prefix):
        root=L/'sb'/'cli-cwd'; root.mkdir(parents=True,exist_ok=True)
        self.name=tempfile.mkdtemp(prefix=prefix,dir=root)
    def __enter__(self): return self.name
    def __exit__(self,*args): return False
def ask(system,user,model=None,timeout=1500):
    env={k:v for k,v in os.environ.items() if k not in ('ANTHROPIC_API_KEY','OPENAI_API_KEY','GEMINI_API_KEY','GEMINI_API_KEYS')}
    with RetainedDirectory(prefix='lec-lab-') as cwd:
        out=Path(cwd)/'reply.txt'
        argv=['codex','exec','--skip-git-repo-check','--sandbox','read-only','--model',MODEL,'--ephemeral','--output-last-message',str(out),'-']
        r=subprocess.run(argv,input='<system_instructions>\n'+system+'\n</system_instructions>\n'+user,capture_output=True,text=True,timeout=timeout,env=env,cwd=cwd)
        reply=out.read_text(encoding='utf-8') if out.exists() else ''
    with (L/'backend-calls.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps({'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'backend':BACKEND,'model':MODEL,'returncode':r.returncode,'reply_chars':len(reply)},ensure_ascii=False)+'\n')
    if r.returncode: raise RuntimeError((r.stderr+r.stdout)[-1500:])
    if not reply: raise RuntimeError('Codex returned no final text')
    return reply,{'backend':BACKEND,'model':MODEL},None
def parse(t):
    t=t.strip(); t=re.sub(r'^```(?:json)?\s*|\s*```$','',t)
    return json.loads(t[t.find('{'):t.rfind('}')+1])

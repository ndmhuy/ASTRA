import json,os,sys
sys.path.insert(0,os.getcwd())
from fastapi.testclient import TestClient
import web_app,launch_token
c=TestClient(web_app.app,headers={launch_token.HEADER_NAME:launch_token.token()})
for p in ('/api/ai/mode','/api/plan'):
    r=c.get(p); d=r.json() if r.headers.get('content-type','').startswith('application/json') else r.text[:200]
    if isinstance(d,dict): d={k:v for k,v in d.items() if not any(s in k.lower() for s in('key','token','secret','email'))}
    print(p,r.status_code,json.dumps(d,ensure_ascii=False)[:700])

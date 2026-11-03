"""Join curriculum metadata by original subject name, never by exam topic heuristics."""
from common import *
from functools import lru_cache
import unicodedata

def norm(s):return re.sub(r'\W+','', ''.join(c for c in unicodedata.normalize('NFD',s.casefold().replace('đ','d')) if unicodedata.category(c)!='Mn'))
@lru_cache(maxsize=32)
def catalog_context(subject):
 path=ROOT/'audit/outputs/curriculum-catalog.json';snapshot=ROOT/'audit/outputs/defaults-snapshot.json'
 if not path.exists():return {'status':'no_catalog'}
 data=load(path);names={}
 for f in data['source_files']:
  source=Path(f['path']);slug=source.stem.rsplit('-',1)[0]
  if not source.exists():continue
  first=next((line for line in source.read_text(encoding='utf-8').splitlines() if line.strip()),None)
  if first:
   name=load_name=json.loads(first).get('subject','');names[norm(name)]=slug
 candidates=[subject]
 if snapshot.exists():
  for s in load(snapshot)['subjects'].values():
   if norm(s['display_name'])==norm(subject):candidates.append(s['display_name'])
 slug=next((names[norm(c)] for c in candidates if norm(c) in names),None)
 if slug is None:return {'status':'no_matching_curriculum_subject','subject':subject,'note':'No subject-name match; do not invent a catalog.'}
 rows=data['subjects'][slug];return {'status':'draft_curriculum_metadata_not_exam_evidence','grades_available':data['grades_by_subject'].get(slug,[]),'lessons':[{'grade':r['grade'],'chapter':r.get('chapter'),'lesson':r['lesson']} for r in rows],'limitations':'Source curriculum maps can be draft or third-party teaching plans, incomplete; this is a grade/topic aid, not evidence of exam frequency. Missing grade levels cannot be treated as absent from real papers.'}

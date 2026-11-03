from common import *
import collections

def summarise(subject,items):
 unique={x['output']['blind_code']:x for x in items};rfile=ROOT/'profiles'/subject/'rows.json';real=load(rfile) if rfile.exists() else {'rows':[],'papers':[]};topics=sorted({r['topic'] for r in real['rows']}|{r['topic'] for x in unique.values() for r in x['output']['rows']});anchorfile=ROOT/'audit/outputs/matrix-mapping'/f'{subject}.json';anchors=load(anchorfile).get('topic_mapping',[]) if anchorfile.exists() else []
 payload={'input_topics':topics,'canonical_profile_mapping':anchors,'prototype_audits':[{'code':x['output']['blind_code'],'rows':[{k:r.get(k) for k in ['part','idx','topic','grade','routine','discrimination','error_flags','coverage_comment','statements','alternatives']} for r in x['output']['rows']],'metrics':x['output']['metrics']} for x in unique.values()]}
 payload=json.loads(json.dumps(payload,ensure_ascii=False))
 # Option texts are unnecessary here and must not be copied to summary.
 for audit in payload['prototype_audits']:
  for row in audit['rows']:
   for a in row.get('alternatives') or []:a.pop('text',None)
 path=ROOT/'audit/outputs/prototype-summaries'/f'{subject}.json';signature=hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest();input_file=path.with_suffix('.input.json');cache_current=path.exists() and input_file.exists() and load(input_file).get('sha256')==signature
 if path.exists() and not cache_current:
  archive=ROOT/'audit/outputs/prototype-summary-history'/subject/(str(time.time_ns())+'.json');dump(archive,load(path))
 def call():
  x=ask('prototype-summary-'+subject+'-'+signature[:12],(ROOT/'audit/prompts/PROTOTYPE_SUMMARY.txt').read_text()+'\n'+json.dumps(payload,ensure_ascii=False),timeout=900)
  got=[t['input_topic'] for t in x['topic_mapping']]
  if set(got)!=set(topics) or len(got)!=len(topics) or len(x.get('fixes',[]))>3:raise ValueError('PROTOTYPE_SUMMARY_MAPPING_OR_FIX_COUNT')
  anchored={m['input_topic']:m.get('default_topic') or m['family_topic'] for m in anchors};found={m['input_topic']:m['family_topic'] for m in x['topic_mapping']}
  if any(found[t]!=family for t,family in anchored.items()):raise ValueError('PROTOTYPE_SUMMARY_CANONICAL_ANCHOR_DRIFT')
  return x
 summary=load(path) if cache_current else twice('prototype-summary-'+subject+'-'+signature[:12],call)
 if summary is None:return ['Tổng hợp theo môn thất bại hai lần; giữ nguyên kết quả từng câu, chưa có đề xuất sửa theo môn.']
 dump(path,summary);dump(input_file,{'sha256':signature,'canonical_mapping_present':bool(anchors),'context_change_requires_new_summary_not_new_item_grades':True});mapping={x['input_topic']:x['family_topic'] for x in summary['topic_mapping']};rp=collections.defaultdict(set);rq=collections.defaultdict(set);high=collections.defaultdict(set);paper_classes={r['paper_id']:r['evidence_class'] for r in real['rows']}
 for r in real['rows']:
  k=(r['evidence_class'],r['part'],mapping[r['topic']]);rp[k].add(r['paper_id']);rq[(r['paper_id'],r['part'],mapping[r['topic']])].add(r['idx'])
  if r.get('discrimination')=='high':high[r['paper_id']].add((r['part'],r['idx']))
 doc=['## Phủ chủ đề so với đề thật','','Hiện diện đếm theo đề phân biệt; không cộng chính thức với tỉnh. Chủ đề đã ánh xạ về cùng họ nội dung bằng model. Câu TF có nhiều chủ đề có thể hiện diện ở hơn một hàng; không cộng bảng thành tổng câu.','', '| Phần | Chủ đề | Đề chính thức có | Đề tỉnh có | Prototype (câu) |','|---|---|---:|---:|---|'];families=sorted(set((k[1],k[2]) for k in rp)|{(r['part'],mapping[r['topic']]) for x in unique.values() for r in x['output']['rows']});ct=collections.Counter(p['class'] for p in real['papers'])
 for part,topic in families:
  official=f'{len(rp[("official",part,topic)])}/{ct["official"]}' if ct['official'] else 'chưa có đề';provincial=f'{len(rp[("provincial_third_party",part,topic)])}/{ct["provincial_third_party"]}' if ct['provincial_third_party'] else 'chưa có đề'
  proto='; '.join(code+': '+str(sum(r['part']==part and mapping[r['topic']]==topic for r in x['output']['rows'])) for code,x in unique.items());doc.append(f'| {part} | {topic} | {official} | {provincial} | {proto} |')
 doc+=['','## Phân hoá cao so với đề thật','','Ước lượng model; một câu thật được tính cao nếu có ít nhất một ý được gắn cao. Chưa có điểm học sinh.','']
 for pid,cls in sorted(paper_classes.items()):doc.append('- '+cls+' / '+pid+': '+str(len(high[pid]))+' câu.')
 for code,x in unique.items():doc.append('- Prototype '+code+': '+str(x['output']['metrics']['high_discrimination_count'])+' câu.')
 doc+=['','## Nghi vấn nặng nhất','']
 for f in summary.get('worst_findings',[]):doc.append('- '+f['code']+' '+f['part']+'/'+str(f['idx'])+': '+f['finding'])
 doc+=['','## Tối đa ba việc sửa cụ thể','']+['- '+f for f in summary.get('fixes',[])]+['','Giới hạn: '+'; '.join(summary.get('limits',[])),''];return doc

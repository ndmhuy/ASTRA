from common import *
import collections
ALIASES={'giao-duc-kinh-te-va-phap-luat':'gdktpl'}
SUBJECT_IDS={'toan':'Toan','vat-li':'VatLy','hoa-hoc':'HoaHoc','sinh-hoc':'SinhHoc','lich-su':'LichSu','dia-li':'DiaLy','gdktpl':'GDKTPL','tin-hoc':'TinHoc','ngu-van':'NguVan','tieng-anh':'TiengAnh','tieng-nga':'TiengNga','tieng-nhat':'TiengNhat','tieng-han':'TiengHan','tieng-phap':'TiengPhap','tieng-duc':'TiengDuc','tieng-trung':'TiengTrung','cong-nghe-cong-nghiep':'CongNgheCongNghiep','cong-nghe-nong-nghiep':'CongNgheNongNghiep'}
def publish_matrices(proposed):
 lines=['# Đối chiếu ma trận mặc định','','Chỉ là báo cáo và đề xuất; không thay product. Các môn chưa có báo cáo riêng vẫn chưa hoàn tất audit. Snapshot và hash ở audit/outputs/defaults-snapshot.json.','']
 for file in sorted((ROOT/'audit/matrices').glob('*.md')):lines+=[file.read_text(encoding='utf-8'),'']
 (ROOT/'audit/default-matrices.md').write_text('\n'.join(lines),encoding='utf-8');dump(ROOT/'audit/proposed-matrices.json',proposed)

def stage3(subjects=None):
 defaults=load(ROOT/'audit/outputs/defaults-snapshot.json')['subjects'];saved=ROOT/'audit/proposed-matrices.json';proposed=load(saved) if saved.exists() else {};sections=['# Đối chiếu ma trận mặc định','','Chỉ là đề xuất dữ liệu; không sửa product. Cột mặc định đếm câu; cột bằng chứng đếm số đề phân biệt có chủ đề. Số ý không biến thành số đề. Một đề chính thức không đại diện tần suất ổn định. Toán do chủ app đặt tay, chỉ chủ app quyết định thay đổi.','']
 for subject,sid in SUBJECT_IDS.items():
  if subjects and subject not in subjects:continue
  d=ROOT/'profiles'/subject;rowsfile=d/'rows.json';sections+=['## '+subject,'']
  if not rowsfile.exists():sections+=['Chưa đủ bằng chứng; không đề xuất.',''];proposed[subject]={'status':'insufficient_evidence'};continue
  data=load(rowsfile);rows=data['rows'];papers=data['papers'];counts=collections.Counter(p['class'] for p in papers)
  if len(papers)<5 or (subject=='toan' and counts['provincial_third_party']<20):
   sections+=[f'Chưa đủ bằng chứng: chính thức {counts["official"]}, tỉnh {counts["provincial_third_party"]}. Không đề xuất.',''];proposed[subject]={'status':'insufficient_evidence','paper_counts':dict(counts)};continue
  verification=load(d/'verification.json') if (d/'verification.json').exists() else {}
  structure=load(d/'paper-structures.json') if (d/'paper-structures.json').exists() else {}
  qa_ok=verification.get('aggregate_classes_complete') and verification.get('aggregate_input_current') and verification.get('no_reference_inputs') and not any(verification.get(k) for k in ['source_hash_mismatches','address_coverage_incomplete','refs_invalid','wrong_option_coverage_issues','ten_word_overlap_count','numeric_narrative_candidates']) and len(structure.get('observations',[]))==len(papers)
  if not qa_ok:
   sections+=['Hồ sơ còn chờ kiểm định hoặc cấu trúc câu chùm/thứ tự; chưa đề xuất ma trận.',''];proposed[subject]={'status':'profile_QA_hold','paper_counts':dict(counts)};continue
  default=defaults[sid];topics=sorted({x['topic'] for x in rows});mpath=ROOT/'audit/outputs/matrix-mapping'/f'{subject}.json'
  def mapping_call():
   x=ask('matrix-map-'+subject,(ROOT/'audit/prompts/MATRIX_MAP.txt').read_text()+'\n'+json.dumps({'subject':subject,'input_topics':topics,'default':default},ensure_ascii=False))
   got=[m['input_topic'] for m in x['topic_mapping']]
   if set(got)!=set(topics) or len(got)!=len(topics):raise ValueError('TOPIC_MAP_COVERAGE')
   return x
  mapping=load(mpath) if mpath.exists() else twice('matrix-map-'+subject,mapping_call)
  if mapping is None:sections+=['Ánh xạ chủ đề thất bại hai lần; chưa thể đối chiếu hoặc đề xuất.',''];continue
  dump(mpath,mapping)
  run([os.sys.executable,'audit/tools/profile_topics.py',subject],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  lookup={m['input_topic']:m for m in mapping['topic_mapping']}
  for m in lookup.values():m['comparison_topic']=m.get('default_topic') or m['family_topic']
  evidence=collections.defaultdict(lambda:collections.defaultdict(set));qcounts=collections.defaultdict(lambda:collections.defaultdict(set));grades=collections.defaultdict(set)
  for r in rows:
   topic=lookup[r['topic']]['comparison_topic'];key=(r['part'],topic);evidence[key][r['evidence_class']].add(r['paper_id']);qcounts[(r['evidence_class'],r['part'],topic,r['paper_id'])]['questions'].add(r['idx']);grades[key].add(r.get('grade'))
  table=[]
  for (part,topic),byclass in sorted(evidence.items()):
   oldtopics={lookup[r['topic']].get('default_topic') for r in rows if r['part']==part and lookup[r['topic']]['comparison_topic']==topic};oldtopics.discard(None)
   dc=sum(x['count'] for x in default['topic_counts'] if x['part']==part and x['topic'] in oldtopics)
   v={'part':part,'topic':topic,'grades':sorted(grades[(part,topic)],key=str),'default_count':dc,'default_topics':sorted(oldtopics),'official_papers':len(byclass['official']),'provincial_papers':len(byclass['provincial_third_party']),'official_ids':sorted(byclass['official']),'provincial_ids':sorted(byclass['provincial_third_party'])}
   for cls,label in [('official','official_mean_questions'),('provincial_third_party','provincial_mean_questions')]:
    n=counts[cls];v[label]=sum(len(x['questions']) for k,x in qcounts.items() if k[:3]==(cls,part,topic))/n if n else None
   table.append(v)
  # Current default topics with zero evidence remain visible.
  for x in default['topic_counts']:
   if not any(x['part']==v['part'] and x['topic'] in v['default_topics'] for v in table):table.append({'part':x['part'],'topic':x['topic'],'grades':[],'default_count':x['count'],'default_topics':[x['topic']],'official_papers':0,'provincial_papers':0,'official_mean_questions':0,'provincial_mean_questions':0})
  dump(ROOT/'audit/outputs/matrix-evidence'/f'{subject}.json',{'counts':dict(counts),'table':table,'mapping':mapping})
  sections += [f'Đề chính thức: {counts["official"]}; đề tỉnh: {counts["provincial_third_party"]}.','', '| Phần | Chủ đề | Lớp | Mặc định (câu) | Đề chính thức có | Đề tỉnh có |','|---|---|---|---:|---:|---:|']
  for x in table:sections.append(f'| {x["part"]} | {x["topic"]} | {", ".join(map(str,x["grades"]))} | {x["default_count"]} | {x["official_papers"]}/{counts["official"]} | {x["provincial_papers"]}/{counts["provincial_third_party"]} |')
  sections+=['','Đối chiếu ở cấp chương: các bài cùng nằm trong một chương mặc định được gộp, không gán số câu mặc định của cả chương cho từng bài. Một câu tích hợp có thể hiện diện ở nhiều chương; không cộng các hàng thành tổng câu. Tệp matrix-evidence có trung bình số câu/đề, còn hiện diện chủ đề không tự chứng minh quá nặng.','']
  ppath=ROOT/'audit/outputs/matrix-proposals'/f'{subject}.json'
  def propose():
   x=ask('matrix-propose-'+subject,(ROOT/'audit/prompts/MATRIX_PROPOSE.txt').read_text()+'\n'+json.dumps({'subject':subject,'paper_counts':dict(counts),'default':default,'evidence':table,'observed_paper_structure':load(d/'paper-structures.json') if (d/'paper-structures.json').exists() else {'status':'structure_not_yet_extracted'},'structure_audit_path':str(ROOT/'audit/block-structure.md')},ensure_ascii=False))
   if x['status']=='proposal_only':
    parts={p['part_id']:p['count'] for p in default['parts']};got=x['_PART_TOPICS'];known={r['topic'] for r in table}
    if set(got)!=set(parts) or any(len(got[k])!=n for k,n in parts.items()) or any(t not in known for ts in got.values() for t in ts):raise ValueError('PROPOSAL_SHAPE_OR_UNKNOWN_TOPIC')
   return x
  x=load(ppath) if ppath.exists() else twice('matrix-propose-'+subject,propose)
  if x is None:sections+=['Đề xuất thất bại hai lần; không thay bằng danh sách tự đoán.',''];continue
  dump(ppath,x);x['paper_counts']=dict(counts);x['evidence_per_topic']=table;proposed[subject]=x
  sections+=['','Các ghi chú ánh xạ sau chỉ phản ánh bước nhận danh sách tên chủ đề; bước đó không nhận phân lớp nguồn. Bảng đếm ở trên đã nối về từng đề và tách chính thức/tỉnh; không hiểu ghi chú thiếu metadata ở bước ánh xạ là thiếu metadata của toàn bộ audit.','']
  for concern in mapping.get('concerns',[]):sections.append('- '+concern)
  for risk in x.get('risks',[]):sections.append('- Giới hạn: '+risk)
  for decision in x.get('owner_decisions',[]):sections.append('- Chủ app quyết: '+decision)
  sections+=['']
  start=next(i for i,line in enumerate(sections) if line=='## '+subject)
  detail=ROOT/'audit/matrices'/f'{subject}.md';detail.parent.mkdir(parents=True,exist_ok=True);detail.write_text('# Audit ma trận — '+subject+'\n\nĐối chiếu theo bằng chứng; chỉ là đề xuất, chưa thay product.\n\n'+'\n'.join(sections[start+2:])+'\n',encoding='utf-8')
  publish_matrices(proposed)
 publish_matrices(proposed)
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--subjects',nargs='*');args=ap.parse_args();stage3(args.subjects)

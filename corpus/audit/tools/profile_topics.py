"""Readable topic dossiers from existing evidence; never invent samples or cognitive labels."""
from common import *
from stage3 import SUBJECT_IDS
import collections

def render(subject):
 d=ROOT/'profiles'/subject
 if not (d/'profile.compact.json').exists():return
 p=load(d/'profile.compact.json');data=load(d/'rows.json');papers=data['papers']
 if len(papers)<5:return
 mapping_file=ROOT/'audit/outputs/matrix-mapping'/f'{subject}.json';mapping=load(mapping_file)['topic_mapping'] if mapping_file.exists() else []
 families={m['input_topic']:m.get('default_topic') or m['family_topic'] for m in mapping};groups=collections.defaultdict(list)
 for row in data['rows']:groups[families.get(row['topic'],row['topic'])].append(row)
 defaults=load(ROOT/'audit/outputs/defaults-snapshot.json')['subjects'][SUBJECT_IDS[subject]];den=collections.Counter(x['class'] for x in papers);result=[]
 title='# Hồ sơ theo chủ đề — '+subject
 lines=[title,'','Đây là lớp hồ sơ đang bổ sung. Audit ma trận, audit prototype, mức NB/TH/VD và câu mẫu mới được báo trạng thái riêng; trích xuất kỹ thuật đạt không có nghĩa hồ sơ ra đề đã đủ.','',('Tên chủ đề đã được ánh xạ về họ/chương; vẫn cần rà ánh xạ.' if mapping else 'Tên chủ đề hiện theo nhãn trích xuất, chưa gộp thành họ/chương; không coi các tên gần nhau là các chương độc lập.'),'','## Mục lục','']
 for n,name in enumerate(sorted(groups),1):lines.append(f'{n}. {name}')
 for n,(topic,rows) in enumerate(sorted(groups.items()),1):
  refs={r['ref'] for r in rows};patterns={};parts=sorted({r['part'] for r in rows});grades=sorted({str(r.get('grade')) for r in rows});classes={}
  lines+=['',f'## {n}. {topic}','',f'Lớp được gắn nhãn: {", ".join(grades)}. Phần xuất hiện: {", ".join(parts)}.','', '| Nguồn / phần | Đề có chủ đề / tổng đề | Câu phân biệt | Ý/hàng | Thấp | Vừa | Cao | Chưa rõ |','|---|---:|---:|---:|---:|---:|---:|---:|']
  for cls,label in [('official','Chính thức'),('provincial_third_party','Tỉnh/trường')]:
   classrows=[r for r in rows if r['evidence_class']==cls];classes[cls]={'distinct_papers':len({r['paper_id'] for r in classrows}),'rows':len(classrows),'parts':{}}
   for part in parts:
    rs=[r for r in classrows if r['part']==part];levels=collections.Counter(r.get('discrimination') for r in rs);counts={'papers':len({r['paper_id'] for r in rs}),'questions':len({(r['paper_id'],r['part'],r['idx']) for r in rs}),'rows':len(rs),'discrimination':{str(k):v for k,v in levels.items()}};classes[cls]['parts'][part]=counts
    lines.append('| '+label+' / '+part+' | '+f'{counts["papers"]}/{den[cls]} | {counts["questions"]} | {len(rs)} | '+' | '.join(str(levels[k]) for k in ['low','medium','high',None])+' |')
   related=[]
   for pattern in p.get('profiles_by_class',{}).get(cls,{}).get('patterns',[]):
    support=sorted(refs.intersection(pattern.get('refs',[])))
    if support:related.append({**pattern,'topic_support_refs':support})
   patterns[cls]=related
  lines+=['','Số câu/ý và số đề là các đơn vị khác nhau; một câu tích hợp có thể thuộc nhiều chủ đề. Thấp/vừa/cao là nhận định phân hóa, chưa phải NB/TH/VD hay kết quả đo trên học sinh.','', '**Nội dung và cách hỏi quan sát được:**','']
  for cls,label in [('official','Chính thức'),('provincial_third_party','Tỉnh/trường')]:
   rs=[r for r in rows if r['evidence_class']==cls]
   if not rs:lines.append('- '+label+': chưa có quan sát trong mẫu.');continue
   seen=set()
   for r in rs:
    signature=(r['given'],r['task'],str(r['reasoning']))
    if signature in seen:continue
    seen.add(signature);reasoning=' → '.join(r['reasoning']) if isinstance(r['reasoning'],list) else r['reasoning'];combines='; '.join(r.get('combines') or []) or 'chưa nêu'
    lines+=['- '+label+' / '+r['part']+': cho '+r['given']+' Yêu cầu: '+r['task'],'  Suy luận: '+str(reasoning)+' Kết hợp: '+combines+'. Nguồn độ khó: '+str(r.get('difficulty_source'))+'.']
    if r.get('evidence_uncertainty'):lines.append('  Giới hạn: '+str(r['evidence_uncertainty']))
  lines+=['','**Các dạng câu và cách tạo nhiễu:**','']
  for cls,label in [('official','Chính thức'),('provincial_third_party','Tỉnh/trường')]:
   for pat in patterns[cls]:lines.append('- '+label+' / '+str(pat.get('part_kind'))+': '+str(pat.get('construction'))+' Nhiễu: '+str(pat.get('wrong_options') or 'không áp dụng/chưa rõ'))
   if not patterns[cls]:lines.append('- '+label+': chưa có mẫu lặp được aggregate xác lập cho chủ đề này; xem mô tả từng câu phía trên.')
  lines+=['','**Đối chiếu ma trận và NB/TH/VD:**','']
  matched_defaults=[r for r in defaults['rows'] if r['topic']==topic]
  if mapping:
   if matched_defaults:
    for part in parts:
     ct=collections.Counter()
     for r in matched_defaults:
      if r['part_id']==part:ct[r['level']]+=r.get('count',0)
     lines.append('- Mặc định '+part+': '+(', '.join(k+'='+str(v) for k,v in sorted(ct.items())) or 'không có slot trong phần này')+'.')
   else:lines.append('- Họ chủ đề này chưa được ánh xạ vào một chương mặc định; cần xem kết luận audit trước khi đề xuất thêm.')
  else:lines.append('- Chưa hoàn tất ánh xạ chủ đề với chương mặc định; chưa công bố bảng so sánh NB/TH/VD.')
  lines+=[('- Phân bố NB/TH/VD: xem [bảng mức nhận thức]('+str(d/'LEVELS.md')+'). Đây là nhãn trên khái quát, chờ rà đề gốc; không quy đổi từ thấp/vừa/cao.' if (d/'levels.json').exists() else '- Phân bố NB/TH/VD của đề thật: chưa được gắn nhãn theo thang canonical. Không quy đổi từ thấp/vừa/cao.'),'', '**Câu mẫu mới:** chưa sinh và tự giải độc lập. Các mô tả phía trên là khái quát từ bằng chứng, không phải câu mẫu có thể đưa vào đề.','', '**Audit prototype theo chủ đề:** '+('xem audit môn đã xuất; chưa có bảng nối đầy đủ đến chủ đề này.' if (ROOT/'audit/prototypes'/f'{subject}.md').exists() else 'chưa hoàn tất chấm độc lập; số đo độ dài phương án hiện có không thay thế bước này.')]
  result.append({'topic':topic,'raw_topics':sorted({r['topic'] for r in rows}),'grades':grades,'classes':classes,'patterns_by_class':patterns,'support_refs':sorted(refs),'cognitive_level_status':'pending_canonical_rater','sample_status':'pending_original_generation_and_blind_resolve','prototype_status':'pending_topic_join'})
 lines+=['','## Phạm vi cần bổ sung','','Hồ sơ ra đề đầy đủ còn cần: phân bố nhận thức theo ma trận; câu mẫu mới với đáp án, lời giải, lỗi đằng sau từng nhiễu và kiểm tự giải độc lập; audit ma trận/prototype; các điều kiện câu chùm và tiên quyết cho từng dạng. Không dùng ví dụ app sinh làm bằng chứng tần suất.','']
 dump(d/'topics.json',{'schema_version':'research-topic-dossier-v1','subject':subject,'status':'incomplete_dossier','mapping_available':bool(mapping),'evidence_classes_separate':True,'topics':result})
 (d/'TOPICS.md').write_text('\n'.join(lines),encoding='utf-8');print('TOPICS',subject,len(result))

if __name__=='__main__':
 import sys
 for subject in sys.argv[1:] or SUBJECT_IDS:render(subject)

"""Owner-readable one-page notes, derived from accepted rows and aggregate observations."""
from common import *
import collections

def note(subject):
 d=ROOT/'profiles'/subject;rf=d/'rows.json';pf=d/'profile.compact.json'
 if not rf.exists() or not pf.exists():return
 data=load(rf);profile=load(pf);papers=data['papers'];by=collections.Counter(p['class'] for p in papers);verified=collections.Counter(p['class'] for p in papers if p.get('has_matched_key'));v=load(d/'verification.json') if (d/'verification.json').exists() else {};stats=profile.get('code_derived',{});structure=load(d/'paper-structures.json') if (d/'paper-structures.json').exists() else {};classes=profile.get('profiles_by_class',{});complete=set(classes)==set(by) and bool(by);holds=[]
 if not complete:holds.append('aggregate chưa đủ lớp bằng chứng')
 if len(structure.get('observations',[]))<len(papers):holds.append('cấu trúc câu chùm/thứ tự chưa đủ')
 if v.get('address_coverage_incomplete'):holds.append('còn địa chỉ thiếu/lệch')
 if v.get('refs_invalid'):holds.append('còn tham chiếu chưa khớp')
 if v.get('wrong_option_coverage_issues'):holds.append('phân tích nhiễu còn thiếu/lệch nhãn')
 if v.get('ten_word_overlap_count'):holds.append('còn cụm trùng chữ cần rà')
 if v.get('numeric_narrative_candidates'):holds.append('còn chữ số trong mô tả cần rà')
 if v.get('aggregate_input_current') is False:holds.append('aggregate chưa theo nguồn hiện tại')
 state='Đang hoàn thiện: '+', '.join(holds)+'.' if holds else 'Trích xuất và aggregate đã qua kiểm kỹ thuật; nhận định vẫn chờ giáo viên rà.'
 lines=['# Hồ sơ '+subject,'','**Hồ sơ ra đề chưa được nghiệm thu đầy đủ. Tình trạng từng thành phần được ghi bên dưới; có tệp kết quả không đồng nghĩa đã hoàn chỉnh.**','',state,'','[Đọc cách hỏi theo từng chủ đề]('+str(d/'TOPICS.md')+')','',f'**Bằng chứng:** chính thức {by["official"]} đề; tỉnh/trường {by["provincial_third_party"]} đề; {len(data["rows"])} câu/ý được gắn nhãn. Model EXTRACT: {data.get("model") or data.get("extraction_model")}. Hai nguồn được tổng hợp riêng.',f'Khóa khớp đã chấp nhận: chính thức {verified["official"]}/{by["official"]}, tỉnh/trường {verified["provincial_third_party"]}/{by["provincial_third_party"]}.','', '**Lớp kiến thức xuất hiện — số đề phân biệt:**','','| Nguồn / phần | Lớp 10 | Lớp 11 | Lớp 12 | Chưa rõ |','|---|---:|---:|---:|---:|']
 component_files=[('Audit ma trận',ROOT/'audit/matrices'/f'{subject}.md'),('Audit prototype',ROOT/'audit/prototypes'/f'{subject}.md'),('NB/TH/VD',d/'LEVELS.md'),('Câu mẫu mới',d/'SAMPLES.md')]
 components=['**Các phần của hồ sơ:**','']+['- ['+label+']('+str(path)+') — đã có bản, còn chờ rà.' if path.exists() else '- '+label+': đang bổ sung, chưa nghiệm thu.' for label,path in component_files]+['']
 lines[8:8]=components
 gp={(r['class'],r['part'],r['grade']):r['distinct_papers'] for r in stats.get('grade_presence',[])}
 for cls,part in sorted({(r['class'],r['part']) for r in stats.get('grade_presence',[])}):lines.append('| '+('Chính thức' if cls=='official' else 'Tỉnh/trường')+' / '+part+' | '+' | '.join(str(gp.get((cls,part,g),0))+'/'+str(by[cls]) for g in ['10','11','12','None'])+' |')
 lines+=['','Một đề có thể chứa nhiều lớp; không cộng các cột thành tổng đề. Nhãn lớp và độ phân hóa do model nhận định.','', '**Cách dựng câu và phân hóa:**','']
 for cls,label in [('official','Chính thức'),('provincial_third_party','Tỉnh/trường')]:
  prof=classes.get(cls)
  if not prof:continue
  moves=prof.get('discrimination_moves') or [];patterns=prof.get('patterns') or [];example=moves[0] if moves else patterns[0] if patterns else None
  if example:
   text=example.get('how_to_apply') or example.get('construction') or example.get('move') or '';lines.append('- '+label+': '+str(text))
  elif prof.get('easy_vs_hard'):
   contrast=prof['easy_vs_hard'][0];lines.append('- '+label+': '+str(contrast.get('hard',''))+' (Đối sánh trong mẫu; chưa khẳng định là dạng lặp giữa nhiều đề.)')
 if by['official']<2:lines+=['','Nguồn chính thức ít: mô tả quan sát, chưa suy ra quy luật tần suất phổ quát.']
 lines+=['','**Mức phân hóa do model nhận định:**','','| Nguồn | Thấp | Vừa | Cao | Chưa phán đoán |','|---|---:|---:|---:|---:|']
 for cls,label in [('official','Chính thức'),('provincial_third_party','Tỉnh/trường')]:
  levels=collections.Counter(r.get('discrimination') for r in data['rows'] if r['evidence_class']==cls)
  lines.append('| '+label+' | '+' | '.join(str(levels.get(level,0)) for level in ['low','medium','high',None])+' |')
 lines+=['','Đếm theo câu/ý đã gắn nhãn; đây là độ phức tạp suy luận được nhận định, chưa phải độ phân hóa đo từ bài làm học sinh. Các cách dựng ở trên không mặc nhiên đều đạt mức cao.','', '**Dữ kiện thuộc lòng được dùng thế nào:**','','| Nguồn | Hỏi trực tiếp | Cho làm gợi ý | Cần trong suy luận | Không dùng |','|---|---:|---:|---:|---:|']
 for cls,label in [('official','Chính thức'),('provincial_third_party','Tỉnh/trường')]:
  facts=stats.get('fact_use_counts',{}).get(cls,{})
  lines.append('| '+label+' | '+' | '.join(str(facts.get(use,0)) for use in ['asked for directly','given as a cue','needed in reasoning','none'])+' |')
 lines+=['','Các cột đếm câu/ý trong mẫu đã phân tích, không phải tần suất học sinh nhớ hoặc quên.','', '**Phương án nhiễu:**','']
 distr=stats.get('distractors',{})
 if not distr:lines.append('Không có số liệu phương án lựa chọn để báo tỷ lệ.')
 for cls,counts in distr.items():
  a,b,u=counts.get('identifiable',0),counts.get('not_identifiable',0),counts.get('unverified',0);den=a+b;ratio=f'{100*a/den:.1f}%' if den else 'chưa đủ để tính';lines.append('- '+('Chính thức' if cls=='official' else 'Tỉnh/trường')+f': liên hệ được một kiểu nhầm cụ thể ở {a}/{den} phương án đã phán đoán ({ratio}); chưa xác minh {u}.')
 unrated=collections.Counter(r['evidence_class'] for r in data['rows'] if r.get('discrimination') is None)
 lines+=['',f'Chưa phán đoán được mức phân hóa ở chính thức {unrated["official"]}, tỉnh/trường {unrated["provincial_third_party"]} slot. Xem evidence_uncertainty trong từng hàng để biết ngữ cảnh/hình/bảng còn thiếu.']
 lines+=['','Đây là độ hợp lý của lỗi do model đánh giá, chưa phải lỗi thường gặp được đo trên học sinh. Không suy rộng tỷ lệ của phần đã xác nhận khóa sang các đề chưa có khóa. Mục chưa xác minh có thể chứa lựa chọn chưa biết đúng/sai, không phải số phương án sai đã xác nhận.','', '**Câu chùm và thứ tự:**','']
 obs=structure.get('observations',[])
 if obs:
  multi=collections.Counter(p['class'] for p in obs if any(g['scope'] in ['multiple_questions','cross_parts'] for g in p['structure']['shared_stimuli']));lines.append(f'Đã đọc cấu trúc {len(obs)}/{len(papers)} đề; có chùm nhiều câu/xuyên phần được quan sát ở chính thức {multi["official"]}, tỉnh/trường {multi["provincial_third_party"]}. Các ý TF trong một câu được giữ riêng với chùm nhiều câu.')
  for r in structure.get('part_order_observations',[]):lines.append('- '+('Chính thức' if r['class']=='official' else 'Tỉnh/trường')+': '+' → '.join(r['order'])+f', quan sát ở {r["distinct_papers"]} đề.')
 else:lines.append('Đang bổ sung cấu trúc; chưa kết luận thứ tự cố định hay vị trí chùm từ thống kê chủ đề.')
 lines+=['','Thứ tự quan sát không tự trở thành luật cố định. Xem [audit cấu trúc](../../audit/block-structure.md) để phân biệt canonical, hoán vị và vị trí tự do.','', '**Truy nguyên:** [rows](rows.json), [phân bố](distributions.json), [compact](profile.compact.json), [cấu trúc từng đề](paper-structures.json), [kiểm định](verification.json).','']
 (d/'NOTE.md').write_text('\n'.join(lines),encoding='utf-8')
if __name__=='__main__':
 import sys
 for subject in sys.argv[1:] or [p.name for p in (ROOT/'profiles').iterdir() if p.is_dir()]:note(subject)

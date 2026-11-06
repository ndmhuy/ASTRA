#!/usr/bin/env python3
"""One row per transcribed paper. No model. Run from corpus root.
Evidence is a paper, never a directory/README/download file; references excluded.
Completeness checks retain source uncertainty rather than infer from file size alone.
"""
import csv,json,os,re,subprocess,collections
from pathlib import Path
files=subprocess.run(['git','ls-files','--cached','--others','--exclude-standard'],capture_output=True,text=True,check=True).stdout.splitlines()
files=sorted(set(files));rows=[]
for de in [f for f in files if re.match(r'transcriptions/[^/]+/.*de\.md$',f)]:
 parts=de.split('/');subj=parts[1];d=Path(de).parent;bucket=parts[2]
 kind='reference' if 'reference' in bucket else 'provincial' if 'provincial' in bucket else 'paper' if 'paper' in bucket else bucket
 cls={'paper':'official','reference':'format_only','provincial':'provincial_third_party'}.get(kind,kind)
 year=(re.search(r'20\d\d',bucket) or [None])[0];status=(d/'STATUS.md').read_text(encoding='utf-8',errors='replace') if (d/'STATUS.md').exists() else ''
 st=json.loads((d/'structure.json').read_text(encoding='utf-8')) if (d/'structure.json').exists() else {}
 stopped=bool(re.search(r'\bstop(?:ped)?\b|dừng|missing page|thiếu trang|lacks',status[:600],re.I))
 missing=st.get('missing_pages') or [];unreadable=st.get('unreadable_count',0) or 0
 audit=json.loads((d/'AUDIT-20261102.json').read_text(encoding='utf-8')) if (d/'AUDIT-20261102.json').exists() else {}
 excluded=bool(audit.get('excluded_from_analysis'))
 if audit:stopped=False
 incomplete=bool(audit.get('failures')) or bool(audit.get('qa_content_failures',audit.get('qa_failures'))) or stopped or bool(missing) or bool(unreadable) or Path(de).stat().st_size<1500
 haskey=((d/'key.json').exists() and isinstance(json.loads((d/'key.json').read_text(encoding='utf-8')),dict)) or (d/'key.md').exists()
 # Official keys may be stored beside the paper, under the exact year/code.
 if not haskey and year:
  kp=d.parent/(year+'-answer')/'key.json';code=st.get('ma_de')
  if kp.exists() and code:
   kd=json.loads(kp.read_text(encoding='utf-8'));haskey=isinstance(kd.get('ma_de'),dict) and str(code) in kd['ma_de']
 rows.append({'subject':subj,'class':cls,'year':year,'path':de,'bytes':Path(de).stat().st_size,'has_key':haskey,'status_flag':'excluded' if excluded else 'incomplete' if incomplete else 'ok','usable_as_content_evidence':kind in ['paper','provincial'] and not incomplete and not excluded,'missing_pages':json.dumps(missing,ensure_ascii=False),'unreadable_count':unreadable})
down=collections.Counter(f.split('/')[1].replace('2026-provincial-','') for f in files if f.startswith('official/2026-provincial-') and f.lower().endswith(('.pdf','.jpg','.png','.docx')))
extra=collections.Counter(f.split('/')[2] for f in files if f.startswith('official/2026-papers-extra/') and len(f.split('/'))>3 and f.lower().endswith(('.pdf','.jpg','.png')))
with open('registry/papers.csv','w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(sorted(rows,key=lambda r:(r['subject'],r['class'],r['path'])))
s=collections.defaultdict(collections.Counter)
for r in rows:
 if r['usable_as_content_evidence']:s[r['subject']][r['class']]+=1
 else:s[r['subject']]['unusable']+=1
out=['# Sổ dữ liệu đề','','Sinh tự động bằng `registry/build.py`. Đề app sinh và đề tham khảo không là bằng chứng nội dung. Hai mã hoán vị không tự động là hai đề độc lập; xem kiểm trùng của đợt phân tích. Cờ dùng được chỉ nói về độ đầy đủ phiên âm, không phải giáo viên đã duyệt.','','| Môn | Chính thức dùng được | Đề tỉnh dùng được | Không dùng (tham khảo, dở) | File đề tỉnh đã tải | File đề ngoại ngữ thêm |','|---|---|---|---|---|---|']
for n in sorted(set(s)|set(down)|set(extra)):
 out.append(f"| {n} | {s[n]['official']} | {s[n]['provincial_third_party']} | {s[n]['unusable']} | {down.get(n,0)} | {extra.get(n,0)} |")
Path('registry/README.md').write_text('\n'.join(out)+'\n',encoding='utf-8');print('\n'.join(out))

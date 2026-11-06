from common import *
from addresses import questions
from registry_shape import option_labels_for
from option_measure import source_options
import importlib.util,sys,collections

def latex_support(text):
 path=product_root()/'exam_generator/latex/scripts.py';spec=importlib.util.spec_from_file_location('corpus_script_support',path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m.build_for_text(text)
def stage5():
 defaults=load(ROOT/'audit/outputs/defaults-snapshot.json')['subjects'];outcomes={}
 for subject,sid in [('tieng-nga','TiengNga'),('tieng-nhat','TiengNhat'),('tieng-han','TiengHan')]:
  d=ROOT/'prototypes'/subject;d.mkdir(parents=True,exist_ok=True);sources=[]
  for source in (ROOT/'transcriptions'/subject).glob('*paper*/de.md'):
   st=source.with_name('STATUS.md').read_text(encoding='utf-8');structure=load(source.with_name('structure.json'))
   audit=load(source.with_name('AUDIT-20261102.json')) if source.with_name('AUDIT-20261102.json').exists() else {}
   form_only=bool(audit.get('form_reference_eligible')) and structure.get('pages_present')==structure.get('pages_expected') and structure.get('total_cau')==sum(p['count'] for p in defaults[sid]['parts'])
   if not structure.get('missing_pages') and (form_only or (not re.search(r'STOPPED|incomplete|thiếu trang',st[:650],re.I) and not structure.get('unreadable_count'))):sources.append(source)
  if not sources:
   msg='Chưa có đề thật đầy đủ, đọc được và qua lượt hai; chưa sinh mẫu để tránh đoán form/độ khó của trang thiếu. Chờ chủ app bổ sung nguồn; xem phiên âm và STATUS.'
   (d/'NOTE.md').write_text('# '+subject+'\n\n'+msg+'\n',encoding='utf-8');outcomes[subject]={'status':'blocked_missing_usable_paper'};continue
  source=sources[0];source_audit=load(source.with_name('AUDIT-20261102.json'));source_images=[]
  call_dir=ROOT/'audit/outputs/calls'/('ocr-'+subject+'--'+source_audit['input']['slug'])
  for meta in sorted(call_dir.glob('*.meta.json')):
   data=load(meta)
   if data['returncode']==0:source_images=data.get('images',[])
  layout=defaults[sid];name='PROTO_thptqg_'+subject+'_corpus_20261102';payload={'subject':layout['display_name'],'registered_layout':layout,'evidence_paper':source.read_text(encoding='utf-8'),'evidence_structure':load(source.with_name('structure.json')),'de_name':name,'source_use':'form and approximate difficulty only; no frequency claim','source_uncertainties':source_audit.get('source_readability_resolution',{}).get('remaining_unreadable_addresses',[])}
  raw=d/'generation.json'
  def generate():
   x=ask('new-prototype-'+subject,(ROOT/'audit/prompts/NEW_PROTOTYPE.txt').read_text()+'\n'+json.dumps(payload,ensure_ascii=False),images=source_images,timeout=1100)
   expected=sum(p['count'] for p in layout['parts']);qs=questions(x['body_tex'],strip_tex_comments=True);keys=x['answers']['questions']
   wanted={(p['part_id'],i) for p in layout['parts'] for i in range(1,p['count']+1)}
   if {(q['part'],q['idx']) for q in qs}!=wanted or {(q['part'],q['idx']) for q in keys}!=wanted:raise ValueError('NEW_PROTOTYPE_ADDRESS_SET')
   for q in keys:
    labels=option_labels_for(x['answers']['exam_type'],sid,q['part'])
    if len(q['slots'])!=1 or q['slots'][0].get('sub') is not None or q['slots'][0]['answer'] not in (labels or ()):raise ValueError('NEW_PROTOTYPE_KEY_SHAPE')
   for q in qs:
    labels=option_labels_for(x['answers']['exam_type'],sid,q['part'])
    if not labels or source_options(q['text'],labels) is None:raise ValueError('NEW_PROTOTYPE_OPTIONS_LAYOUT')
   if len(qs)!=expected or len(keys)!=expected or {q['idx'] for q in qs}!={q['idx'] for q in keys}:raise ValueError('NEW_PROTOTYPE_COUNT')
   label=layout['question_label']
   prefix=(label['word']+(' ' if label['space'] else '')) if label['word'] is not None else ''
   pattern=r'\\noindent\s*\\textbf\{'+re.escape(prefix)+r'(\d+)'+re.escape(label['end'])+r'\}'
   if len(re.findall(pattern,x['body_tex']))!=expected:raise ValueError('NEW_PROTOTYPE_REGISTERED_QUESTION_LABEL')
   starts=re.findall(r'LECTURING-BLOCK:\s*(\w+)',x['body_tex']);blocks=[b['kind'] for p in layout['parts'] for b in p['blocks']]
   if starts!=blocks:raise ValueError('NEW_PROTOTYPE_BLOCK_ORDER')
   marks=list(re.finditer(r'LECTURING-BLOCK:\s*(\w+)',x['body_tex']));block_specs=[b for p in layout['parts'] for b in p['blocks']]
   for i,mark in enumerate(marks):
    end=marks[i+1].start() if i+1<len(marks) else len(x['body_tex'])
    if len(questions(x['body_tex'][mark.end():end],strip_tex_comments=True))!=block_specs[i]['count']:raise ValueError('NEW_PROTOTYPE_BLOCK_COUNT')
   return x
  x=load(raw) if raw.exists() else twice('new-prototype-'+subject,generate)
  if x is None:outcomes[subject]={'status':'generation_failed_twice'};continue
  dump(raw,x)
  verify=d/'independent-resolve.json'
  def resolve():
   v=ask('resolve-new-'+subject,(ROOT/'audit/prompts/VERIFY_NEW_PROTOTYPE.txt').read_text()+'\n'+re.sub(r'(?m)(?<!\\)%[^\n]*','',x['body_tex']),timeout=1000)
   if len(v['answers'])!=len(x['answers']['questions']) or {(a['part'],a['idx']) for a in v['answers']}!={(q['part'],q['idx']) for q in x['answers']['questions']}:raise ValueError('RESOLVE_NEW_ADDRESS_SET')
   return v
  v=load(verify) if verify.exists() else twice('resolve-new-'+subject,resolve)
  if v is None:outcomes[subject]={'status':'independent_resolve_failed_twice'};continue
  dump(verify,v);published={(q['part'],q['idx']):q['slots'][0]['answer'] for q in x['answers']['questions']};disagreements=[a for a in v['answers'] if published.get((a['part'],a['idx']))!=a['answer']]
  # A disagreement is reported, never a silent key overwrite.
  support=latex_support(x['body_tex']+'\nĐề luyện tập chờ giáo viên duyệt');preamble_lines=support.lines if hasattr(support,'lines') else support.preamble_lines
  preamble='\\documentclass[12pt,a4paper]{article}\n'+'\n'.join(preamble_lines)+'\n\\usepackage{amsmath,amssymb,graphicx,enumitem}\n\\usepackage[margin=1.8cm]{geometry}\n\\setlength{\\parindent}{0pt}\n\\setlength{\\parskip}{5pt}\n\\begin{document}\n'
  header='\\begin{center}\\textbf{ĐỀ LUYỆN TẬP — '+layout['display_name']+'}\\\\Chờ giáo viên duyệt\\\\Thời gian làm bài: '+str(layout['duration_minutes'])+' phút\\end{center}\n'
  tex=d/(name+'.tex');tex.write_text(preamble+header+x['body_tex']+'\n\\end{document}\n',encoding='utf-8');dump(d/(name+'_Answers.json'),x['answers'])
  engine=support.engine;logs=[];ok=False
  for n in range(2):
   r=subprocess.run([engine,'-interaction=nonstopmode','-halt-on-error','-no-shell-escape','-output-directory',str(d),str(tex)],capture_output=True,text=True,cwd=d,timeout=180);logs.append({'pass':n+1,'returncode':r.returncode});(d/f'compile-{n+1}.log').write_text(r.stdout+r.stderr,encoding='utf-8')
   if r.returncode or 'Missing character:' in r.stdout+r.stderr:continue
   ok=True
  pdf=tex.with_suffix('.pdf');renders=[]
  if ok and pdf.exists():
   rend=d/'rendered';rend.mkdir(exist_ok=True);run(['pdftoppm','-r','110','-png',pdf,rend/'page'],timeout=180);renders=sorted(str(p) for p in rend.glob('page-*.png'))
  # Copy avoidance check against every real input, lexical only; no proof of semantic noncopying.
  sourcewords=re.findall(r'\w+',source.read_text(encoding='utf-8').lower());newwords=re.findall(r'\w+',x['body_tex'].lower());n=10;ngrams=lambda ws:{tuple(ws[i:i+n]) for i in range(len(ws)-n+1)};overlap=len(ngrams(sourcewords)&ngrams(newwords))
  compact_chars=lambda text:''.join(re.findall(r'\w',re.sub(r'\\[A-Za-z]+','',text).lower()))
  sourcechars=compact_chars(source.read_text(encoding='utf-8'));newchars=compact_chars(x['body_tex']);width=40
  sourcegrams={sourcechars[i:i+width] for i in range(max(0,len(sourcechars)-width+1))};char_overlap=len(sourcegrams&{newchars[i:i+width] for i in range(max(0,len(newchars)-width+1))})
  notes=['# '+subject,'','**Chờ giáo viên duyệt.** Không ai trong nhóm đọc ngôn ngữ này ở trình độ đề thi; kiểm model không phải duyệt giáo viên.','', 'Nguồn hình thức/độ khó: '+str(source),'Model tạo và lượt giải độc lập: '+MODEL+' (hai context riêng, cùng model).',f'Bất đồng khóa: {len(disagreements)}; câu chưa giải được: {v.get("unanswerable",[])}; trùng mười từ với bản nguồn: {overlap}; trùng chuỗi bốn mươi ký tự đã chuẩn hóa: {char_overlap}.',f'Compile: {ok}; engine: {engine}; trang render: {len(renders)}. Còn cần người điều phối mở từng trang để kiểm hệ chữ.','']+['- '+a for a in x.get('source_form_notes',[]) + x.get('doubts',[]) + v.get('limits',[])];(d/'NOTE.md').write_text('\n'.join(notes)+'\n',encoding='utf-8')
  result={'status':'pending_teacher_review' if ok else 'compile_failed_pending_repair','key_disagreements':disagreements,'resolve_issues':v.get('language_issues',[]),'compile_ok':ok,'compile_passes':logs,'rendered':renders,'visual_reviewed':False,'source':str(source),'ten_word_overlap_count':overlap,'forty_character_overlap_count':char_overlap};dump(d/'verification.json',result);outcomes[subject]=result
 # Explicitly no Chinese paper without real evidence.
 gap=ROOT/'audit/gaps/tieng-trung.md';gap.parent.mkdir(parents=True,exist_ok=True);gap.write_text('# Tiếng Trung\n\nChờ chủ app cung cấp đề thật. Không tạo prototype; khóa đáp án không thay thế đề.\n',encoding='utf-8');dump(ROOT/'audit/outputs/new-prototypes.json',outcomes)
if __name__=='__main__':stage5()

from common import *
import argparse,shutil,collections
from PIL import Image
P=ROOT/'audit/prompts'
OCR_MODEL='gpt-6-luna'
VERIFY_MODEL='gpt-6-luna'
def make_manifest():
 tasks=[];selection=[]
 # Five distinct provincial authorities, with geographical spread; fallback candidates remain listed.
 preferred={'hoa-hoc':['ca-mau','quang-ninh','quang-tri','tp-hue','da-nang'], 'sinh-hoc':['ca-mau','lang-son','thanh-hoa','tp-hue','ha-tinh'], 'lich-su':['an-giang','bac-ninh','can-tho','dien-bien','gia-lai'], 'dia-li':['thai-nguyen','da-nang','gia-lai','hai-phong','ca-mau']}
 for s,provs in preferred.items():
  dirs=sorted((ROOT/f'official/2026-provincial-{s}').glob('*/paper.docx'));chosen=[]
  for prov in provs:
   match=next((p for p in dirs if prov in p.parent.name and p not in chosen),None)
   if match:chosen.append(match)
  for p in dirs:
   selected=p in chosen;selection.append({'subject':s,'path':str(p.relative_to(ROOT)),'selected':selected,'reason':'Đa dạng tỉnh; ưu tiên đề sở, một lần thi mỗi tỉnh.' if selected else 'Ngoài mẫu năm tỉnh đa vùng của đợt này; không kết luận không đọc được.'})
  tasks += [{'subject':s,'kind':'provincial','year':2026,'source':str(p.relative_to(ROOT)),'slug':p.parent.name} for p in chosen]
 existing={p.parent.name for p in (ROOT/'transcriptions/toan/2026-provincial').glob('*/de.md')};need=max(0,20-len(existing));math=[]
 for p in sorted((ROOT/'official/2026-provincial-toan').glob('*/paper.pdf')):
  name=p.parent.name
  if name in existing or any(w in name for w in ['tham-khao','chinh-thuc']):continue
  # Prefer provincial authorities, spread once before additional rounds.
  if 'so-gddt' in name:math.append(p)
 # geographic diversity: prioritize a name not sharing province suffix with those selected
 uniq=[];seen=set()
 for p in math:
  tail=p.parent.name.split('so-gddt-')[-1]
  if tail not in seen:seen.add(tail);uniq.append(p)
 for p in (ROOT/'official/2026-provincial-toan').glob('*/paper.pdf'):
  selection.append({'subject':'toan','path':str(p.relative_to(ROOT)),'selected':p in uniq[:need],'reason':'Đã phiên âm trước đợt này' if p.parent.name in existing else 'Chọn đủ tối đa hai mươi đề tỉnh, ưu tiên sở đa tỉnh; loại đề tham khảo/chính thức khỏi lớp tỉnh.' if p in uniq[:need] else 'Không chọn đợt này; giữ nguyên nguồn.'})
 tasks += [{'subject':'toan','kind':'provincial','year':2026,'source':str(p.relative_to(ROOT)),'slug':p.parent.name} for p in uniq[:need]]
 for s,stem in [('toan','toan-2025-ma-0101'),('vat-li','vat-li-2025-ma-0201'),('hoa-hoc','hoa-hoc-2025-ma-0301')]:
  tasks.append({'subject':s,'kind':'paper','year':2025,'source':f'official/2025-web/{stem}.pdf','slug':stem})
 for s in ['tieng-nga','tieng-nhat','tieng-han']:
  src=f'official/2026-papers-extra/{s}'
  tasks.append({'subject':s,'kind':'paper','year':2026,'source':src,'slug':'ma-1225' if s=='tieng-nga' else 'ma-1603' if s=='tieng-nhat' else 'ma-1725'})
 dump(ROOT/'audit/outputs/selection.json',selection);dump(ROOT/'audit/outputs/stage1-manifest.json',tasks);return tasks

def prepare(t):
 ident=t['subject']+'--'+t['slug'];src=ROOT/t['source'];w=ROOT/'audit/work'/ident;w.mkdir(parents=True,exist_ok=True)
 if src.is_dir():
  if t['subject']=='tieng-nhat':src=src/(t['slug']+'.pdf')
  else:
   images=sorted([p for p in src.iterdir() if p.suffix.lower() in ['.jpg','.png'] and 'page-' in p.name],key=lambda p:p.name)
   return w,images,'Photo images. Filenames are printed page identities. Social-post extra is excluded.',None
 pdf=src
 if src.suffix=='.docx':
  pdf=w/'paper.pdf'
  if not pdf.exists():run(['/opt/homebrew/bin/soffice','-env:UserInstallation=file://'+str(ROOT/'audit/work/lo'),'--headless','--convert-to','pdf','--outdir',w,src],timeout=120)
 text=run(['pdftotext','-layout',pdf,'-']);(w/'text.txt').write_text(text,encoding='utf-8');pages=text.split('\f');n=int(re.search(r'^Pages:\s*(\d+)',run(['pdfinfo',pdf]),re.M)[1])
 # Attach first eight plus candidate key-table pages. The model sees all text and can request absent exam pages.
 selected=set(range(1,min(n,8)+1))
 for i,p in enumerate(pages,1):
  if i<=n and re.search(r'(BẢNG\s*ĐÁP\s*ÁN|ĐÁP\s*ÁN\s*(?:MÃ|PHẦN|ĐỀ)|HƯỚNG DẪN CHẤM)',p,re.I): selected.add(i)
 selected=sorted(selected)[:13]
 images=[]
 for i in selected:
  found=list(w.glob(f'p{i}-*.jpg'))
  if not found:run(['pdftoppm','-f',i,'-l',i,'-r','140','-jpeg','-jpegopt','quality=85',pdf,w/f'p{i}'],timeout=90);found=list(w.glob(f'p{i}-*.jpg'))
  images+=found
 return w,images,('\nPAGE MAP: '+', '.join(f'image {j+1}=PDF page {i}' for j,i in enumerate(selected))+'\nPDF has '+str(n)+' pages.\nALL EXTRACTED TEXT:\n'+text[:160000]),pdf

def include_key_window(data):
 pages=data.get('key_pages') or [];solutions=data.get('solutions_from_page')
 if not pages or not isinstance(solutions,int):return
 start=min(pages)
 if solutions>=start:data['key_pages']=list(range(start,solutions+1))

def process(t, *, update_checksums=True, auto_commit=True):
 ident=t['subject']+'--'+t['slug']; dest=ROOT/'transcriptions'/t['subject']/(str(t['year'])+'-'+t['kind'])
 if t['kind']=='provincial':dest/=t['slug']
 elif (dest/'de.md').exists():dest=dest.parent/(str(t['year'])+'-paper-web-'+t['slug'])
 # Existing audit records are checkpoints, including quality-stopped records.
 # Only quota/auth stops from the interrupted batch may be resumed.
 if (dest/'AUDIT-20261102.json').exists():print('SKIP audited',ident,flush=True);return
 global_stop=ROOT/'audit/outputs/GLOBAL-MODEL-STOP.json'
 if global_stop.exists():print('STOP global model prerequisite',ident,flush=True);return
 stopped=[]
 for stage in ('ocr-'+ident,'verify-full-'+ident):
  fp=ROOT/'audit/outputs/stops'/f'{stage}.json'
  if fp.exists():
   record=load(fp)
   if not record.get('resolved'):stopped.extend(record.get('errors',[]))
 if stopped and not all(re.search(r'usage limit|rate limit|quota|authentication failed|unauthorized',e,re.I) for e in stopped):
  print('SKIP prior non-quota stop',ident,flush=True);return
 if stopped:print('RESUME prior quota/auth stop',ident,flush=True)
 print('START',ident,flush=True)
 prepared=twice('prepare-'+ident,lambda:prepare(t))
 if prepared is None:return
 w,images,text,pdf=prepared
 data=load(w/'first.json') if (w/'first.json').exists() else twice('ocr-'+ident,lambda:ask('ocr-'+ident,(P/'OCR.txt').read_text(encoding='utf-8')+'\nSOURCE META:\n'+json.dumps(t,ensure_ascii=False)+'\n'+text,images,timeout=1000,model=OCR_MODEL))
 if data is None:return
 include_key_window(data)
 dump(w/'first.json',data)
 first_model='unknown (cached first-pass model not recorded)'
 metas=sorted((ROOT/'audit/outputs/calls'/('ocr-'+ident)).glob('*.meta.json'))
 successful=[load(m) for m in metas if load(m).get('returncode')==0]
 if successful:first_model=successful[-1]['model']
 if not successful and (w/'first.json').exists():
  prior=sorted((ROOT/'audit/outputs/calls'/('ocr-'+ident)).glob('*.meta.json'))
  prior_ok=[load(m) for m in prior if load(m).get('returncode')==0]
  if prior_ok:first_model=prior_ok[-1].get('model',first_model)
 dump(w/'first.meta.json',{'model':first_model})
 # A separate subscription context rereads the two densest pages. Same model explicitly declared.
 hard=data.get('hard_pages') or data.get('exam_pages',[])[:2]
 verify_images=[]
 for i in sorted(set(data.get('exam_pages',[]) + data.get('key_pages',[]))) or hard[:2]:
  if pdf:
   found=list(w.glob(f'p{i}-*.jpg'))
   if not found:run(['pdftoppm','-f',i,'-l',i,'-r','160','-jpeg',pdf,w/f'p{i}']);found=list(w.glob(f'p{i}-*.jpg'))
   verify_images+=found
  elif 1<=i<=len(images):verify_images.append(images[i-1])
 ver=twice('verify-full-'+ident,lambda:ask('verify-full-'+ident,(P/'VERIFY_OCR.txt').read_text(encoding='utf-8')+'\nTRANSCRIPT:\n'+data['de_md'],verify_images,timeout=800,model=VERIFY_MODEL))
 if ver is None:return
 md=data['de_md']
 for x in ver.get('disagreements',[]):
  if x.get('settled_by_image') and x.get('before') and 'HẾT' not in x['before'] and md.count(x['before'])==1:md=md.replace(x['before'],x['after'],1)
 failures=[]
 if not ver.get('pass'):failures.append('Lượt hai chưa đạt')
 if ver.get('missing_figures'):failures.append('Lượt hai phát hiện thiếu hình')
 if data.get('missing_pages'):failures.append('Thiếu trang: '+str(data['missing_pages']))
 if data['structure'].get('unreadable_count',0) or ver.get('unreadable'):failures.append('Có chỗ không đọc được')
 dest.mkdir(parents=True,exist_ok=True)
 for f in data.get('figures',[]):
  page=f['page'];fp=dest/f['file'];fp.parent.mkdir(exist_ok=True,parents=True)
  if pdf:impath=next(iter(w.glob(f'p{page}-*.jpg')),None)
  else:impath=images[page-1] if 1<=page<=len(images) else None
  if not impath:failures.append('Thiếu ảnh gốc cho hình '+f['file']);continue
  im=Image.open(impath);b=f['box'];box=tuple(round(v*dim/1000) for v,dim in zip(b,[im.width,im.height,im.width,im.height]))
  if box[2]<=box[0] or box[3]<=box[1] or box[0]<0 or box[1]<0 or box[2]>im.width or box[3]>im.height:failures.append('Khung cắt không hợp lệ');continue
  im.crop(box).save(fp)
 if not md.startswith('status:'):md='status: ocr-draft\n'+md
 (dest/'de.md').write_text(md,encoding='utf-8')
 st=data['structure'];st['subject']=t['subject'];st['figures']=data.get('figures',[]);st['figure_count']=len(st['figures']);st['missing_pages']=data.get('missing_pages') or [];dump(dest/'structure.json',st)
 if data.get('key') is not None:dump(dest/'key.json',data['key'])
 source=srcsource=ROOT/t['source'];sourcefile=source.parent/'source.json' if source.is_file() else source/'source.json'
 if sourcefile.exists():shutil.copyfile(sourcefile,dest/'source.json')
 else:dump(dest/'source.json',{'path':t['source'],'provenance_note':'See original source README; third-party copy. No new download.','sha256':hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None})
 status=f'Transcribed by {first_model}, 2026-11-02; second pass separate fresh context by {VERIFY_MODEL}; teacher verification no. Third-party copy; private internal evidence only.\n\n'
 status+='## '+('STOPPED / incomplete' if failures else 'OCR draft, second pass completed')+'\n'
 status+='\n'.join('- '+x for x in failures or ['Không phát hiện sai khác chưa giải quyết trong lượt hai.'])+'\n\n'
 status+='Route: '+('docx -> LibreOffice PDF -> text + rendered images' if str(t['source']).endswith('.docx') else 'source PDF/photo -> text + rendered images')+'\n'
 status+='\nSecond-pass pages: '+str(hard[:2])+'; checked addresses: '+str(ver.get('checked_addresses'))+'\n'
 status+='\n'+json.dumps({'notes':data.get('notes'), 'second_pass':ver,'key_pages':data.get('key_pages'),'solutions_from_page':data.get('solutions_from_page')},ensure_ascii=False,indent=2)+'\n'
 (dest/'STATUS.md').write_text(status,encoding='utf-8');dump(dest/'AUDIT-20261102.json',{'input':t,'verification':ver,'failures':failures,'model':first_model,'verification_model':VERIFY_MODEL,'calls':str(ROOT/'audit/outputs/calls'/('ocr-'+ident))})
 # Keep shared index/checksum updates opt-in so parallel corpus lanes stay isolated.
 paths=[str(dest.relative_to(ROOT))]
 if update_checksums:
  sums=ROOT/'SHA256SUMS.txt';lines=sums.read_text(encoding='utf-8').splitlines() if sums.exists() else []
  existing={l.split('  ',1)[1]:l for l in lines if '  ' in l}
  for p in dest.rglob('*'):
   if p.is_file():existing[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT))
  sums.write_text('\n'.join(existing[k] for k in sorted(existing))+'\n',encoding='utf-8')
  paths.append('SHA256SUMS.txt')
 if auto_commit:
  run(['git','add',str(dest.relative_to(ROOT))],cwd=ROOT)
  if update_checksums:run(['git','add','SHA256SUMS.txt'],cwd=ROOT)
  run(['git','commit','--only','-m','corpus: transcribe '+t['subject']+' '+t['slug'],'--',*paths],cwd=ROOT)
 print('DONE',ident,'failures',failures,flush=True)
def reverify(t,extra_key_pages=()):
 ident=t['subject']+'--'+t['slug']; dest=ROOT/'transcriptions'/t['subject']/(str(t['year'])+'-'+t['kind'])
 if t['kind']=='provincial':dest/=t['slug']
 elif (dest/'de.md').exists():dest=dest.parent/(str(t['year'])+'-paper-web-'+t['slug'])
 w,_,_,pdf=prepare(t);first=w/'first.json'
 if not first.exists() or not (dest/'AUDIT-20261102.json').exists():
  print('SKIP reverify missing checkpoint',ident,flush=True);return
 data=load(first);data['key_pages']=sorted(set(data.get('key_pages',[]))|set(extra_key_pages));include_key_window(data);dump(first,data)
 pages=sorted(set(data.get('exam_pages',[])+data.get('key_pages',[])));images=[]
 for i in pages:
  found=list(w.glob(f'p{i}-*.jpg'))
  if not found and pdf:
   run(['pdftoppm','-f',i,'-l',i,'-r','160','-jpeg',pdf,w/f'p{i}'],timeout=90);found=list(w.glob(f'p{i}-*.jpg'))
  if not found:raise FileNotFoundError(f'{ident}: source page {i} has no rendered image')
  images.extend(found)
 tag='verify-full-recheck-'+ident
 ver=twice(tag,lambda:ask(tag,(P/'VERIFY_OCR.txt').read_text(encoding='utf-8')+'\nTRANSCRIPT:\n'+data['de_md'],images,timeout=800,model=VERIFY_MODEL))
 if ver is None:return
 md=(dest/'de.md').read_text(encoding='utf-8')
 for x in ver.get('disagreements',[]):
  if x.get('settled_by_image') and x.get('before') and 'HẾT' not in x['before'] and md.count(x['before'])==1:md=md.replace(x['before'],x['after'],1)
 (dest/'de.md').write_text(md,encoding='utf-8')
 ap=dest/'AUDIT-20261102.json';audit=load(ap);audit.setdefault('verification_history',[]).append(audit.get('verification'))
 audit['verification']=ver;audit['verification_model']=VERIFY_MODEL;audit['reverified_key_pages']=data['key_pages']
 failures=[x for x in audit.get('failures',[]) if x.startswith('Thiếu trang:')]
 if not ver.get('pass'):failures.append('Lượt hai chưa đạt')
 if ver.get('missing_figures'):failures.append('Lượt hai phát hiện thiếu hình')
 if data.get('missing_pages'):failures.append('Thiếu trang: '+str(data['missing_pages']))
 if data['structure'].get('unreadable_count',0) or ver.get('unreadable'):failures.append('Có chỗ không đọc được')
 audit['failures']=list(dict.fromkeys(failures));dump(ap,audit)
 with (dest/'STATUS.md').open('a',encoding='utf-8') as f:
  f.write('\n## Re-verification 2026-11-02\n')
  f.write(f'- Model: {VERIFY_MODEL}; checked source pages: {pages}.\n')
  f.write('- Result: '+('pass' if ver.get('pass') else 'not passed')+'; printed key was re-read independently.\n')
  f.write(json.dumps(ver,ensure_ascii=False,indent=2)+'\n')
 # Refresh checksums for changed paper files and the index.
 sums=ROOT/'SHA256SUMS.txt';lines=sums.read_text(encoding='utf-8').splitlines() if sums.exists() else []
 existing={l.split('  ',1)[1]:l for l in lines if '  ' in l}
 for p in [dest/'de.md',ap,dest/'STATUS.md']:
  rel=str(p.relative_to(ROOT));existing[rel]=hashlib.sha256(p.read_bytes()).hexdigest()+'  '+rel
 sums.write_text('\n'.join(existing[k] for k in sorted(existing))+'\n',encoding='utf-8')
 print('REVERIFIED',ident,'pages',pages,'failures',audit['failures'],flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--limit',type=int,default=0);a.add_argument('--start',type=int,default=0);a.add_argument('--reverify',action='store_true');a.add_argument('--extra-key-page',type=int,action='append',default=[]);args=a.parse_args();tasks=load(ROOT/'audit/outputs/stage1-manifest.json') if (ROOT/'audit/outputs/stage1-manifest.json').exists() else make_manifest()
 for t in tasks[args.start:args.start+args.limit if args.limit else None]:reverify(t,args.extra_key_page) if args.reverify else process(t)

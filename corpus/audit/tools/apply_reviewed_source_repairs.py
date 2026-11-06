"""Apply only parent-reviewed source-image corrections; no OCR or model calls."""
from common import *
from addresses import indexed_questions
from PIL import Image
import shutil
PROOF=ROOT/'audit/outputs/reviewed-source-repairs-20261103'

def archive(source):
 d=PROOF/source.parent.parent.parent.name/source.parent.name;d.mkdir(parents=True,exist_ok=True)
 for name in ['de.md','structure.json','AUDIT-20261102.json']:
  p=source.with_name(name)
  if p.exists() and not (d/name).exists():shutil.copyfile(p,d/name)
 return d

def crop(directory,name,src,box,part,idx):
 im=Image.open(src);target=directory/name;target.parent.mkdir(exist_ok=True);im.crop(box).save(target)
 return {'part':part,'idx':idx,'cau':str(idx),'file':name,'page':int(src.name[1]),'box':[round(v*1000/d) for v,d in zip(box,[im.width,im.height,im.width,im.height])],'pixel_box_reviewed':list(box),'source_image':str(src.relative_to(ROOT)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'crop_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}

def replace_q_images(md,parts,replacements):
 for q in indexed_questions(md,parts):
  key=(q['part'],q['idx'])
  if key in replacements:
   old=q['text'];new=old
   for before,after in replacements[key].items():new=new.replace(before,after)
   if old!=new:
    if md.count(old)!=1:raise ValueError('ambiguous question body')
    md=md.replace(old,new,1)
 return md

def main():
 marker=PROOF/'applied.json'
 if marker.exists():print('Reviewed repairs already applied');return
 review=load(ROOT/'audit/outputs/figure-collision-review-20261103.json');events=[]
 # Hóa has not been analysed yet: complete the previously truncated table and fix nonexistent/misaddressed images.
 source=ROOT/review['transcription_table_fix']['transcription'];saved=archive(source);md=source.read_text();oldsha=hashlib.sha256(md.encode()).hexdigest();st=load(source.with_name('structure.json'));table=review['transcription_table_fix']['table'];header=['Cốc','Nồng độ phần trăm $C_2H_5OH$ trong dung dịch nghiên cứu',*table['columns'][2:]];newtable='| '+' | '.join(header)+' |\n|'+ '|'.join(['---']*len(header))+'|\n'+'\n'.join('| '+' | '.join(row)+' |' for row in table['rows'])
 start=md.index('| Cốc |',md.index('## PHẦN II'));end=md.index('[HÌNH:',start);md=md[:start]+newtable+'\n\n'+md[end:]
 qs=indexed_questions(md,st['parts']);q=next(q for q in qs if q['part']=='P2' and q['idx']==1);body=q['text'];replacement=re.sub(r'(?m)^c\).*$',review['transcription_table_fix']['verbatim_item_c'],body);md=md.replace(body,replacement,1)
 caption='[HÌNH: Các giai đoạn 1–2 của quy trình sản xuất magnesium Pidgeon và phương trình nung dolomite.]\n![](images/cau_2.png)';assert md.count(caption)==1;md=md.replace(caption,'')
 md=replace_q_images(md,st['parts'],{('P2',1):{'images/cau_1.png':'images/cau_1_part2.png'},('P3',2):{'images/cau_2.png':'images/cau_2_part3.png'},('P3',5):{'images/cau_5.png':'images/cau_5_part3.png'}})
 work=ROOT/'audit/work/hoa-hoc--de-thi-thu-tn-thpt-nam-2026-mon-hoa-so-gd-nghe-an-lan-2';p3=work/'p3-03.jpg';p5=work/'p5-05.jpg';assert hashlib.sha256(p3.read_bytes()).hexdigest()==review['transcription_table_fix']['source']['sha256']
 fresh=[crop(source.parent,'images/cau_1_part2.png',p3,(158,709,1090,985),'P2',1),crop(source.parent,'images/cau_2_part3.png',p5,(100,95,978,210),'P3',2),crop(source.parent,'images/cau_5_part3.png',p5,(99,1148,1150,1248),'P3',5)]
 st['figures']=[g for g in st['figures'] if g['file'] not in ['images/cau_1.png','images/cau_2.png','images/cau_5.png']]+fresh;st['figure_count']=len(re.findall(r'!\[[^]]*\]\(([^)]+)\)',md));assert len(st['figures'])==st['figure_count'];source.write_text(md,encoding='utf-8');dump(source.with_name('structure.json'),st);a=load(source.with_name('AUDIT-20261102.json'));a['parent_figure_resolution']={'reviewer':'parent visual confirmation of Luna targeted QA','evidence':'audit/outputs/figure-collision-review-20261103.json','fixed':'Complete source table/c statement; remove invented process image; use part-specific correct table images','before_sha256':oldsha,'teacher_checked':False};dump(source.with_name('AUDIT-20261102.json'),a);events.append({'path':str(source.relative_to(ROOT)),'old_sha256':oldsha,'new_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'content_table_completed':True})
 # Sơn La changes image references only. Existing analytical rows stay valid; preserve exact model-input source hash.
 source=ROOT/'transcriptions/toan/2026-provincial/de-thi-thu-tot-nghiep-thpt-2026-mon-toan-lan-1-so-gddt-son-la/de.md';saved=archive(source);before=source.read_text();oldsha=hashlib.sha256(before.encode()).hexdigest();st=load(source.with_name('structure.json'));md=replace_q_images(before,st['parts'],{('P1',4):{'images/cau_4.png':'images/cau_4_part1.png'},('P2',4):{'images/cau_4.png':'images/cau_4_part2.png'},('P2',1):{'images/cau_1.png':'images/cau_1_part2.png'},('P3',1):{'images/cau_1.png':'images/cau_1_part3.png'}})
 strip=lambda text:re.sub(r'!\[[^]]*\]\([^)]+\)','',text);assert strip(before)==strip(md);work=ROOT/'audit/work/toan--de-thi-thu-tot-nghiep-thpt-2026-mon-toan-lan-1-so-gddt-son-la';fresh=[crop(source.parent,'images/cau_4_part1.png',work/'p1-01.jpg',(875,790,1090,975),'P1',4),crop(source.parent,'images/cau_1_part2.png',work/'p2-02.jpg',(430,990,725,1290),'P2',1),crop(source.parent,'images/cau_4_part2.png',work/'p3-03.jpg',(340,510,825,860),'P2',4),crop(source.parent,'images/cau_1_part3.png',work/'p3-03.jpg',(340,1225,825,1545),'P3',1)]
 st['figures']=[g for g in st['figures'] if g['file'] not in ['images/cau_1.png','images/cau_4.png']]+fresh;st['figure_count']=len(re.findall(r'!\[[^]]*\]\(([^)]+)\)',md));assert len(st['figures'])==st['figure_count'];source.write_text(md,encoding='utf-8');newsha=hashlib.sha256(source.read_bytes()).hexdigest();dump(source.with_name('structure.json'),st);a=load(source.with_name('AUDIT-20261102.json'));a['parent_figure_resolution']={'reviewer':'parent visual confirmation; pixel bounds adjusted to include labels','evidence':'audit/outputs/figure-collision-review-20261103.json','before_sha256':oldsha,'reference_only':True,'non_image_text_unchanged':True,'teacher_checked':False};dump(source.with_name('AUDIT-20261102.json'),a);relative=str(source.relative_to(ROOT))
 def reconcile(value):
  if isinstance(value,dict):
   if (value.get('path')==relative or value.get('source')==relative) and value.get('source_sha256')==oldsha:value['model_input_source_sha256']=value.get('model_input_source_sha256',oldsha);value['source_sha256']=newsha;value['source_reference_revision']='Parent repaired image references only; non-image text unchanged; see reviewed-source-repairs-20261103'
   for child in value.values():reconcile(child)
  elif isinstance(value,list):
   for child in value:reconcile(child)
 for file in (ROOT/'profiles/toan').rglob('*.json'):
  x=load(file);old=json.dumps(x,sort_keys=True);reconcile(x)
  if json.dumps(x,sort_keys=True)!=old:
   dst=saved/'profile-cache-before'/file.relative_to(ROOT/'profiles/toan');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,dst);dump(file,x)
 events.append({'path':relative,'old_sha256':oldsha,'new_sha256':newsha,'non_image_text_unchanged':True})
 manifest=load(ROOT/'audit/outputs/profile-inputs.json')
 for e in manifest['selected']:
  if any(e['path']==r['path'] for r in events):e['source_sha256']=hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()
 dump(ROOT/'audit/outputs/profile-inputs.json',manifest);dump(marker,{'reviewed_repairs':events,'models_reOCRed':False,'source_proof':'Luna targeted QA plus parent actual-page visual review'});print('Applied reviewed source repairs',len(events))
if __name__=='__main__':main()

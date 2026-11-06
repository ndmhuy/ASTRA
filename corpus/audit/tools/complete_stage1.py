from common import *
from stage1 import process
import collections
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import unicodedata

def usable(subject):
 result=[]
 for p in (ROOT/'transcriptions'/subject/'2026-provincial').glob('*/de.md'):
  status=p.with_name('STATUS.md').read_text(encoding='utf-8');st=load(p.with_name('structure.json')) if p.with_name('structure.json').exists() else {}
  a=load(p.with_name('AUDIT-20261102.json')) if p.with_name('AUDIT-20261102.json').exists() else {}
  if subject in ('hoa-hoc','sinh-hoc') and a.get('input',{}).get('source'):
   source=ROOT/a['input']['source']
   if not is_sgd_source(source):continue
  if not a.get('failures') and not a.get('qa_failures') and not re.search(r'STOPPED|incomplete|thiếu trang',status[:650],re.I) and not st.get('unreadable_count') and p.with_name('key.json').exists():result.append(p)
 return result
def is_sgd_source(src):
 if src.suffix.lower()!='.docx':return 'so-gd' in src.parent.name
 ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 try:
  with ZipFile(src) as z:
   xml=ET.fromstring(z.read('word/document.xml'))
  paragraphs=[''.join(x.text or '' for x in p.findall('.//w:t',ns)) for p in xml.findall('.//w:p',ns)]
 except (OSError,KeyError,ET.ParseError):return False
 header_parts=[]
 for paragraph in paragraphs[:30]:
  header_parts.append(paragraph)
  if re.search(r'\bMÔN(?:\s+THI)?\s*:',paragraph,re.I) or re.search(r'\bPHẦN\s+I\b',paragraph,re.I):break
 header=unicodedata.normalize('NFC',' '.join(header_parts)).upper()
 if re.search(r'\bTRƯỜNG\b',header):return False
 return bool(re.search(r'\bSỞ\s+(?:GIÁO\s+DỤC|GD)\b',header) and re.search(r'(?:ĐÀO\s*TẠO|GD\s*&?\s*ĐT)',header))
def complete(subjects=None, *, update_checksums=False, auto_commit=False):
 targets=[('hoa-hoc',5),('sinh-hoc',5),('lich-su',5),('dia-li',5),('toan',20)]
 if subjects is not None:
  unknown=set(subjects)-{s for s,_ in targets}
  if unknown:raise ValueError('Unknown subjects: '+', '.join(sorted(unknown)))
  targets=[item for item in targets if item[0] in subjects]
 for subject,target in targets:
  tried={p.parent.name for p in (ROOT/'transcriptions'/subject/'2026-provincial').glob('*/de.md')}
  suffix='pdf' if subject=='toan' else 'docx';sources=sorted((ROOT/f'official/2026-provincial-{subject}').glob('*/paper.'+suffix))
  for src in sources:
   if len(usable(subject))>=target:break
   slug=src.parent.name
   if subject in ('hoa-hoc','sinh-hoc') and not is_sgd_source(src):continue
   if slug in tried or any(x in slug for x in ['tham-khao','chinh-thuc']):continue
   tried.add(slug);t={'subject':subject,'kind':'provincial','year':2026,'source':str(src.relative_to(ROOT)),'slug':slug,'selection_reason':'Dự phòng để đủ số đề đọc được sau khi loại nguồn dở.'}
   process(t,update_checksums=update_checksums,auto_commit=auto_commit)
  dump(ROOT/'audit/outputs'/f'stage1-usable-{subject}.json',{'subject':subject,'target':target,'usable':len(usable(subject)),'papers':[str(p.relative_to(ROOT)) for p in usable(subject)]})
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser()
 parser.add_argument('--subjects',nargs='+',choices=['hoa-hoc','sinh-hoc','lich-su','dia-li','toan'])
 complete(parser.parse_args().subjects)

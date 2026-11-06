"""Build a disposable FTS5 projection of the curriculum and profile records."""
import hashlib
import json
import re
import sqlite3
from contextlib import closing
import subprocess
import sys
from pathlib import Path

RAG = Path(__file__).resolve().parents[1]
ROOT = RAG.parent
sys.path.insert(0, str(RAG / 'compat'))
from exam_generator import curriculum_map as cm

INDEX = RAG / '.index' / 'astra_rag.sqlite3'
SUBJECTS = {'toan': 'Toán', 'vat-li': 'Vật lí', 'hoa-hoc': 'Hóa học',
            'sinh-hoc': 'Sinh học', 'lich-su': 'Lịch sử', 'dia-li': 'Địa lí',
            'ngu-van': 'Ngữ văn', 'tieng-anh': 'Tiếng Anh', 'gdktpl': 'GDKT&PL'}


def inputs():
    return sorted([*RAG.joinpath('data').glob('*.jsonl'),
                   *ROOT.glob('corpus/profiles/*/topics/*.json')])


def snapshot_id(paths):
    head = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip()
    h = hashlib.sha256()
    for p in paths:
        h.update(str(p.relative_to(ROOT)).encode() + b'\0')
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return f'{head}-{h.hexdigest()[:16]}'


def build(path=INDEX):
    paths = inputs()
    snap = snapshot_id(paths)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db, db:
        db.executescript('''DROP TABLE IF EXISTS chunks; DROP TABLE IF EXISTS chunk_grades;
        DROP TABLE IF EXISTS search_fts; DROP TABLE IF EXISTS metadata;
        CREATE TABLE chunks (chunk_id TEXT PRIMARY KEY, kind TEXT, source_id TEXT, subject TEXT,
          grade INTEGER, locator TEXT, title TEXT, text TEXT, text_folded TEXT, review_status TEXT, snapshot_id TEXT);
        CREATE TABLE chunk_grades (chunk_id TEXT, grade INTEGER, PRIMARY KEY (chunk_id, grade));
        CREATE VIRTUAL TABLE search_fts USING fts5(chunk_id UNINDEXED, text_folded);
        CREATE TABLE metadata (snapshot_id TEXT);''')
        db.execute('INSERT INTO metadata VALUES (?)', (snap,))
        for p in paths:
            rel = p.relative_to(ROOT).as_posix()
            if p.suffix == '.jsonl':
                records = [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
                for row in records:
                    text = ' '.join([row['title_vi'], *(row.get('keywords_vi') or []), *(row.get('outcomes_vi') or [])])
                    add(db, f"curriculum:{row['unit_id']}", 'curriculum', row['unit_id'], row['subject'],
                        [row['grade']], f"{rel}#{row['unit_id']}", row['title_vi'], text, row['status'], snap)
            else:
                row = json.loads(p.read_text(encoding='utf-8'))
                topic = row['topic']
                grades = sorted({int(g) for g in topic.get('grades', []) if str(g) in ('10', '11', '12')})
                title = topic.get('display_topic') or topic['topic']
                parts = [title, *(topic.get('raw_topics') or [])]
                for entry in topic.get('component_details', {}).get('reasoning_moves', []):
                    move = entry.get('move', {})
                    if isinstance(move, dict):
                        parts.extend(str(move.get(k) or '') for k in ('move', 'how_to_apply'))
                subject = SUBJECTS.get(row['subject'], row['subject'].replace('-', ' '))
                add(db, f"profile:{row['subject']}:{p.stem}", 'profile', p.stem, subject, grades,
                    f'{rel}#{p.stem}', title, ' '.join(parts), 'agent-reviewed, not teacher-confirmed', snap)
    return snap


def add(db, chunk_id, kind, source_id, subject, grades, locator, title, text, status, snap):
    grade = grades[0] if len(grades) == 1 else None
    folded = cm.fold(text)
    db.execute('INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?,?,?)',
               (chunk_id, kind, source_id, subject, grade, locator, title, text, folded, status, snap))
    db.execute('INSERT INTO search_fts VALUES (?,?)', (chunk_id, folded))
    db.executemany('INSERT INTO chunk_grades VALUES (?,?)', [(chunk_id, g) for g in grades])


def tokens(query):
    return [t for t in re.findall(r'[a-z0-9]+', cm.fold(query)) if t not in cm._STOP]

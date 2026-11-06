"""Search the offline FTS index and append a retrieval receipt."""
import argparse
import datetime
import json
import sqlite3
from contextlib import closing
from .index import INDEX, SUBJECTS, build, cm, tokens

VERSION = 'fts5-v1'

# Spelling variants from the copied assistant curriculum source, not semantic synonyms.
VARIANTS = {'om': ('ohm',), 'niuton': ('newton',), 'jun': ('joule',), 'jul': ('joule',)}


def search(query, subject=None, grades=None, kind='both', limit=5, rebuild=False, expand=False):
    if rebuild or not INDEX.exists():
        build()
    with closing(sqlite3.connect(INDEX)) as db:
        db.row_factory = sqlite3.Row
        snap = db.execute('SELECT snapshot_id FROM metadata').fetchone()[0]
        filters = {'subject': subject, 'grades': grades, 'kind': kind, 'limit': limit, 'expand': expand}
        grade_values = []
        gap = None
        if grades is not None:
            fields = grades.split(',')
            if not fields or any(x.strip() not in ('10', '11', '12') for x in fields):
                gap = 'bad_grades'
            else:
                grade_values = sorted({int(x.strip()) for x in fields})
        words = tokens(query)
        if not gap and not words:
            gap = 'empty_query'
        where, params = [], []
        if subject:
            aliases = {cm.fold(v).strip(): cm.fold(v).strip() for v in SUBJECTS.values()}
            aliases.update({cm.fold(k.replace('-', ' ')): cm.fold(v) for k, v in SUBJECTS.items()})
            aliases.update({'hoa': 'hoa hoc', 'ly': 'vat li', 'vat ly': 'vat li', 'sinh': 'sinh hoc', 'su': 'lich su', 'dia': 'dia li', 'van': 'ngu van', 'anh': 'tieng anh'})
            target = aliases.get(cm.fold(subject).strip(), cm.fold(subject).strip())
            # SQLite's lower() does not fold Vietnamese; enumerate exact stored subjects in Python.
            matched = [r[0] for r in db.execute('SELECT DISTINCT subject FROM chunks') if cm.fold(r[0]).strip() == target]
            where.append('c.subject IN (' + ','.join('?' for _ in matched or [None]) + ')')
            params.extend(matched or [None])
        if grade_values:
            where.append('EXISTS (SELECT 1 FROM chunk_grades g WHERE g.chunk_id=c.chunk_id AND g.grade IN (' + ','.join('?' for _ in grade_values) + '))')
            params.extend(grade_values)
        if kind != 'both':
            where.append('c.kind = ?')
            params.append(kind)
        clause = (' WHERE ' + ' AND '.join(where)) if where else ''
        if not gap and not db.execute('SELECT 1 FROM chunks c' + clause + ' LIMIT 1', params).fetchone():
            gap = 'no_rows'
        hits = []
        if not gap:
            match = ' AND '.join(('(' + ' OR '.join('"' + v + '"' for v in (t, *VARIANTS[t])) + ')') if expand and t in VARIANTS else '"' + t + '"' for t in words)
            sql = ('SELECT c.*, bm25(search_fts) AS score FROM search_fts JOIN chunks c ON c.chunk_id=search_fts.chunk_id'
                   + (' WHERE ' + ' AND '.join(where) + ' AND ' if where else ' WHERE ')
                   + 'search_fts MATCH ? ORDER BY score ASC, c.chunk_id ASC LIMIT ?')
            for rank, row in enumerate(db.execute(sql, [*params, match, limit]), 1):
                hit = dict(row)
                hit['rank'] = rank
                hit['excerpt'] = ' '.join(hit.pop('text').split())[:150]
                hit.pop('text_folded')
                hits.append(hit)
            if not hits:
                gap = 'no_match'
        receipt = {'query': query, 'filters': filters, 'ranked_chunk_ids': [h['chunk_id'] for h in hits],
                   'snapshot_id': snap, 'retriever_version': VERSION,
                   'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        with (INDEX.parent / 'receipts.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(receipt, ensure_ascii=False) + '\n')
        return {'hits': hits, 'gap': gap, 'receipt': receipt}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-q', '--query', required=True)
    parser.add_argument('--subject')
    parser.add_argument('--grades')
    parser.add_argument('--kind', choices=('curriculum', 'profile', 'both'), default='both')
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('--expand', action='store_true', help='enable limited spelling variants')
    parser.add_argument('--show-receipt', action='store_true')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    result = search(args.query, args.subject, args.grades, args.kind, args.limit, args.rebuild, args.expand)
    if args.json:
        payload = {'hits': result['hits'], 'gap': result['gap']}
        if args.show_receipt:
            payload['receipt'] = result['receipt']
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif result['gap']:
        print('GAP: ' + result['gap'])
    else:
        for h in result['hits']:
            print(f"{h['rank']}. score={h['score']:.6f} {h['chunk_id']} | {h['kind']} | {h['subject']} | grade={h['grade']}\n   {h['title']}\n   {h['locator']} | {h['review_status']}\n   {h['excerpt']}")
            if h['kind'] == 'profile':
                print('   labels agent-reviewed, not teacher-confirmed')
    if args.show_receipt and not args.json:
        print('Receipt: ' + json.dumps(result['receipt'], ensure_ascii=False))


if __name__ == '__main__':
    main()

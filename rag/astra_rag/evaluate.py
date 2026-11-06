"""Reproduce the small, provisional curriculum-only comparison."""
import json
import statistics
import time
from pathlib import Path
from .index import INDEX, build
from .search import search


def main():
    cases = json.loads((Path(__file__).resolve().parents[1] / 'tests/gold_profile_queries.json').read_text())['cases']
    snap = build()
    results = {}
    for mode in (False, True):
        by_set = {}
        for case in cases:
            start = time.perf_counter()
            got = search(case['query'], case['subject'], case['grades'], 'curriculum', 5, expand=mode)
            elapsed = (time.perf_counter() - start) * 1000
            ids = [h['source_id'] for h in got['hits']]
            ranks = [i for i, item in enumerate(ids, 1) if item in case.get('relevant', [])]
            scope_errors = sum(h['subject'] != case['subject'] or str(h['grade']) != case['grades'] for h in got['hits'])
            by_set.setdefault(case['set'], []).append({'id': case['id'], 'ids': ids, 'gap': got['gap'],
                'hit': bool(ranks), 'rr': 1 / ranks[0] if ranks else 0,
                'gap_correct': got['gap'] == case.get('gap') if 'gap' in case else None,
                'scope_errors': scope_errors, 'ms': elapsed})
        results['expanded' if mode else 'lexical'] = by_set
    print(json.dumps({'snapshot_id': snap, 'index_bytes': INDEX.stat().st_size, 'results': results}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

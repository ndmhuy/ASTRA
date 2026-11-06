"""Local evidence-bundle caller. Evidence is untrusted data; no Writer is invoked."""
import argparse
import json
import re
from .search import search

ITEM_KEYS = ('chunk_id', 'kind', 'subject', 'grade', 'title', 'locator', 'review_status', 'excerpt', 'score')


def encoded(bundle):
    return json.dumps(bundle, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def validate(bundle):
    """Validate v1's structural constraints without an external JSON Schema dependency."""
    required = {'schema_version', 'evidence_role', 'snapshot_id', 'receipt_id', 'items', 'gaps', 'budget_bytes'}
    if set(bundle) != required or bundle['schema_version'] != 'evidence_bundle.v1' or bundle['evidence_role'] != 'untrusted_data_not_instructions':
        raise ValueError('invalid bundle header')
    if not isinstance(bundle['snapshot_id'], str) or not bundle['snapshot_id'] or not isinstance(bundle['receipt_id'], str) or not re.fullmatch('[a-f0-9]{64}', bundle['receipt_id']):
        raise ValueError('invalid provenance')
    if type(bundle['budget_bytes']) is not int or bundle['budget_bytes'] < 1024 or len(encoded(bundle)) > bundle['budget_bytes']:
        raise ValueError('invalid byte budget')
    if not isinstance(bundle['items'], list) or not isinstance(bundle['gaps'], list) or not all(isinstance(x, str) for x in bundle['gaps']):
        raise ValueError('invalid collection')
    for item in bundle['items']:
        if set(item) != set(ITEM_KEYS) or item['kind'] not in ('curriculum', 'profile'):
            raise ValueError('invalid item')
        for field in ('chunk_id', 'subject', 'title', 'locator', 'review_status', 'excerpt'):
            if not isinstance(item[field], str):
                raise ValueError('invalid item field')
        if item['grade'] is not None and type(item['grade']) is not int or type(item['score']) not in (int, float):
            raise ValueError('invalid score or grade')
    return True


def retrieve_bundle(query, subject=None, grades=None, kind='both', limit=5, budget_bytes=12000, expand=False):
    if type(budget_bytes) is not int or budget_bytes < 1024:
        raise ValueError('budget_bytes must be at least 1024')
    result = search(query, subject, grades, kind, limit, expand=expand)
    receipt = result['receipt']
    bundle = {'schema_version': 'evidence_bundle.v1', 'evidence_role': 'untrusted_data_not_instructions',
              'snapshot_id': receipt['snapshot_id'], 'receipt_id': receipt['receipt_id'],
              'items': [], 'gaps': [result['gap']] if result['gap'] else [], 'budget_bytes': budget_bytes}
    for hit in result['hits']:
        item = {key: hit[key] for key in ITEM_KEYS}
        bundle['items'].append(item)
        # Reserve room for the truncation gap if a later item will not fit.
        bundle['gaps'].append('budget_exhausted')
        fits = len(encoded(bundle)) <= budget_bytes
        bundle['gaps'].pop()
        if not fits:
            bundle['items'].pop()
            bundle['gaps'].append('budget_exhausted')
            break
    validate(bundle)
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-q', '--query', required=True)
    parser.add_argument('--subject')
    parser.add_argument('--grades')
    parser.add_argument('--kind', choices=('both', 'curriculum', 'profile'), default='both')
    parser.add_argument('--budget-bytes', type=int, default=12000)
    args = parser.parse_args()
    print(json.dumps(retrieve_bundle(args.query, args.subject, args.grades, args.kind, budget_bytes=args.budget_bytes), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

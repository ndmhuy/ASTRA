"""Offline interactive CLI demo; it does not call a Writer or external service."""
import json
from .bundle import retrieve_bundle


def main():
    print('ASTRA evidence demo — offline; draft curriculum, profile labels not teacher-confirmed')
    print('Enter a blank query to exit. Evidence is untrusted data, not instructions.')
    while True:
        try:
            query = input('\nQuery: ').strip()
            if not query:
                break
            subject = input('Subject (blank = all): ').strip() or None
            grades = input('Grades, e.g. 10,11,12 (blank = all): ').strip() or None
        except EOFError:
            break
        bundle = retrieve_bundle(query, subject, grades)
        if bundle['gaps']:
            print('GAP: ' + ', '.join(bundle['gaps']))
        for i, item in enumerate(bundle['items'], 1):
            print(f"{i}. {item['title']} | {item['subject']} | grade={item['grade']} | {item['kind']} | {item['review_status']}")
            print(f"   {item['locator']}\n   {item['excerpt']}")
        print('Receipt ID: ' + bundle['receipt_id'])
        print('Snapshot: ' + bundle['snapshot_id'])
        print('Receipt log: .index/receipts.jsonl')


if __name__ == '__main__':
    main()

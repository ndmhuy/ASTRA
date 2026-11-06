import json
import unittest
from astra_rag.bundle import retrieve_bundle, validate, encoded
from astra_rag.index import INDEX


class BundleTests(unittest.TestCase):
    def test_scope_provenance_and_receipt(self):
        bundle = retrieve_bundle('hàm số', 'Toán', '12', 'curriculum')
        self.assertTrue(bundle['items'])
        self.assertTrue(validate(bundle))
        self.assertEqual(bundle['evidence_role'], 'untrusted_data_not_instructions')
        self.assertTrue(all(x['subject'] == 'Toán' and x['grade'] == 12 for x in bundle['items']))
        receipt = json.loads((INDEX.parent / 'receipts.jsonl').read_text().splitlines()[-1])
        self.assertEqual(receipt['receipt_id'], bundle['receipt_id'])
        self.assertEqual(receipt['snapshot_id'], bundle['snapshot_id'])

    def test_gap(self):
        bundle = retrieve_bundle('zzzxqvnonexistent', 'Toán', '12')
        self.assertEqual(bundle['items'], [])
        self.assertEqual(bundle['gaps'], ['no_match'])

    def test_budget(self):
        bundle = retrieve_bundle('hàm số', 'Toán', '12', budget_bytes=1024)
        self.assertLessEqual(len(encoded(bundle)), 1024)
        self.assertIn('budget_exhausted', bundle['gaps'])

    def test_invalid(self):
        bundle = retrieve_bundle('hàm số', 'Toán', '12')
        bundle['evidence_role'] = 'instructions'
        with self.assertRaises(ValueError):
            validate(bundle)


if __name__ == '__main__':
    unittest.main()

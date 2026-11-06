import unittest
from astra_rag.index import build
from astra_rag.search import search


class SearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()

    def ids(self, query, **kwargs):
        return [h['chunk_id'] for h in search(query, **kwargs)['hits']]

    def test_accents(self):
        self.assertEqual(self.ids('hàm số', subject='Toán', grades='12'),
                         self.ids('ham so', subject='Toan', grades='12'))
        self.assertTrue(self.ids('ham so', subject='Toan', grades='12'))

    def test_grade(self):
        hits = search('hàm số', subject='Toán', grades='12', kind='curriculum', limit=50)['hits']
        self.assertTrue(hits)
        self.assertTrue(all(h['grade'] == 12 for h in hits))

    def test_subject(self):
        hits = search('hàm số', subject='Toán', limit=50)['hits']
        self.assertTrue(hits)
        self.assertTrue(all(h['subject'] == 'Toán' for h in hits))

    def test_no_answer(self):
        self.assertEqual(search('zzzxqvnonexistent')['gap'], 'no_match')

    def test_repeat_order(self):
        self.assertEqual(self.ids('hàm số'), self.ids('hàm số'))

    def test_empty(self):
        self.assertEqual(search('   ')['gap'], 'empty_query')

    def test_unknown_grade_not_widened(self):
        self.assertEqual(search('hàm số', grades='13')['gap'], 'bad_grades')

    def test_no_rows(self):
        self.assertEqual(search('hàm số', subject='subject nonexistent')['gap'], 'no_rows')

class ExpansionTests(unittest.TestCase):
    def test_variant_does_not_widen_scope(self):
        hits = search('om', subject='Vật lí', grades='11', kind='curriculum', expand=True)['hits']
        self.assertTrue(any(h['source_id'] == 'vat-li-11-c4-b23' for h in hits))
        self.assertTrue(all(h['subject'] == 'Vật lí' and h['grade'] == 11 for h in hits))
        wrong = search('om', subject='Toán', grades='11', kind='curriculum', expand=True)
        self.assertTrue(all(h['subject'] == 'Toán' and h['grade'] == 11 for h in wrong['hits']))


if __name__ == '__main__':
    unittest.main()

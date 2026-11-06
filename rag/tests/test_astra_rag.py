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


if __name__ == '__main__':
    unittest.main()

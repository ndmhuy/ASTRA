"""S3b: the curriculum source on the REAL curriculum map (no fakes), plus the 30-question eval."""
import unittest

from exam_generator.assistant.sources.curriculum import CurriculumSource, parse_scope
from tests.assistant_eval.run import run

SRC = CurriculumSource()


class ScopeTests(unittest.TestCase):
    def test_subject_grade_chapter(self):
        self.assertEqual(parse_scope("Chương 2 Vật lí 11 có những bài nào?"), {"grade": 11, "subject": "Vật lí", "chapter": 2})

    def test_roman_chapter_and_semester(self):
        s = parse_scope("Toán 10 học kì 2 chương VI")
        self.assertEqual((s["chapter"], s["semester"], s["grade"]), (6, 2, 10))

    def test_unsaid_stays_absent(self):
        self.assertEqual(parse_scope("định luật Ôm"), {})


class SourceTests(unittest.TestCase):
    def test_ohm_spelling_is_mapped(self):
        got = SRC.search({"text": "định luật Ôm"}, limit=3)
        self.assertIsNone(got.gap)
        self.assertIn("vat-li-11-c4-b23", [p.id for p in got.passages])

    def test_tu_dien_is_not_dropped(self):
        got = SRC.search({"text": "Vật lí 11 tụ điện"}, limit=5)
        self.assertTrue(any("Tụ" in p.title for p in got.passages))

    def test_missing_subject_says_no_rows_not_a_guess(self):
        self.assertEqual(SRC.search({"text": "Tin học 11 có những bài gì?"}, limit=3).gap, "no_rows")

    def test_absent_lesson_says_no_match_and_lists_what_exists(self):
        got = SRC.search({"text": "Lịch sử 12 có bài về Điện Biên Phủ không?"}, limit=3)
        self.assertEqual(got.gap, "no_match")
        self.assertTrue(got.meta["unit_titles"])

    def test_semester_unknown_is_said(self):
        self.assertEqual(SRC.search({"text": "Học kì 1 môn Vật lí 11"}, limit=3).gap, "semester_unknown")

    def test_no_subject_is_flagged_as_a_guess(self):
        got = SRC.search({"text": "hàm số bậc hai"}, limit=3)
        self.assertTrue(got.meta.get("subject_guessed"))

    def test_a_lesson_matching_under_half_the_words_is_no_match(self):
        # "Ôm" alone finds the Ohm lesson; with three unrelated words the same lesson is not an answer to the question.
        self.assertIsNone(SRC.search({"text": "Vật lí 11 Ôm"}, limit=3).gap)
        self.assertEqual(SRC.search({"text": "Vật lí 11 Ôm Hubble Kepler Tesla"}, limit=3).gap, "no_match")

    def test_empty_question(self):
        self.assertEqual(SRC.search({"text": "   "}, limit=3).gap, "empty_query")

    def test_every_passage_has_an_id_that_exists(self):
        from exam_generator import curriculum_map as cm
        got = SRC.search({"text": "Vật lí 11 chương 2"}, limit=3)
        for p in got.passages:
            self.assertIsNotNone(cm.unit_by_id(p.id))


class EvalTests(unittest.TestCase):
    def test_all_three_sets_pass(self):
        rows = run()
        self.assertEqual(len(rows), 30)
        bad = [(r["id"], r["detail"]) for r in rows if not r["ok"]]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()

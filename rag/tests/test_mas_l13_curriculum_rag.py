"""MAS lanes L13 and L9-lite: the curriculum map and the evidence builder on it (session flag `mas.rag`).

Owner decision 2026-10-23 (A): RAG is made simply for the curriculum map now; the rest of the data comes later.
Draft map rows are usable now; the owner decides their status in the last review. There is no model, no embedding
and no network here: the retriever is lexical (diacritics folded, BM25-style), behind an interface so an embedding
retriever can plug in later.

* `curriculum_map`: the rows (`exam_generator/curriculum_map_data/*.jsonl`, copied from
  `docs/mas-cloud/knowledge-map`), `units_for`, `cumulative_scope`, `find`; every miss is a `GAP`, never a guess;
* `rag`: the retriever interface, the lexical retriever, the evidence bundle under a token cap (degrading in a fixed
  order, never cutting inside an item), the text block, and the hook that appends the block to the composer's matrix
  block ONLY under `mas.rag` (no flag: the block is byte for byte what it was).

Each test marked "Red on the base" was run red on the base (no such module) before the fix.
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

GRADING_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(GRADING_TOOLS_DIR)

from exam_generator import curriculum_map as cm  # noqa: E402
from exam_generator import mas_profile, rag  # noqa: E402

DATA = Path(GRADING_TOOLS_DIR) / "exam_generator" / "curriculum_map_data"
DOCS = Path(GRADING_TOOLS_DIR).parent / "docs" / "mas-cloud" / "knowledge-map"


class TestTheRows(unittest.TestCase):
    def test_the_687_draft_rows_ship_and_match_the_documented_data(self):
        """Red on the base."""
        shipped = sorted(p.name for p in DATA.glob("*.jsonl"))
        documented = sorted(p.name for p in DOCS.glob("group*/*.jsonl"))
        self.assertEqual(documented, shipped)
        rows = [json.loads(line) for p in DATA.glob("*.jsonl") for line in p.read_text(encoding="utf-8").splitlines()
                if line.strip()]
        self.assertEqual(687, len(rows))
        self.assertEqual({"draft"}, {r["status"] for r in rows})
        self.assertEqual(687, len(cm.all_units()))

    def test_every_row_is_a_unit_with_a_source_and_a_status(self):
        """Red on the base."""
        for unit in cm.all_units():
            with self.subTest(unit=unit.unit_id):
                self.assertTrue(unit.title_vi.strip())
                self.assertTrue(unit.source.get("document"))
                self.assertIn(unit.status, ("draft", "verified"))
                self.assertIn(unit.grade, (10, 11, 12))

    def test_a_draft_row_does_not_pass_as_verified(self):
        """Red on the base: `verified_only` keeps every draft out, whatever asks."""
        self.assertEqual([], list(cm.all_units(verified_only=True)))
        self.assertTrue(cm.is_gap(cm.units_for("Toán", 10, verified_only=True)))
        self.assertTrue(cm.is_gap(cm.find("Toán", "hàm số", verified_only=True)))

    def test_a_broken_line_is_skipped_not_fatal(self):
        """Red on the base."""
        good = json.dumps({"unit_id": "x-1", "subject": "Toán", "grade": 10, "kind": "bài", "title_vi": "Hàm số",
                           "order": 1, "status": "draft", "source": {"document": "d"}})
        units = cm.parse_lines(["", "{not json", "[1]", json.dumps({"unit_id": "no-title"}), good])
        self.assertEqual(["x-1"], [u.unit_id for u in units])


class TestTheBaselineApi(unittest.TestCase):
    def test_the_subject_is_matched_whatever_the_spelling(self):
        """Red on the base."""
        for spelling in ("Toán", "toan", "TOÁN", " Toán "):
            self.assertTrue(cm.units_for(spelling, 10), spelling)
        for spelling in ("Vật lí", "Vật lý", "vat ly", "VatLy"):
            self.assertTrue(cm.units_for(spelling, 10), spelling)
        for spelling in ("GDKTPL", "GDKT&PL", "gdkt&pl"):
            self.assertTrue(cm.units_for(spelling, 10), spelling)
        self.assertTrue(cm.units_for("Hóa", 11))
        self.assertTrue(cm.units_for("Địa lý", 12))

    def test_a_subject_or_grade_with_no_rows_is_a_gap_not_an_empty_guess(self):
        """Red on the base: Vật lí 12 has no rows at all (the data's own GAPS.md)."""
        for result in (cm.units_for("Vật lí", 12), cm.units_for("Âm nhạc", 10), cm.units_for("Toán", 9),
                       cm.units_for(None, 10), cm.units_for("Toán", "mười")):
            with self.subTest(result=result):
                self.assertTrue(cm.is_gap(result))
                self.assertFalse(result)
                self.assertTrue(result.reason)

    def test_units_are_in_book_order(self):
        """Red on the base."""
        units = cm.units_for("Toán", 10)
        self.assertEqual(sorted(u.order for u in units), [u.order for u in units])
        self.assertTrue(all(u.subject == "Toán" and u.grade == 10 for u in units))

    def test_upto_a_test_point_keeps_the_units_the_phase_places_before_it(self):
        """Red on the base: GDKT&PL 10 (b1-b3 early HK1, b4-b7 mid HK1, b8-b11 late HK1, b12.. HK2)."""
        ids = lambda point: [u.unit_id for u in cm.units_for("GDKTPL", 10, upto=point)]
        self.assertEqual(["gdktpl-10-b1", "gdktpl-10-b2", "gdktpl-10-b3", "gdktpl-10-b4", "gdktpl-10-b5",
                          "gdktpl-10-b6", "gdktpl-10-b7"], ids("hk1_mid"))
        self.assertEqual(11, len(ids("hk1_end")))
        self.assertEqual(23, len(ids("hk2_end")))
        self.assertEqual(23, len(ids(None)))
        self.assertLess(len(ids("hk1_mid")), len(ids("hk2_mid")))

    def test_upto_an_order_or_a_unit_id(self):
        """Red on the base."""
        self.assertEqual(["gdktpl-10-b1", "gdktpl-10-b2"], [u.unit_id for u in cm.units_for("GDKTPL", 10, upto=2)])
        self.assertEqual(3, len(cm.units_for("GDKTPL", 10, upto="gdktpl-10-b3")))

    def test_an_unknown_boundary_is_a_gap_and_a_unit_without_a_phase_is_not_placed(self):
        """Red on the base."""
        for upto in ("hk3_mid", "gdktpl-11-b1", 0, -1, 1.5, ["hk1_mid"]):
            with self.subTest(upto=upto):
                self.assertTrue(cm.is_gap(cm.units_for("GDKTPL", 10, upto=upto)), upto)
        unplaced = cm.unplaced("Sinh học", 10)  # 11 rows carry a phase, 22 do not
        placed = cm.units_for("Sinh học", 10, upto="hk2_end")
        self.assertEqual((11, 22), (len(placed), len(unplaced)))
        self.assertTrue(all(u.semester is None for u in unplaced))
        none_placed = cm.units_for("Vật lí", 10, upto="hk2_end")  # no row of Vật lí 10 has a phase
        self.assertTrue(cm.is_gap(none_placed))
        self.assertEqual(41, len(cm.unplaced("Vật lí", 10)))

    def test_the_cumulative_scope_of_a_national_exam_says_which_grade_it_lacks(self):
        """Red on the base."""
        scope = cm.cumulative_scope("Vật lí")
        self.assertEqual([12], scope.missing_grades)
        self.assertEqual({10, 11}, {u.grade for u in scope.units})
        self.assertTrue(scope)
        full = cm.cumulative_scope("Toán", (10, 11, 12))
        self.assertEqual([], full.missing_grades)
        self.assertEqual(133, len(full.units))
        self.assertTrue(cm.is_gap(cm.cumulative_scope("Âm nhạc")))
        self.assertTrue(cm.is_gap(cm.cumulative_scope("Toán", ())))
        self.assertTrue(cm.is_gap(cm.cumulative_scope("Toán", ("x", None))))

    def test_find_is_lexical_with_diacritics_folded_both_ways(self):
        """Red on the base."""
        for query in ("Thuế", "thue", "THUẾ"):
            hits = cm.find("GDKTPL", query)
            self.assertEqual("gdktpl-10-b6", hits[0].unit.unit_id, query)
        self.assertEqual("gdktpl-10-b4", cm.find("GDKTPL", "co che thi truong")[0].unit.unit_id)
        scores = [h.score for h in cm.find("GDKTPL", "hiến pháp")]
        self.assertEqual(sorted(scores, reverse=True), scores)

    def test_a_miss_is_a_gap_with_the_query_in_it(self):
        """Red on the base."""
        for query in ("zzzxyz", "", "   ", None, 3):
            with self.subTest(query=query):
                self.assertTrue(cm.is_gap(cm.find("GDKTPL", query)))
        self.assertEqual("zzzxyz", cm.find("GDKTPL", "zzzxyz").query)
        self.assertTrue(cm.is_gap(cm.find("Âm nhạc", "thuế")))

    def test_find_stays_in_the_grades_asked_and_obeys_the_limit(self):
        """Red on the base."""
        hits = cm.find("Toán", "hàm số", grades=(10,), limit=2)
        self.assertLessEqual(len(hits), 2)
        self.assertTrue(all(h.unit.grade == 10 for h in hits))
        self.assertTrue(cm.is_gap(cm.find("Toán", "hàm số", grades=(9,))))


class TestTheRetriever(unittest.TestCase):
    def test_the_lexical_retriever_answers_through_the_interface(self):
        """Red on the base."""
        retriever = rag.LexicalRetriever()
        hits = retriever.retrieve("Thuế", subject="GDKTPL", grades=(10, 11, 12), limit=3)
        self.assertEqual("gdktpl-10-b6", hits[0].unit.unit_id)
        self.assertIsInstance(retriever, rag.Retriever)
        self.assertTrue(cm.is_gap(retriever.retrieve("zzzxyz", subject="GDKTPL", grades=(10,), limit=3)))

    def test_another_retriever_can_be_registered_and_chosen_by_the_flag(self):
        """Red on the base: the seam an embedding retriever plugs into later."""
        class Fixed:
            def retrieve(self, query, *, subject, grades, limit, verified_only=False):
                return [cm.Hit(unit=cm.units_for("GDKTPL", 10)[0], score=1.0)]

        with mock.patch.dict(rag.RETRIEVERS, {"fixed": Fixed}):
            config = {"mas": {"profile": "on", "rag": "fixed"}, "subject": "GDKTPL"}
            bundle = rag.build_bundle(config, ["bất kỳ"])
            self.assertEqual(["gdktpl-10-b1"], [i["unit_id"] for i in bundle.items])

    def test_no_model_or_embedding_library_is_imported(self):
        """Red on the base: the owner's question 'why no model and embeddings'."""
        for module in (cm, rag):
            text = Path(module.__file__).read_text(encoding="utf-8")
            for word in ("import anthropic", "import numpy", "sentence_transformers", "requests", "urllib", "socket"):
                self.assertNotIn(word, text, (module.__name__, word))


class TestTheFlag(unittest.TestCase):
    def test_the_flag_needs_the_profile_and_reads_strictly(self):
        """Red on the base."""
        self.assertIsNone(rag.retriever_name({"mas": {"rag": True}}))
        self.assertIsNone(rag.retriever_name({}))
        self.assertIsNone(rag.retriever_name(None))
        for off in ("0", "off", "no", False, None, 0, "", [], {}):
            self.assertIsNone(rag.retriever_name({"mas": {"profile": "on", "rag": off}}), off)
        for on in (True, "true", "yes", "on", "1", "lexical"):
            self.assertEqual("lexical", rag.retriever_name({"mas": {"profile": "on", "rag": on}}), on)
        self.assertIsNone(rag.retriever_name({"mas": {"profile": "on", "rag": "nonesuch"}}))
        self.assertTrue(mas_profile.rag({"mas": {"profile": "on", "rag": True}}))
        self.assertFalse(mas_profile.rag({"mas": {"profile": "on"}}))
        for junk in (["mas"], "mas", 5):
            self.assertIsNone(rag.retriever_name(junk))


class TestTheBundle(unittest.TestCase):
    CONFIG = {"mas": {"profile": "on", "rag": True}, "subject": "GDKTPL"}

    def test_a_topic_that_is_in_the_map_is_an_item_and_one_that_is_not_is_a_gap(self):
        """Red on the base: T12, a missing topic yields GAP, not a citation."""
        bundle = rag.build_bundle(self.CONFIG, ["Thuế", "zzzxyz"])
        self.assertIn("gdktpl-10-b6", [i["unit_id"] for i in bundle.items])
        self.assertEqual(["zzzxyz"], [g["topic"] for g in bundle.gaps])
        self.assertTrue(bundle.gaps[0]["reason"])
        text = rag.render(bundle)
        self.assertIn("GAP", text)
        self.assertIn("zzzxyz", text)

    def test_every_item_is_in_the_exams_scope_and_carries_its_source(self):
        """Red on the base: out-of-scope items in a bundle = 0."""
        config = {"mas": {"profile": "on", "rag": True, "rag_grades": [11]}, "subject": "GDKTPL"}
        bundle = rag.build_bundle(config, ["Thuế", "Hiến pháp", "pháp luật"])
        self.assertTrue(bundle.items)
        for item in bundle.items:
            self.assertEqual(11, cm.unit_by_id(item["unit_id"]).grade)
            self.assertTrue(item["source"])
        self.assertNotIn("gdktpl-10-b6", [i["unit_id"] for i in bundle.items])

    def test_the_default_scope_is_grades_10_to_12(self):
        """Red on the base."""
        bundle = rag.build_bundle(self.CONFIG, ["Hiến pháp"])
        self.assertTrue(bundle.items)
        self.assertLessEqual({cm.unit_by_id(i["unit_id"]).grade for i in bundle.items}, {10, 11, 12})

    def test_an_item_appears_once_however_many_topics_find_it(self):
        """Red on the base."""
        bundle = rag.build_bundle(self.CONFIG, ["Thuế", "thuế", "Thuế nhà nước"])
        ids = [i["unit_id"] for i in bundle.items]
        self.assertEqual(len(ids), len(set(ids)))

    def test_the_bundle_is_the_same_twice(self):
        """Red on the base."""
        a, b = rag.build_bundle(self.CONFIG, ["Thuế", "Hiến pháp"]), rag.build_bundle(self.CONFIG, ["Thuế", "Hiến pháp"])
        self.assertEqual(rag.render(a), rag.render(b))

    def test_a_bundle_is_never_over_its_budget_and_degrades_in_a_fixed_order(self):
        """Red on the base: the design's order, outcomes then keywords out, then the lowest item; never cut inside one."""
        rich = {"unit_id": "t-1", "subject": "Toán", "grade": 10, "kind": "bài", "title_vi": "Hàm số",
                "order": 1, "status": "draft", "source": {"document": "d"},
                "keywords_vi": ["đồ thị", "tập xác định"], "outcomes_vi": ["Nhận biết hàm số " * 30]}
        rows = [dict(rich, unit_id=f"t-{i}", title_vi=f"Hàm số {i}") for i in range(1, 9)]
        with mock.patch.object(cm, "all_units", lambda verified_only=False: tuple(cm.parse_lines(
                [json.dumps(r) for r in rows]))):
            config = {"mas": {"profile": "on", "rag": True}, "subject": "Toán"}
            full = rag.build_bundle(config, ["Hàm số"], budget_tokens=100000, per_topic=8)
            self.assertEqual(8, len(full.items))
            self.assertTrue(any("outcomes" in i for i in full.items))
            small = rag.build_bundle(config, ["Hàm số"], budget_tokens=full.tokens // 2, per_topic=8)
            self.assertLessEqual(small.tokens, full.tokens // 2)
            tiny = rag.build_bundle(config, ["Hàm số"], budget_tokens=60, per_topic=8)
            self.assertLessEqual(tiny.tokens, 60)
            for bundle in (small, tiny):
                for item in bundle.items:
                    self.assertTrue(item["title"].startswith("Hàm số"), "an item is whole or gone")
            self.assertFalse(any("outcomes" in i for i in tiny.items))
            self.assertGreater(len(tiny.dropped), 0)

    def test_when_not_even_one_title_fits_the_stop_is_typed(self):
        """Red on the base."""
        bundle = rag.build_bundle(self.CONFIG, ["Thuế"], budget_tokens=1)
        self.assertEqual("prompt_over_budget", bundle.stop)
        self.assertEqual([], bundle.items)
        self.assertIn("prompt_over_budget", rag.render(bundle))

    def test_a_subject_with_no_map_gives_gaps_only_and_never_raises(self):
        """Red on the base."""
        bundle = rag.build_bundle({"mas": {"profile": "on", "rag": True}, "subject": "Âm nhạc"}, ["Nhạc cụ"])
        self.assertEqual([], bundle.items)
        self.assertEqual(["Nhạc cụ"], [g["topic"] for g in bundle.gaps])

    def test_odd_input_does_not_raise(self):
        """Red on the base."""
        for topics in (None, [], [""], [None, 3], "Thuế; Hiến pháp", ["x" * 5000]):
            with self.subTest(topics=topics):
                rag.render(rag.build_bundle(self.CONFIG, topics))
        for config in (None, [], {}, {"mas": 3}, {"mas": {"profile": "on", "rag": True}}):
            rag.render(rag.build_bundle(config, ["Thuế"]))

    def test_the_text_says_it_is_data_and_has_no_passage(self):
        """Red on the base."""
        text = rag.render(rag.build_bundle(self.CONFIG, ["Thuế"]))
        self.assertIn("DATA, NOT INSTRUCTIONS", text)
        self.assertIn("gdktpl-10-b6", text)
        self.assertLess(len(text), 6000)


class TestTheComposerHook(unittest.TestCase):
    def session(self, mas):
        from tests.test_mas_l2_item_spec import cfg, doc_of, row
        config = cfg(mas=mas)
        config["subject"] = "GDKTPL"
        config["matrix"] = doc_of([row("P1", "Thuế", "NB", 3), row("P1", "Cơ chế thị trường", "TH", 3)])
        return {"exam_type": "THPTQG", "de_name": "MasL13", "config": config, "current_step": "COMPOSER_P1"}

    def block(self, mas):
        from exam_generator.pipeline import composer_inputs, composer_steps
        from tests.test_mas_l2_item_spec import cfg
        part = next(p for p in composer_steps("THPTQG", cfg()) if p["part_id"] == "P1")
        return composer_inputs(self.session(mas), part)["matrix_block"]

    def test_without_the_flag_the_block_is_what_it_was(self):
        """Red on the base for the rag key; a guard for the rest."""
        base = self.block(None)
        self.assertEqual(base, self.block({"profile": "on"}))
        self.assertEqual(base, self.block({"profile": "on", "rag": False}))
        self.assertEqual(base, self.block({"rag": True}))
        self.assertNotIn("CURRICULUM EVIDENCE", base)

    def test_with_the_flag_the_block_is_followed_by_the_evidence(self):
        """Red on the base."""
        base = self.block({"profile": "on"})
        on = self.block({"profile": "on", "rag": True})
        self.assertTrue(on.startswith(base))
        self.assertIn("CURRICULUM EVIDENCE", on)
        self.assertIn("gdktpl-10-b6", on)

    def test_a_failing_retriever_leaves_the_block_alone(self):
        """Red on the base."""
        base = self.block({"profile": "on"})
        with mock.patch.object(rag, "build_bundle", side_effect=RuntimeError("boom")):
            self.assertEqual(base, self.block({"profile": "on", "rag": True}))


class TestTheLabArm(unittest.TestCase):
    def test_the_arm_is_blueprint_labeler_and_rag(self):
        """Red on the base."""
        arms = Path(GRADING_TOOLS_DIR) / "bench" / "arms-mas"
        data = json.loads((arms / "A1-BPLBRAG.json").read_text(encoding="utf-8"))
        base = json.loads((arms / "A1-BPLB.json").read_text(encoding="utf-8"))
        self.assertEqual("A1-BPLBRAG", data["id"])
        self.assertEqual(dict(base["mas"], rag=True), data["mas"])
        self.assertEqual(base["routing"], data["routing"])
        self.assertEqual(base["batching"], data["batching"])


def synthetic(*titles, semester=None, band=None):
    """Map rows made for one test: `titles` in book order, one subject, grade 10."""
    rows = [{"unit_id": f"s-{i}", "subject": "Toán", "grade": 10, "kind": "bài", "title_vi": t, "order": i,
             "status": "draft", "source": {"document": "d"},
             "typical_phase": {"semester": semester, "band": band, "provenance": "assumed"}}
            for i, t in enumerate(titles, 1)]
    units = cm.parse_lines([json.dumps(r) for r in rows])
    return mock.patch.object(cm, "all_units", lambda verified_only=False: tuple(units))


class TestAddedWithTheMutationCheck(unittest.TestCase):
    CONFIG = {"mas": {"profile": "on", "rag": True}, "subject": "Toán"}

    def test_a_row_with_a_semester_and_no_band_counts_as_late(self):
        with synthetic("Một", semester=1, band=None):
            self.assertTrue(cm.is_gap(cm.units_for("Toán", 10, upto="hk1_mid")))
            self.assertEqual(1, len(cm.units_for("Toán", 10, upto="hk1_end")))

    def test_the_reason_of_a_gap_names_what_was_wrong(self):
        self.assertEqual("bad_grade", cm.units_for("Toán", "mười").reason)
        self.assertEqual("bad_grade", cm.units_for("Toán", True).reason)
        self.assertEqual("bad_grades", cm.cumulative_scope("Toán", ("x", None)).reason)
        self.assertEqual("empty_query", cm.find("Toán", "   ").reason)
        self.assertEqual("no_match", cm.find("Toán", "zzzxyz").reason)
        self.assertEqual("no_rows", cm.find("Âm nhạc", "thuế").reason)
        self.assertEqual("bad_boundary", cm.units_for("Toán", 10, upto="hk3_mid").reason)

    def test_a_short_word_matches_only_whole_words_and_a_long_prefix_counts_half(self):
        with synthetic("Bậc hai", "Bacteria", "Hàm"):
            self.assertEqual(["s-1"], [h.unit.unit_id for h in cm.find("Toán", "bac")])
            self.assertTrue(cm.is_gap(cm.find("Toán", "hamster")), "a three-letter word is not a prefix")
        with synthetic("Phươngtrình", "Phương"):
            hits = cm.find("Toán", "phuong")
            self.assertEqual(["s-2", "s-1"], [h.unit.unit_id for h in hits], "the exact word outranks the prefix")
            self.assertAlmostEqual(hits[0].score / 2, hits[1].score, places=4)

    def test_a_rare_word_counts_more_than_a_common_one(self):
        with synthetic("Alpha một", "Alpha hai", "Alpha ba", "Gamma bốn", "Beta năm"):
            hits = cm.find("Toán", "alpha beta", limit=5)
            self.assertEqual("s-5", hits[0].unit.unit_id)

    def test_the_token_estimate_is_one_per_three_characters(self):
        self.assertEqual(10, rag.estimate_tokens("a" * 30))
        self.assertEqual(11, rag.estimate_tokens("a" * 31))
        self.assertEqual(0, rag.estimate_tokens(""))

    def test_outcomes_go_before_keywords_and_the_lowest_ranked_item_goes_first(self):
        rows = [{"unit_id": f"t-{i}", "subject": "Toán", "grade": 10, "kind": "bài", "title_vi": f"Hàm số {i}",
                 "order": i, "status": "draft", "source": {"document": "d"}, "keywords_vi": ["đồ thị"],
                 "outcomes_vi": ["Nhận biết " * 20]} for i in range(1, 6)]
        units = tuple(cm.parse_lines([json.dumps(r) for r in rows]))
        with mock.patch.object(cm, "all_units", lambda verified_only=False: units):
            full = rag.build_bundle(self.CONFIG, ["Hàm số"], budget_tokens=10 ** 6, per_topic=5)
            no_outcomes = rag.build_bundle(self.CONFIG, ["Hàm số"], per_topic=5, budget_tokens=full.tokens - 1)
            self.assertEqual(5, len(no_outcomes.items))
            self.assertTrue(all("keywords" in i and "outcomes" not in i for i in no_outcomes.items))
            no_keywords = rag.build_bundle(self.CONFIG, ["Hàm số"], per_topic=5, budget_tokens=no_outcomes.tokens - 1)
            self.assertEqual(5, len(no_keywords.items))
            self.assertTrue(all("keywords" not in i for i in no_keywords.items))
            fewer = rag.build_bundle(self.CONFIG, ["Hàm số"], per_topic=5, budget_tokens=no_keywords.tokens - 20)
            self.assertTrue(0 < len(fewer.items) < 5)
            ranked = [i["unit_id"] for i in full.items]
            self.assertEqual(ranked[:len(fewer.items)], [i["unit_id"] for i in fewer.items])
            self.assertEqual(ranked[len(fewer.items):], fewer.dropped[::-1])

    def test_the_default_scope_reaches_more_than_one_grade(self):
        bundle = rag.build_bundle({"mas": {"profile": "on", "rag": True}, "subject": "Toán"}, ["Xác suất"], per_topic=10)
        self.assertGreater(len({cm.unit_by_id(i["unit_id"]).grade for i in bundle.items}), 1)

    def test_a_long_topic_is_cut_and_the_gaps_are_capped(self):
        bundle = rag.build_bundle(self.CONFIG, ["z" * 500])
        self.assertEqual(200, len(bundle.gaps[0]["topic"]))
        many = rag.build_bundle(self.CONFIG, [f"zzzx{chr(97 + i)}{chr(97 + j)}" for i in range(5) for j in range(6)])
        self.assertEqual(10, len(many.gaps))

    def test_a_retriever_that_raises_is_a_gap_for_that_topic(self):
        class Boom:
            def retrieve(self, *a, **k):
                raise RuntimeError("boom")
        bundle = rag.build_bundle(self.CONFIG, ["Hàm số"], retriever=Boom())
        self.assertEqual([("Hàm số", "retriever_error")], [(g["topic"], g["reason"]) for g in bundle.gaps])

    def test_an_empty_bundle_renders_to_nothing(self):
        self.assertEqual("", rag.render(rag.Bundle()))
        self.assertEqual("", rag.block_for(self.CONFIG, []))

    def test_topics_given_as_one_string_are_split(self):
        bundle = rag.build_bundle({"mas": {"profile": "on", "rag": True}, "subject": "GDKTPL"}, "Thuế; zzzxyz")
        self.assertIn("gdktpl-10-b6", [i["unit_id"] for i in bundle.items])
        self.assertEqual(["zzzxyz"], [g["topic"] for g in bundle.gaps])

    def test_a_matrix_topic_with_a_comma_stays_one_topic_in_the_hook(self):
        from exam_generator.pipeline import composer_inputs, composer_steps
        from tests.test_mas_l2_item_spec import cfg, doc_of, row
        config = cfg(mas={"profile": "on", "rag": True})
        config["subject"] = "GDKTPL"
        config["matrix"] = doc_of([row("P1", "Thuế, zzzxyz", "NB", 3)])
        part = next(p for p in composer_steps("THPTQG", cfg()) if p["part_id"] == "P1")
        text = composer_inputs({"exam_type": "THPTQG", "de_name": "M", "config": config,
                                "current_step": "COMPOSER_P1"}, part)["matrix_block"]
        self.assertIn("gdktpl-10-b6", text)
        self.assertNotIn("GAP:", text)


class TestVerifierFindings(unittest.TestCase):
    """Defects a read-only verifier reported; each is a test that was run red before the fix."""

    CONFIG = {"mas": {"profile": "on", "rag": True}, "subject": "Toán"}

    def test_one_bad_row_does_not_take_the_map_down(self):
        good = {"unit_id": "g-1", "subject": "Toán", "grade": 10, "kind": "bài", "title_vi": "Hàm số", "order": 1,
                "status": "draft", "source": {"document": "d"}}
        bad = [dict(good, unit_id="b-1", typical_phase={"band": ["early"], "semester": {"x": 1}}),
               dict(good, unit_id="b-2", keywords_vi=[None, {"a": 1}, "ok"], outcomes_vi=[3]),
               dict(good, unit_id="b-3", source="not a dict", book=[1], parent_id=5, order="x")]
        lines = [json.dumps(r) for r in [good, *bad]] + ["[" * 100000, "\x00", json.dumps({"unit_id": ["x"]})]
        units = {u.unit_id: u for u in cm.parse_lines(lines)}
        self.assertIn("g-1", units)
        self.assertEqual(("ok",), units["b-2"].keywords_vi)
        self.assertIsNone(units["b-2"].outcomes_vi, "a non-string entry is not text")
        self.assertIsNone(units["b-1"].band)
        with mock.patch.object(cm, "all_units", lambda verified_only=False: tuple(units.values())):
            self.assertTrue(rag.render(rag.build_bundle(self.CONFIG, ["Hàm số"])).count("g-1"))

    def test_a_file_that_is_not_utf8_is_skipped_and_the_rest_still_load(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "a.jsonl").write_bytes(b"\xff\xfe not text")
            (Path(folder) / "b.jsonl").write_text(json.dumps({
                "unit_id": "ok-1", "subject": "Toán", "grade": 10, "title_vi": "Hàm số", "order": 1}), encoding="utf-8")
            with mock.patch.object(cm, "DATA_DIR", Path(folder)):
                cm._load.cache_clear()
                try:
                    self.assertEqual(["ok-1"], [u.unit_id for u in cm.all_units()])
                finally:
                    cm._load.cache_clear()

    def test_the_item_that_goes_first_is_the_lowest_ranked_not_the_last_asked(self):
        config = {"mas": {"profile": "on", "rag": True}, "subject": "Địa lí"}
        topics = ["Khí quyển", "Thực hành: Viết báo cáo về biến đổi khí hậu"]
        full = rag.build_bundle(config, topics, budget_tokens=10 ** 6, per_topic=5)
        scores = [i["score"] for i in full.items]
        self.assertEqual(sorted(scores, reverse=True), scores, "best first in the block")
        tight = rag.build_bundle(config, topics, budget_tokens=full.tokens - 1, per_topic=5)
        if tight.dropped:
            kept = min(i["score"] for i in tight.items) if tight.items else float("inf")
            lost = max(i["score"] for i in full.items if i["unit_id"] in tight.dropped)
            self.assertLessEqual(lost, kept)

    def test_gaps_give_way_to_the_budget_too(self):
        bundle = rag.build_bundle(self.CONFIG, ["zzzxyz qqq www eee rrr ttt"], budget_tokens=5)
        self.assertLessEqual(bundle.tokens, 5)
        self.assertIsNone(bundle.stop, "nothing was found, so nothing was stopped")

    def test_a_scope_that_cannot_be_read_is_no_scope_not_every_grade(self):
        for junk in (10, "10", ["10"], [], [None], [9], {"a": 1}, True):
            with self.subTest(junk=junk):
                config = {"mas": {"profile": "on", "rag": True, "rag_grades": junk}, "subject": "Toán"}
                bundle = rag.build_bundle(config, ["Hàm số"])
                self.assertEqual([], bundle.items)
                self.assertEqual(["Hàm số"], [g["topic"] for g in bundle.gaps])
        ok = {"mas": {"profile": "on", "rag": True, "rag_grades": [10]}, "subject": "Toán"}
        self.assertTrue(all(cm.unit_by_id(i["unit_id"]).grade == 10 for i in rag.build_bundle(ok, ["Hàm số"]).items))

    def test_the_same_topic_in_another_case_is_one_topic(self):
        bundle = rag.build_bundle(self.CONFIG, ["zzzq", "ZZZQ", "zzzq "])
        self.assertEqual(1, len(bundle.gaps))


if __name__ == "__main__":
    unittest.main()

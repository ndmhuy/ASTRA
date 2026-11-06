import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import unicodedata

from rag_workflow.document_loader import decode_documents
from rag_workflow.models import Gap, RetrievalRequest, SourceDocument
from rag_workflow.query_parser import parse
from rag_workflow.workflow import run
from rag_workflow.search_index import PassageIndex, split_passages


def record(document_id="demo-1", **changes):
    content = changes.pop("content", "Synthetic explanation of Ohm law and electrical resistance.")
    result = dict(document_id=document_id, subject="vat-li", grade=11,
                  title="Ohm law", content=content, chapter=4, lesson=24, semester=None,
                  series="Kết nối tri thức", edition="synthetic-demo-v1",
                  source_id="synthetic-demo", source_locator="section-1",
                  source_version="1", content_sha256=hashlib.sha256(content.encode()).hexdigest(),
                  approval_status="approved", approved_by="synthetic fixture author",
                  approved_on="2026-11-06", rights_evidence="Original synthetic test text",
                  evidence_class="synthetic",
                  allow_local_retrieval=True, allow_quotation=True)
    result.update(changes)
    return result


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "corpus.jsonl"
        self.write([record()])

    def write(self, records):
        self.path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records), encoding="utf-8")

    def query(self, text="Physics grade 11 chapter 4 Ohm", **kwargs):
        return run(dict(query_text=text, **kwargs), self.path)

    def gap(self, text, code, **kwargs):
        response = self.query(text, **kwargs)
        self.assertEqual(response.status, "gap")
        self.assertEqual(response.documents, [])
        self.assertEqual(response.gaps[0]["code"], code)

    def test_vietnamese_aliases_and_roman_ranges(self):
        for name in ("Vật lí", "Vật lý", "vat li", "physics", "vat-li"):
            with self.subTest(name=name):
                scope = parse(RetrievalRequest(f"Tìm tài liệu {name} lớp 11 chương II đến IV về Ohm"))
                self.assertEqual((scope.subject, scope.start, scope.end), ("vat-li", 2, 4))

    def test_subjects_are_canonical(self):
        for alias, canonical in (("Toán", "toan"), ("Hóa học", "hoa-hoc"), ("Ngữ văn", "ngu-van"), ("GDKT&PL", "gdktpl")):
            self.assertEqual(parse(RetrievalRequest(f"{alias} lớp 11 bài 2")).subject, canonical)

    def test_invalid_and_ambiguous_queries(self):
        cases = [("grade 11 chapter 4", "missing_subject"),
                 ("Physics chapter 4", "missing_grade"),
                 ("Physics grade 9 chapter 4", "invalid_grade"),
                 ("Physics grade 11 chapter 4-2", "invalid_range"),
                 ("Physics grade 11", "missing_range"),
                 ("Physics grade 11 half chapter 4", "ambiguous_range"),
                 ("Physics grade 11 chapters 2 and 4", "ambiguous_range"),
                 ("Physics grade 11 chapter 4 semester 1", "ambiguous_range"),
                 ("Physics grade 11 chapter 4 Cánh Diều", "unsupported_series"),
                 ("Physics Mathematics grade 11 chapter 4", "ambiguous_subject")]
        for text, code in cases:
            with self.subTest(text=text):
                self.gap(text, code)

    def test_request_boundary(self):
        for payload, code in [({}, "invalid_request"), ([], "invalid_request"),
                              ({"query_text": "x", "top_k": True}, "invalid_request"),
                              ({"query_text": "x", "schema_version": "0"}, "unsupported_schema"),
                              ({"query_text": "x" * 2001}, "query_over_limit")]:
            self.assertEqual(run(payload, self.path).gaps[0]["code"], code)

    def test_hard_filters_prevent_scope_and_permission_leaks(self):
        bad = [dict(subject="toan"), dict(grade=10), dict(chapter=3),
               dict(approval_status="draft"), dict(approval_status="teacher-checked"),
               dict(approval_status="superseded"), dict(allow_local_retrieval=False),
               dict(allow_quotation=False), dict(series="other")]
        self.write([record("good")] + [record(f"bad-{i}", **v) for i, v in enumerate(bad)])
        self.assertEqual([d["document_id"] for d in self.query().documents], ["good"])

    def test_missing_semester_is_not_inferred_from_volume_or_position(self):
        self.gap("Physics grade 11 semester 1", "no_documents_in_scope")

    def test_lesson_and_topic_ranges(self):
        self.assertEqual(self.query("Physics grade 11 lesson 24").status, "success")
        self.assertEqual(self.query("Physics grade 11 Ohm").status, "success")

    def test_no_match_and_no_scope(self):
        self.gap("Physics grade 11 chapter 4 oscillation", "no_relevant_match")
        self.gap("Physics grade 11 chapter 2", "no_documents_in_scope")

    def test_multiple_editions_require_confirmation(self):
        self.write([record(), record("other", edition="other-edition")])
        self.gap("Physics grade 11 chapter 4", "ambiguous_edition")
        self.assertEqual(self.query(edition="synthetic-demo-v1").status, "success")

    def test_ranking_deduplication_and_limit(self):
        self.write([record("a", title="Resistance", content="Ohm"),
                    record("b", title="Ohm", content="Alternative Ohm explanation"),
                    record("c", title="Ohm", content="Alternative Ohm explanation")])
        response = self.query(top_k=2)
        self.assertEqual([d["document_id"] for d in response.documents], ["b", "a"])
        self.assertEqual(len(self.query(top_k=1).documents), 1)
        self.assertEqual(response.to_dict(), self.query(top_k=2).to_dict())

    def test_provenance_and_snapshot_fingerprints(self):
        response = self.query()
        hit = response.documents[0]
        for field in ("source_id", "source_locator", "source_version", "content_sha256", "edition"):
            self.assertTrue(hit[field])
        self.assertEqual(response.corpus_sha256, hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertNotIn("content", hit)

    def test_corrupt_and_duplicate_records_fail_closed(self):
        for records in ([record(content_sha256="bad")], [record(), record()],
                        [record(approved_by=None)], [record(allow_local_retrieval="false")],
                        [record(content_kind="answer_key")]):
            self.write(records)
            self.gap("Physics grade 11 chapter 4", "malformed_document")

    def test_legacy_curriculum_map_is_not_promoted_to_evidence(self):
        with self.assertRaises(Gap) as caught:
            decode_documents(b'{"unit_id":"vat-li-11-c1","status":"draft"}')
        self.assertEqual(caught.exception.code, "curriculum_metadata_only")

    def test_invalid_encoding_and_json(self):
        for raw in (b"\xff", b"not json", b"[]"):
            with self.assertRaises(Gap):
                decode_documents(raw)

    def test_excerpt_contains_a_match_later_in_document(self):
        self.write([record(content="Unrelated context. " * 100 + "Ohm law explanation.")])
        self.assertIn("Ohm", self.query().documents[0]["excerpt"])

    def test_missing_file_returns_gap(self):
        self.path.unlink()
        self.gap("Physics grade 11 chapter 4", "corpus_unavailable")

    def test_repeated_range_label(self):
        scope = parse(RetrievalRequest("Vật lí lớp 11 chương II đến chương IV về Ohm"))
        self.assertEqual((scope.start, scope.end), (2, 4))

    def test_formula_symbols_are_not_roman_range_numbers(self):
        scope = parse(RetrievalRequest("Physics grade 11 chapter IV I = U/R"))
        self.assertEqual(scope.start, 4)
        self.assertIn("i", scope.keywords)

    def test_best_passage_has_exact_source_offsets(self):
        text = "Generic introduction. " * 150 + "\n\nRare Ohm explanation about voltage and resistance."
        self.write([record(title="Electrical notes", content=text)])
        hit = self.query().documents[0]
        self.assertGreater(hit["passage_start"], 0)
        self.assertEqual(hit["excerpt"], text[hit["excerpt_start"]:hit["excerpt_end"]])
        self.assertIn("Ohm", hit["excerpt"])
        self.assertEqual(hit["matched_terms"], ["ohm"])

    def test_passages_cover_source_without_losing_characters(self):
        text = "Một đoạn kiến thức dài. " * 200
        passages = list(split_passages(text))
        self.assertGreater(len(passages), 1)
        self.assertEqual(passages[0].start, 0)
        self.assertEqual(passages[-1].end, len(text))
        for a, b in zip(passages, passages[1:]):
            self.assertLess(a.start, b.start)
            self.assertLessEqual(b.start, a.end)
        for p in passages:
            self.assertEqual(p.text, text[p.start:p.end])

    def test_vietnamese_composed_and_decomposed_text_retrieve_equally(self):
        content = "Điện trở và định luật Ôm."
        for form in ("NFC", "NFD"):
            self.write([record(title="Ghi chú", content=unicodedata.normalize(form, content))])
            hit = self.query("Vật lí lớp 11 chương 4 về điện trở").documents[0]
            self.assertEqual(hit["matched_terms"], ["dien", "tro"])

    def test_bm25_rewards_rare_terms(self):
        documents = [SourceDocument(**record("rare", title="Notes", content="unique concept")),
                     SourceDocument(**record("common-1", title="Notes", content="common concept")),
                     SourceDocument(**record("common-2", title="Notes", content="common example"))]
        hits = PassageIndex(documents).ranked(("unique", "common"))
        self.assertEqual(hits[0][1].document_id, "rare")

    def test_bm25_normalizes_passage_length(self):
        documents = [SourceDocument(**record("short", title="Notes", content="ohm explanation")),
                     SourceDocument(**record("long", title="Notes", content="ohm " + "context " * 80))]
        hits = PassageIndex(documents).ranked(("ohm",))
        self.assertEqual(hits[0][1].document_id, "short")

    def test_cli_success_and_gap_exit_codes(self):
        for text, expected in (("Physics grade 11 chapter 4 Ohm", 0), ("Physics", 2)):
            result = subprocess.run([sys.executable, "-m", "rag_workflow.cli", "--query", text,
                                     "--corpus", str(self.path)], capture_output=True, encoding="utf-8")
            self.assertEqual(result.returncode, expected, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "success" if expected == 0 else "gap")


if __name__ == "__main__":
    unittest.main()

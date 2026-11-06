"""Synthetic snapshot tests; no exam content is copied into fixtures."""

from dataclasses import asdict
import io
import json
import tarfile
import subprocess
import sys
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.request import Request, urlopen

from rag_workflow.app import create_server
from rag_workflow.existing_corpus import load_existing_corpus, search_existing


class ExistingCorpusTests(unittest.TestCase):
    def setUp(self):
        rows = [
            dict(
                unit_id="vat-li-11-c1",
                subject="Vật lí",
                grade=11,
                kind="chương",
                title_vi="Chương I. Dao động",
                parent_id=None,
                status="draft",
            ),
            dict(
                unit_id="vat-li-11-c1-b2",
                subject="Vật lí",
                grade=11,
                kind="bài",
                title_vi="Bài 2. Dao động điều hòa",
                parent_id="vat-li-11-c1",
                status="draft",
            ),
        ]
        self.files = {
            "rag/data/vat-li-11.jsonl": "\n".join(json.dumps(r) for r in rows),
            "corpus/registry/papers.csv": "subject,class,path,usable_as_content_evidence\n"
            "vat-li,official,transcriptions/vat-li/2025-paper/de.md,True\n"
            "vat-li,format_only,transcriptions/vat-li/2025-reference/de.md,False\n",
            "corpus/transcriptions/vat-li/2025-paper/de.md": "Synthetic dao động illustration. "
            * 50,
            "corpus/transcriptions/vat-li/2025-paper/STATUS.md": "Teacher checked: no",
            "corpus/transcriptions/vat-li/2025-paper/source.json": '{"provenance_note":"third-party copy"}',
            "corpus/transcriptions/vat-li/2025-paper/key.json": '{"SECRET_KEY":"never index"}',
            "corpus/transcriptions/vat-li/2025-reference/de.md": "EXCLUDED_REFERENCE_SENTINEL",
        }

    def load(self):
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w") as archive:
            for path, text in self.files.items():
                raw = text.encode()
                member = tarfile.TarInfo(path)
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
        results = [
            SimpleNamespace(returncode=0, stdout=b"a" * 40 + b"\n"),
            SimpleNamespace(returncode=0, stdout=output.getvalue()),
        ]
        with patch("rag_workflow.existing_corpus.subprocess.run", side_effect=results):
            return load_existing_corpus()

    def test_projection_preserves_drafts_and_excludes_keys_and_reference_papers(self):
        documents, info = self.load()
        self.assertEqual(
            (info["curriculum_rows"], info["exam_papers"], info["excluded_papers"]), (2, 1, 1)
        )
        text = json.dumps([asdict(d) for d in documents])
        self.assertNotIn("SECRET_KEY", text)
        self.assertNotIn("EXCLUDED_REFERENCE_SENTINEL", text)
        self.assertEqual(documents[0].approval_status, "draft")
        self.assertEqual(documents[-1].provenance["source"]["provenance_note"], "third-party copy")
        self.assertIsNone(documents[-1].grade)

    def test_parent_scope_and_draft_curriculum_search(self):
        documents, info = self.load()
        response = search_existing(
            dict(query_text="Vật lí lớp 11 chương 1 dao động"), documents, info["snapshot"]
        )
        self.assertEqual(response.status, "success")
        self.assertEqual(len(response.documents), 2)
        self.assertTrue(
            all(d["chapter"] == 1 and d["approval_status"] == "draft" for d in response.documents)
        )
        response = search_existing(
            dict(query_text="Vật lí lớp 11 bài 2"), documents, info["snapshot"]
        )
        self.assertEqual([d["document_id"] for d in response.documents], ["vat-li-11-c1-b2"])

    def test_exam_topic_search_and_exact_offsets(self):
        documents, info = self.load()
        response = search_existing(
            dict(query_text="Vật lí dao động", collection="exam"), documents, info["snapshot"]
        )
        self.assertEqual(response.status, "success")
        hit = response.documents[0]
        self.assertEqual(
            hit["excerpt"], documents[-1].content[hit["excerpt_start"] : hit["excerpt_end"]]
        )
        self.assertEqual(hit["approval_status"], "ocr-draft")

    def test_exam_scope_is_not_invented(self):
        documents, info = self.load()
        for query in ("Vật lí lớp 11 dao động", "Vật lí chương 1 dao động"):
            response = search_existing(
                dict(query_text=query, collection="exam"), documents, info["snapshot"]
            )
            self.assertEqual(response.gaps[0]["code"], "unmapped_exam_scope")
            self.assertEqual(response.documents, [])

    def test_curriculum_range_cannot_leak_later_chapters(self):
        documents, info = self.load()
        response = search_existing(
            dict(query_text="Vật lí lớp 11 chương 2 dao động"), documents, info["snapshot"]
        )
        self.assertEqual(response.gaps[0]["code"], "no_documents_in_scope")

    def test_broken_parent_graph_fails_ingestion(self):
        self.files["rag/data/vat-li-11.jsonl"] = json.dumps(
            dict(
                unit_id="vat-li-11-b1",
                grade=11,
                kind="bài",
                title_vi="Synthetic",
                parent_id="missing",
                status="draft",
            )
        )
        with self.assertRaisesRegex(ValueError, "Missing curriculum parent"):
            self.load()

    def test_fingerprint_and_snapshot_have_distinct_meanings(self):
        documents, info = self.load()
        response = search_existing(
            dict(query_text="Vật lí dao động", collection="exam"), documents, info["snapshot"]
        )
        self.assertEqual(response.corpus_snapshot, "a" * 40)
        self.assertEqual(response.corpus_sha256, info["corpus_sha256"])
        self.assertEqual(len(response.corpus_sha256), 64)
        self.assertIsNone(response.resolved_scope.series)

    def test_invalid_payloads_return_structured_gaps(self):
        documents, info = self.load()
        for payload in (None, [], "query", {"query_text": "x", "collection": "keys"}):
            response = search_existing(payload, documents, info["snapshot"])
            self.assertEqual(response.gaps[0]["code"], "invalid_request")

    def test_exam_excerpt_centers_on_late_match(self):
        path = "corpus/transcriptions/vat-li/2025-paper/de.md"
        self.files[path] = "Context " * 75 + "dao động explanation."
        documents, info = self.load()
        response = search_existing(
            dict(query_text="Vật lí dao động", collection="exam"), documents, info["snapshot"]
        )
        self.assertIn("dao động", response.documents[0]["excerpt"])

    def test_missing_registry_is_a_source_error(self):
        del self.files["corpus/registry/papers.csv"]
        with self.assertRaisesRegex(ValueError, "registry is missing"):
            self.load()

    def test_assumed_semesters_stay_in_provenance_not_scope(self):
        path = "rag/data/vat-li-11.jsonl"
        rows = [json.loads(line) for line in self.files[path].splitlines()]
        rows[0]["typical_phase"] = {"semester": 1, "provenance": "assumed"}
        rows[0]["book"] = {"series": "Kết nối tri thức (Global Success)"}
        self.files[path] = "\n".join(json.dumps(row) for row in rows)
        documents, _ = self.load()
        self.assertIsNone(documents[0].semester)
        self.assertEqual(documents[0].provenance["typical_phase"]["semester"], 1)

    def test_unrelated_textbook_series_is_rejected(self):
        path = "rag/data/vat-li-11.jsonl"
        rows = [json.loads(line) for line in self.files[path].splitlines()]
        rows[0]["book"] = {"series": "Other series"}
        self.files[path] = "\n".join(json.dumps(row) for row in rows)
        with self.assertRaisesRegex(ValueError, "Unsupported textbook series"):
            self.load()

    def test_cli_missing_snapshot_is_json_gap_without_traceback(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "rag_workflow.cli",
                "--existing",
                "--corpus-ref",
                "refs/heads/does-not-exist-rag-test",
                "--query",
                "Vật lí dao động",
                "--collection",
                "exam",
            ],
            capture_output=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["gaps"][0]["code"], "corpus_unavailable")
        self.assertNotIn("Traceback", result.stderr)

    def test_http_search_and_source_share_checksums(self):
        documents, info = self.load()
        server = create_server(0, documents, info)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            raw = json.dumps(dict(query_text="Vật lí dao động", collection="exam")).encode()
            with urlopen(Request(base + "/api/search", data=raw), timeout=5) as response:
                result = json.load(response)
            hit = result["documents"][0]
            with urlopen(base + "/api/documents/" + hit["document_id"], timeout=5) as response:
                source = json.load(response)
            self.assertEqual(source["content_sha256"], hit["content_sha256"])
            self.assertEqual(result["corpus_sha256"], info["corpus_sha256"])
            self.assertEqual(
                source["content"][hit["excerpt_start"] : hit["excerpt_end"]], hit["excerpt"]
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()

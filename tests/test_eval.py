"""Unit tests for the retrieval evaluation harness and automated gold verifier."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from rag_workflow.demo import demo_documents
from rag_workflow.eval import (
    DEFAULT_DEMO_GOLD,
    evaluate_all_modes,
    load_gold_queries,
    verify_gold_queries,
)
from rag_workflow.results import collection_fingerprint


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.documents = demo_documents()
        self.corpus_hash = collection_fingerprint(self.documents)
        self.rows = load_gold_queries(DEFAULT_DEMO_GOLD)

    def test_gold_verification_succeeds_for_valid_targets_and_rejects_missing(self):
        summary = verify_gold_queries(self.rows, self.documents)
        self.assertEqual(summary["status"], "verified")
        self.assertEqual(summary["verified_by"], "auto-corpus-check-v1")
        self.assertEqual(summary["total_queries"], 10)
        bad_rows = [
            {
                "id": "bad-1",
                "split": "dev",
                "query_text": "Physics grade 11 chapter 4 Ohm",
                "expected_status": "success",
                "relevant": ["nonexistent-doc-id"],
            }
        ]
        with self.assertRaisesRegex(ValueError, "unknown corpus target"):
            verify_gold_queries(bad_rows, self.documents)

    def test_evaluate_all_modes_computes_comparative_metrics(self):
        report = evaluate_all_modes(
            self.rows, self.documents, self.corpus_hash, modes=("hybrid", "bm25", "embedding"), k=5
        )
        self.assertEqual(report["verification"]["status"], "verified")
        for mode in ("hybrid", "bm25", "embedding"):
            overall = report["modes"][mode]["overall"]
            self.assertEqual(overall["queries"], 10)
            self.assertEqual(overall["gap_accuracy"], 1.0)
            self.assertGreaterEqual(overall["hit_at_k"], 0.85)
            self.assertGreaterEqual(overall["mrr"], 0.85)
        self.assertEqual(len(report["queries"]), 10)

    def test_eval_cli_demo_and_invalid_gold_file(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag_workflow.eval", "--demo", "--mode", "all"],
            capture_output=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verification"]["status"], "verified")
        self.assertIn("hybrid", payload["modes"])

        with tempfile.TemporaryDirectory() as tmp:
            bad_file = Path(tmp) / "bad.jsonl"
            bad_file.write_text('{"id": "x"}\n', encoding="utf-8")
            bad_run = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "rag_workflow.eval",
                    "--demo",
                    "--gold",
                    str(bad_file),
                ],
                capture_output=True,
                encoding="utf-8",
            )
            self.assertEqual(bad_run.returncode, 2)


if __name__ == "__main__":
    unittest.main()

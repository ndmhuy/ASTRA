"""Unit and acceptance tests for Toán THPT topic packs, matrix retrieval, and MAS handoff."""

import hashlib
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from rag_workflow.app import create_server
from rag_workflow.eval import evaluate_toan_acceptance
from rag_workflow.matrix_retriever import (
    default_toan_thpt_matrix,
    parse_matrix_request,
    retrieve_exam_context,
)
from rag_workflow.models import Gap
from rag_workflow.profile_pack import (
    _RELEASE_CACHE,
    export_release_pack,
    get_topic_pack,
    load_profile_release,
)


def _sha256_bytes(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _has_staging_rag_ref() -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "origin/staging/rag^{commit}"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _build_synthetic_toan_pack(root: Path) -> Path:
    """Create a minimal deterministic Toán THPT release pack in `root` for unit tests."""
    topics = [
        (
            "5fed66930d74",
            "nguyen-ham",
            "Nguyên hàm",
            {
                "schema_version": "research-topic-pack-v1",
                "origin": "synthetic-test-profile",
                "teacher_approved": False,
                "topic": {
                    "display_topic": "Nguyên hàm",
                    "grades": [12],
                    "raw_topics": ["Nguyên hàm", "Họ nguyên hàm"],
                    "patterns_by_class": {
                        "official": [
                            {
                                "part_kind": "multiple_choice",
                                "topic": "Nguyên hàm",
                                "grade": 12,
                                "construction": "Tìm họ nguyên hàm của hàm số f(x) bằng bảng nguyên hàm cơ bản.",
                                "wrong_options": "Nhầm dấu nguyên hàm lượng giác hoặc quên chia hệ số a.",
                                "difficulty_source": "Biến đổi biểu thức trước khi lấy nguyên hàm.",
                                "discrimination": "medium",
                                "typical_steps": 2,
                                "refs": ["official-2025|P1|3"],
                                "paper_count": 1,
                                "row_count": 1,
                            }
                        ],
                        "provincial_third_party": [],
                    },
                    "classes": {},
                    "component_details": {},
                    "support_refs": ["official-2025|P1|3", "prov-2025|P1|7"],
                },
                "construction_observations": [
                    {
                        "ref": "official-2025|P1|3",
                        "paper_id": "official-2025",
                        "year": 2025,
                        "part": "P1",
                        "idx": 3,
                        "sub": None,
                        "printed_idx": "3",
                        "topic": "Nguyên hàm",
                        "grade": 12,
                        "discrimination": "low",
                        "given": "Hàm số lượng giác cơ bản f(x) = cos x.",
                        "task": "Tìm họ nguyên hàm của hàm số.",
                        "reasoning": ["Áp dụng công thức nguyên hàm của cos x là sin x + C."],
                        "steps": 1,
                        "combines": ["Bảng nguyên hàm cơ bản"],
                        "cue_use": "Trực tiếp",
                        "difficulty_source": None,
                        "wrong_options": "Nhầm dấu thành -sin x + C.",
                        "wrong_option_details": [
                            {
                                "label": "B",
                                "mistake_kind": "Nhầm dấu đạo hàm và nguyên hàm",
                                "reason": "Chọn -sin x + C do nhớ nhầm đạo hàm của cos x.",
                            }
                        ],
                        "evidence_class": "official",
                    },
                    {
                        "ref": "prov-2025|P1|7",
                        "paper_id": "prov-2025",
                        "year": 2025,
                        "part": "P1",
                        "idx": 7,
                        "sub": None,
                        "printed_idx": "7",
                        "topic": "Nguyên hàm",
                        "grade": 12,
                        "discrimination": "medium",
                        "given": "Cho hàm số f(x) = e^(2x) và điều kiện ban đầu F(0) = 1.",
                        "task": "Tìm nguyên hàm F(x) thỏa mãn điều kiện và tính F(1).",
                        "reasoning": [
                            "Tìm họ nguyên hàm F(x) = (1/2)e^(2x) + C.",
                            "Thay F(0) = 1 tìm C = 1/2.",
                        ],
                        "steps": 2,
                        "combines": ["Nguyên hàm hàm mũ", "Điều kiện giá trị ban đầu"],
                        "cue_use": "Thay số tìm C",
                        "difficulty_source": "Hệ số 1/2 của hàm mũ.",
                        "wrong_options": "Quên chia cho hệ số 2 ở số mũ.",
                        "wrong_option_details": [],
                        "evidence_class": "provincial_third_party",
                    },
                    {
                        "ref": "prov-2025|P1|12",
                        "paper_id": "prov-2025",
                        "year": 2025,
                        "part": "P1",
                        "idx": 12,
                        "sub": None,
                        "printed_idx": "12",
                        "topic": "Nguyên hàm",
                        "grade": 12,
                        "discrimination": "medium",
                        "given": "Hàm phân thức hữu tỉ chưa gắn nhãn mức độ.",
                        "task": "Tìm họ nguyên hàm.",
                        "reasoning": ["Tách phân thức."],
                        "steps": 2,
                        "combines": [],
                        "cue_use": None,
                        "difficulty_source": None,
                        "wrong_options": "Sai dấu logarit.",
                        "wrong_option_details": [],
                        "evidence_class": "provincial_third_party",
                    },
                ],
                "level_assignments": [
                    {
                        "ref": "official-2025|P1|3",
                        "level": "NB",
                        "confidence": "high",
                        "justification": "Áp dụng trực tiếp bảng nguyên hàm.",
                    },
                    {
                        "ref": "prov-2025|P1|7",
                        "level": "TH",
                        "confidence": "high",
                        "justification": "2 bước: tìm họ nguyên hàm và xác định hằng số C.",
                    },
                    {
                        "ref": "prov-2025|P1|12",
                        "level": None,
                        "confidence": "low",
                        "uncertainty": "Chưa đủ căn cứ gán mức độ.",
                    },
                ],
                "examples": [
                    {
                        "origin": "synthetic_not_corpus_evidence",
                        "status": "model_checks_passed_pending_teacher_review",
                        "key_agreement": True,
                        "level_agreement": True,
                        "model": "synthetic-fixture",
                        "target": {
                            "id": "ex-nh-th-1",
                            "part": "P1",
                            "level": "TH",
                            "qtype": "multiple_choice",
                            "topic": "Nguyên hàm",
                            "official_anchor_available": True,
                            "support_refs": ["prov-2025|P1|7"],
                        },
                        "sample": {
                            "id": "ex-nh-th-1",
                            "stem": "Cho F(x) là một nguyên hàm của f(x) = 3x^2 - 2x thỏa F(1) = 4. Tính F(2).",
                            "options": ["A. 8", "B. 6", "C. 10", "D. 4"],
                            "answers": ["A"],
                            "solution": "F(x) = x^3 - x^2 + C. Do F(1)=4 nên C=4. Vậy F(2)=8.",
                            "distractors": [
                                {
                                    "label": "B",
                                    "mistake": "Quên cộng hằng số C",
                                    "why_plausible": "Tính trực tiếp 2^3 - 2^2 = 4 hoặc cộng sai C.",
                                }
                            ],
                        },
                    }
                ],
                "unready_example_ids": [],
                "missing_example_ids": [],
            },
        ),
        (
            "eddc9ebdeb25",
            "xac-suat-co-dieu-kien",
            "Xác suất có điều kiện",
            {
                "schema_version": "research-topic-pack-v1",
                "origin": "synthetic-test-profile",
                "teacher_approved": False,
                "topic": {
                    "display_topic": "Xác suất có điều kiện",
                    "grades": [12],
                    "raw_topics": ["Xác suất có điều kiện", "Công thức Bayes"],
                    "patterns_by_class": {
                        "official": [
                            {
                                "part_kind": "true_false",
                                "topic": "Xác suất có điều kiện",
                                "grade": 12,
                                "construction": "Bài toán thực tế kiểm định gồm 4 mệnh đề a, b, c, d tăng dần mức độ từ xác suất cơ bản đến công thức xác suất toàn phần và Bayes.",
                                "wrong_options": "Nhầm P(A|B) với P(B|A) hoặc quên nhánh biến cố đối.",
                                "difficulty_source": "Phân biệt điều kiện thuận và điều kiện ngược Bayes.",
                                "discrimination": "high",
                                "typical_steps": 3,
                                "refs": [
                                    "official-2025|P2|4|a",
                                    "official-2025|P2|4|b",
                                    "official-2025|P2|4|c",
                                    "official-2025|P2|4|d",
                                ],
                                "paper_count": 1,
                                "row_count": 4,
                            }
                        ],
                        "provincial_third_party": [],
                    },
                    "classes": {},
                    "component_details": {},
                    "support_refs": [],
                },
                "construction_observations": [
                    {
                        "ref": f"official-2025|P2|4|{sub}",
                        "paper_id": "official-2025",
                        "year": 2025,
                        "part": "P2",
                        "idx": 4,
                        "sub": sub,
                        "printed_idx": f"4{sub}",
                        "topic": "Xác suất có điều kiện",
                        "grade": 12,
                        "discrimination": "high" if lvl == "VD" else "medium",
                        "given": "Hai dây chuyền sản xuất với tỉ lệ phế phẩm đã cho.",
                        "task": f"Xét tính đúng/sai của mệnh đề ({sub}) ở mức {lvl}.",
                        "reasoning": ["Lập sơ đồ hình cây.", "Áp dụng công thức Bayes."],
                        "steps": 3 if lvl == "VD" else 1,
                        "combines": ["Xác suất toàn phần", "Công thức Bayes"],
                        "cue_use": "Sơ đồ cây",
                        "difficulty_source": "Đảo chiều điều kiện Bayes.",
                        "wrong_options": "Nhầm P(A|B) và P(B|A).",
                        "wrong_option_details": [],
                        "evidence_class": "official",
                    }
                    for sub, lvl in (("a", "NB"), ("b", "TH"), ("c", "TH"), ("d", "VD"))
                ],
                "level_assignments": [
                    {
                        "ref": f"official-2025|P2|4|{sub}",
                        "level": lvl,
                        "confidence": "high",
                        "justification": f"Mệnh đề {sub} ở mức {lvl}.",
                    }
                    for sub, lvl in (("a", "NB"), ("b", "TH"), ("c", "TH"), ("d", "VD"))
                ],
                "examples": [],
                "unready_example_ids": [],
                "missing_example_ids": [],
            },
        ),
        (
            "e8d75b9fb4ed",
            "ung-dung-dao-ham-de-giai-bai-toan-toi-uu",
            "Ứng dụng đạo hàm để giải bài toán tối ưu",
            {
                "schema_version": "research-topic-pack-v1",
                "origin": "synthetic-test-profile",
                "teacher_approved": False,
                "topic": {
                    "display_topic": "Ứng dụng đạo hàm để giải bài toán tối ưu",
                    "grades": [12],
                    "raw_topics": ["Tối ưu", "Bài toán tối ưu thực tế"],
                    "patterns_by_class": {
                        "official": [
                            {
                                "part_kind": "short_answer",
                                "topic": "Ứng dụng đạo hàm để giải bài toán tối ưu",
                                "grade": 12,
                                "construction": "Lập hàm mục tiêu f(x) từ mô hình hình học/kinh tế thực tế và tìm GTLN/GTNN trên đoạn.",
                                "wrong_options": None,
                                "difficulty_source": "Sai lầm khi đặt điều kiện miền xác định thực tế của biến x hoặc làm tròn kết quả sớm.",
                                "discrimination": "high",
                                "typical_steps": 4,
                                "refs": ["official-2025|P3|5"],
                                "paper_count": 1,
                                "row_count": 1,
                            }
                        ],
                        "provincial_third_party": [],
                    },
                    "classes": {},
                    "component_details": {},
                    "support_refs": ["official-2025|P3|5"],
                },
                "construction_observations": [
                    {
                        "ref": "official-2025|P3|5",
                        "paper_id": "official-2025",
                        "year": 2025,
                        "part": "P3",
                        "idx": 5,
                        "sub": None,
                        "printed_idx": "5",
                        "topic": "Ứng dụng đạo hàm để giải bài toán tối ưu",
                        "grade": 12,
                        "discrimination": "high",
                        "given": "Bài toán kéo đường dây điện từ bờ ra đảo với chi phí trên bờ và dưới nước khác nhau.",
                        "task": "Tìm tổng chi phí nhỏ nhất (làm tròn đến hàng phần chục).",
                        "reasoning": [
                            "Đặt ẩn x là đoạn đi dưới nước hoặc trên bờ.",
                            "Thiết lập hàm chi phí C(x) và khảo sát đạo hàm C'(x) = 0.",
                        ],
                        "steps": 4,
                        "combines": ["Định lý Pythagore", "Đạo hàm hàm chứa căn", "GTLN-GTNN"],
                        "cue_use": "Mô hình hóa",
                        "difficulty_source": "Quên kiểm tra giá trị tại biên đoạn thực tế hoặc đổi sai đơn vị.",
                        "wrong_options": None,
                        "wrong_option_details": [],
                        "evidence_class": "official",
                    }
                ],
                "level_assignments": [
                    {
                        "ref": "official-2025|P3|5",
                        "level": "VD",
                        "confidence": "high",
                        "justification": "Mô hình hóa thực tế nhiều bước giải quyết vấn đề.",
                    }
                ],
                "examples": [],
                "unready_example_ids": [],
                "missing_example_ids": [],
            },
        ),
    ]

    topics_dir = root / "corpus" / "profiles" / "toan" / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)
    topic_index = []
    for tp_id, tp_key, tp_name, pack in topics:
        rel_path = f"topics/{tp_id}.json"
        raw_text = json.dumps(pack, ensure_ascii=False, indent=2) + "\n"
        (topics_dir / f"{tp_id}.json").write_text(raw_text, encoding="utf-8", newline="\n")
        topic_index.append(
            {
                "id": tp_id,
                "topic_key": tp_key,
                "topic": tp_name,
                "path": rel_path,
                "sha256": _sha256_bytes(raw_text),
                "clear_example_count": len(pack["examples"]),
                "pending_cell_count": 0,
            }
        )

    bundle = {
        "schema_version": "research-generation-profile-v1",
        "subject": "toan",
        "status": "draft_profile_from_transcription_and_synthetic_examples",
        "teacher_approved": False,
        "runtime_compatibility_verified": True,
        "source_evidence": [
            {"id": "official-2025", "class": "official"},
            {"id": "prov-2025", "class": "provincial_third_party"},
        ],
        "topic_packs": topic_index,
    }
    bundle_dir = root / "corpus" / "profiles" / "toan"
    bundle_text = json.dumps(bundle, ensure_ascii=False, indent=2) + "\n"
    (bundle_dir / "profile.bundle.json").write_text(bundle_text, encoding="utf-8", newline="\n")
    (bundle_dir / "completion.json").write_text(
        json.dumps({"unknown_level_rows": 1, "source_QA_clear": True}, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    curriculum_rows = [
        {
            "unit_id": "toan-12-c1",
            "subject": "Toán",
            "grade": 12,
            "kind": "chương",
            "title_vi": "Chương I. Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số",
            "parent_id": None,
            "status": "draft",
        },
        {
            "unit_id": "toan-12-c1-b2",
            "subject": "Toán",
            "grade": 12,
            "kind": "bài",
            "title_vi": "Bài 2. Giá trị lớn nhất và giá trị nhỏ nhất của hàm số, bài toán tối ưu",
            "parent_id": "toan-12-c1",
            "status": "draft",
            "keywords_vi": ["tối ưu", "giá trị lớn nhất", "giá trị nhỏ nhất", "đạo hàm"],
            "outcomes_vi": ["Giải quyết bài toán tối ưu thực tiễn bằng đạo hàm."],
        },
        {
            "unit_id": "toan-12-c4",
            "subject": "Toán",
            "grade": 12,
            "kind": "chương",
            "title_vi": "Chương IV. Nguyên hàm và tích phân",
            "parent_id": None,
            "status": "draft",
        },
        {
            "unit_id": "toan-12-c4-b11",
            "subject": "Toán",
            "grade": 12,
            "kind": "bài",
            "title_vi": "Bài 11. Nguyên hàm",
            "parent_id": "toan-12-c4",
            "status": "draft",
            "keywords_vi": ["nguyên hàm", "họ nguyên hàm", "bảng nguyên hàm"],
            "outcomes_vi": ["Tìm được nguyên hàm của các hàm số sơ cấp cơ bản."],
        },
        {
            "unit_id": "toan-12-c6",
            "subject": "Toán",
            "grade": 12,
            "kind": "chương",
            "title_vi": "Chương VI. Xác suất có điều kiện",
            "parent_id": None,
            "status": "draft",
        },
        {
            "unit_id": "toan-12-c6-b18",
            "subject": "Toán",
            "grade": 12,
            "kind": "bài",
            "title_vi": "Bài 18. Xác suất có điều kiện, công thức xác suất toàn phần và Bayes",
            "parent_id": "toan-12-c6",
            "status": "draft",
            "keywords_vi": ["xác suất có điều kiện", "công thức Bayes", "xác suất toàn phần"],
            "outcomes_vi": ["Tính được xác suất có điều kiện và áp dụng công thức Bayes."],
        },
    ]
    rag_data_dir = root / "rag" / "data"
    rag_data_dir.mkdir(parents=True, exist_ok=True)
    (rag_data_dir / "toan-12.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in curriculum_rows) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return root


class SyntheticPackRetrievalTests(unittest.TestCase):
    def setUp(self):
        _RELEASE_CACHE.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pack_dir = _build_synthetic_toan_pack(Path(self.temp.name))

    def test_load_profile_release_verifies_sha256_and_invalidates_cache_on_change(self):
        release1 = load_profile_release("toan", pack_dir=self.pack_dir)
        self.assertEqual(len(release1["topic_packs_by_id"]), 3)
        self.assertFalse(release1["cache_hit"])
        fp1 = release1["release_fingerprint"]

        # Second call with unchanged files hits cache
        release_cached = load_profile_release("toan", pack_dir=self.pack_dir)
        self.assertTrue(release_cached["cache_hit"])
        self.assertEqual(release_cached["release_fingerprint"], fp1)

        # Mutate a topic pack and update its manifest sha256 -> fingerprint must change automatically
        topic_file = self.pack_dir / "corpus" / "profiles" / "toan" / "topics" / "5fed66930d74.json"
        data = json.loads(topic_file.read_text(encoding="utf-8"))
        data["topic"]["raw_topics"].append("Nguyên hàm hàm hợp")
        new_raw = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        topic_file.write_text(new_raw, encoding="utf-8", newline="\n")

        bundle_file = self.pack_dir / "corpus" / "profiles" / "toan" / "profile.bundle.json"
        bundle = json.loads(bundle_file.read_text(encoding="utf-8"))
        for entry in bundle["topic_packs"]:
            if entry["id"] == "5fed66930d74":
                entry["sha256"] = _sha256_bytes(new_raw)
        bundle_file.write_text(
            json.dumps(bundle, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        release2 = load_profile_release("toan", pack_dir=self.pack_dir)
        self.assertFalse(release2["cache_hit"])
        self.assertNotEqual(fp1, release2["release_fingerprint"])
        self.assertIn(
            "Nguyên hàm hàm hợp",
            release2["topic_packs_by_id"]["5fed66930d74"]["raw_topics"],
        )

    def test_corrupted_topic_pack_sha256_raises_gap(self):
        topic_file = self.pack_dir / "corpus" / "profiles" / "toan" / "topics" / "5fed66930d74.json"
        topic_file.write_text('{"corrupted": true}\n', encoding="utf-8")
        with self.assertRaises(Gap) as ctx:
            load_profile_release("toan", pack_dir=self.pack_dir)
        self.assertEqual(ctx.exception.code, "malformed_document")

    def test_get_topic_pack_by_id_locator_and_name_returns_full_untruncated_content(self):
        rel = load_profile_release("toan", pack_dir=self.pack_dir)
        by_id = get_topic_pack(rel, "5fed66930d74")
        by_locator = get_topic_pack(rel, "profile:toan:5fed66930d74")
        by_name = get_topic_pack(rel, "Nguyên hàm", part="P1", level="TH")

        self.assertEqual(by_id["topic_pack_id"], "5fed66930d74")
        self.assertEqual(by_locator["topic_pack_id"], "5fed66930d74")
        self.assertEqual(by_name["topic_pack_id"], "5fed66930d74")
        self.assertTrue(by_id["curriculum_units"])
        self.assertTrue(by_id["patterns"])
        self.assertTrue(by_id["common_mistakes"])
        self.assertFalse(by_id["provenance"]["teacher_approved"])

        # Filtered by level="TH" excludes NB and None (unknown) observations
        obs_levels = {o["level"] for o in by_name["construction_observations"]}
        self.assertEqual(obs_levels, {"TH"})

    def test_retrieve_exam_context_handles_p1_p2_p3_vdc_and_gaps(self):
        payload = {
            "subject": "toan",
            "vdc_policy": "fallback_with_warning",
            "questions": [
                {
                    "question_id": "Q1_P1_TH",
                    "part": "P1",
                    "topic": "Nguyên hàm",
                    "objective": "Xác định nguyên hàm thỏa mãn điều kiện ban đầu",
                    "level": "TH",
                },
                {
                    "question_id": "Q2_P2_XS",
                    "part": "P2",
                    "topic": "Xác suất có điều kiện",
                    "objective": "Công thức xác suất toàn phần và Bayes",
                    "statement_levels": {"a": "NB", "b": "TH", "c": "TH", "d": "VDC"},
                },
                {
                    "question_id": "Q3_P3_OPT",
                    "part": "P3",
                    "topic": "Ứng dụng đạo hàm để giải bài toán tối ưu",
                    "objective": "Bài toán tối ưu thực tế",
                    "level": "VDC",
                },
                {
                    "question_id": "Q4_MISSING",
                    "part": "P1",
                    "topic": "Số phức và căn bậc hai số phức",
                    "level": "NB",
                },
            ],
        }
        response = retrieve_exam_context(payload, pack_dir=self.pack_dir)
        self.assertEqual(response.status, "partial_gap")
        self.assertEqual(response.summary["ready_questions"], 3)
        self.assertEqual(response.summary["gap_questions"], 1)

        q_map = {q["question_id"]: q for q in response.question_contexts}
        # Q1: Nguyên hàm P1 TH
        self.assertEqual(q_map["Q1_P1_TH"]["status"], "ready")
        self.assertEqual(
            q_map["Q1_P1_TH"]["matched_topic_packs"][0]["topic_pack_id"], "5fed66930d74"
        )
        self.assertTrue(q_map["Q1_P1_TH"]["examples"])
        self.assertGreater(len(q_map["Q1_P1_TH"]["reference_material_text"]), 500)

        # Q2: Xác suất P2 with a..d sibling grouping and VDC -> VD warning on d
        self.assertEqual(q_map["Q2_P2_XS"]["status"], "ready_with_warnings")
        self.assertEqual(
            q_map["Q2_P2_XS"]["resolved_level"]["statement_levels_effective"],
            {"a": "NB", "b": "TH", "c": "TH", "d": "VD"},
        )
        stmt_keys = {o["sub"] for o in q_map["Q2_P2_XS"]["construction_observations"]}
        self.assertEqual(stmt_keys, {"a", "b", "c", "d"})
        self.assertTrue(any(w["code"] == "vdc_mapped_to_vd" for w in q_map["Q2_P2_XS"]["warnings"]))

        # Q3: Tối ưu P3 with P3 difficulty traps extracted into common_mistakes
        self.assertEqual(q_map["Q3_P3_OPT"]["status"], "ready_with_warnings")
        self.assertTrue(q_map["Q3_P3_OPT"]["common_mistakes"])
        self.assertTrue(
            any(w["code"] == "vdc_mapped_to_vd" for w in q_map["Q3_P3_OPT"]["warnings"])
        )

        # Q4: Missing topic gap
        self.assertEqual(q_map["Q4_MISSING"]["status"], "gap")
        self.assertEqual(q_map["Q4_MISSING"]["gaps"][0]["code"], "topic_not_found")

        # Verify mas_intake_rag entries have provenance and question_id bindings
        self.assertEqual(len(response.mas_intake_rag), 3)
        for item in response.mas_intake_rag:
            self.assertIn(item["question_id"], {"Q1_P1_TH", "Q2_P2_XS", "Q3_P3_OPT"})
            self.assertIn("provenance", item)
            self.assertIn("source_id", item["provenance"])

    def test_vdc_strict_error_blocks_question(self):
        response = retrieve_exam_context(
            {
                "subject": "toan",
                "vdc_policy": "strict_error",
                "questions": [
                    {
                        "question_id": "Q_STRICT",
                        "part": "P3",
                        "topic": "Ứng dụng đạo hàm để giải bài toán tối ưu",
                        "level": "VDC",
                    }
                ],
            },
            pack_dir=self.pack_dir,
        )
        self.assertEqual(response.status, "gap")
        q_ctx = response.question_contexts[0]
        self.assertEqual(q_ctx["status"], "gap")
        self.assertEqual(q_ctx["gaps"][0]["code"], "level_vdc_not_in_scheme")

    def test_part_and_level_not_covered_gaps_and_include_unknown_level(self):
        # Pack e8d75b9fb4ed only has P3:VD
        part_gap = retrieve_exam_context(
            {
                "subject": "toan",
                "questions": [
                    {
                        "question_id": "Q_PART_GAP",
                        "topic": "Ứng dụng đạo hàm để giải bài toán tối ưu",
                        "part": "P2",
                        "statement_levels": {"a": "NB", "b": "TH", "c": "TH", "d": "VD"},
                    }
                ],
            },
            pack_dir=self.pack_dir,
        )
        self.assertEqual(part_gap.question_contexts[0]["gaps"][0]["code"], "part_not_covered")

        # Pack 5fed66930d74 has P1:NB, P1:TH, and 1 P1:unknown (no P1:VD)
        level_gap = retrieve_exam_context(
            {
                "subject": "toan",
                "include_unknown_level": False,
                "questions": [
                    {
                        "question_id": "Q_LVL_GAP",
                        "topic": "Nguyên hàm",
                        "part": "P1",
                        "level": "VD",
                    }
                ],
            },
            pack_dir=self.pack_dir,
        )
        self.assertEqual(level_gap.question_contexts[0]["gaps"][0]["code"], "level_not_covered")

        curriculum_only = retrieve_exam_context(
            {
                "allow_curriculum_only": True,
                "questions": [
                    {
                        "question_id": "Q_CURRICULUM",
                        "topic": "Nguyên hàm",
                        "part": "P1",
                        "level": "VD",
                    },
                ],
            },
            pack_dir=self.pack_dir,
        )
        context = curriculum_only.question_contexts[0]
        self.assertEqual(curriculum_only.status, "success")
        self.assertEqual(context["status"], "ready_with_warnings")
        self.assertEqual(context["resolved_level"]["effective"], "VD")
        self.assertTrue(context["curriculum_knowledge"])
        self.assertFalse(context["construction_patterns"])
        self.assertFalse(context["construction_observations"])
        self.assertFalse(context["examples"])
        self.assertIn("curriculum_only_for_level", {w["code"] for w in context["warnings"]})

        # When include_unknown_level=True, the unknown observation is returned with a warning
        with_unknown = retrieve_exam_context(
            {
                "subject": "toan",
                "include_unknown_level": True,
                "questions": [
                    {
                        "question_id": "Q_LVL_UNKNOWN",
                        "topic": "Nguyên hàm",
                        "part": "P1",
                        "level": "VD",
                    }
                ],
            },
            pack_dir=self.pack_dir,
        )
        q_unk = with_unknown.question_contexts[0]
        self.assertEqual(q_unk["status"], "ready_with_warnings")
        self.assertTrue(
            any(w["code"] == "unknown_level_observations_included" for w in q_unk["warnings"])
        )

    def test_http_endpoints_for_topic_packs_and_matrix_retrieve(self):
        server = create_server(0, pack_dir=self.pack_dir)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with urlopen(base + "/api/topic-packs", timeout=5) as resp:
                listing = json.load(resp)
            self.assertEqual(len(listing["topic_packs"]), 3)

            with urlopen(base + "/api/topic-packs/5fed66930d74", timeout=5) as resp:
                pack_resp = json.load(resp)
            self.assertEqual(pack_resp["topic_pack"]["topic_pack_id"], "5fed66930d74")
            self.assertEqual(len(pack_resp["topic_pack"]["construction_observations"]), 3)

            with self.assertRaises(HTTPError) as err:
                urlopen(base + "/api/topic-packs/missing-pack-id", timeout=5)
            self.assertEqual(err.exception.code, 404)

            with urlopen(base + "/api/matrix-sample", timeout=5) as resp:
                sample_matrix = json.load(resp)
            self.assertEqual(len(sample_matrix["questions"]), 22)

            req_body = json.dumps(
                {
                    "subject": "toan",
                    "questions": [
                        {
                            "question_id": "HTTP_Q1",
                            "part": "P1",
                            "topic": "Nguyên hàm",
                            "level": "TH",
                        }
                    ],
                }
            ).encode("utf-8")
            with urlopen(Request(base + "/api/matrix-retrieve", data=req_body), timeout=5) as resp:
                matrix_out = json.load(resp)
            self.assertEqual(matrix_out["status"], "success")
            self.assertEqual(matrix_out["question_contexts"][0]["question_id"], "HTTP_Q1")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


@unittest.skipUnless(_has_staging_rag_ref(), "origin/staging/rag ref not available locally")
class StagingToanAcceptanceTests(unittest.TestCase):
    def setUp(self):
        _RELEASE_CACHE.clear()

    def test_full_22_question_toan_thpt_matrix_and_acceptance_suite(self):
        sample = default_toan_thpt_matrix()
        parsed = parse_matrix_request(sample)
        self.assertEqual(len(parsed.questions), 22)

        report = evaluate_toan_acceptance()
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["summary"]["passed_cases"], report["summary"]["total_cases"])
        self.assertTrue(report["summary"]["sample_matrix_22q_passed"])
        self.assertGreater(report["summary"]["sample_matrix_min_reference_chars"], 150)

    def test_export_release_pack_and_reload_from_pack_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = export_release_pack(Path(tmp), subject="toan")
            self.assertEqual(manifest["topic_pack_count"], 71)
            reloaded = load_profile_release("toan", pack_dir=Path(tmp))
            self.assertEqual(len(reloaded["topic_packs_by_id"]), 71)
            pack = get_topic_pack(reloaded, "5fed66930d74", part="P1", level="TH")
            self.assertEqual(pack["display_topic"], "Nguyên hàm")
            self.assertTrue(pack["construction_observations"])

    def test_cli_topic_pack_and_acceptance_eval(self):
        cli_res = subprocess.run(
            [
                sys.executable,
                "-m",
                "rag_workflow.cli",
                "--topic-pack",
                "5fed66930d74",
                "--part",
                "P1",
                "--level",
                "TH",
            ],
            capture_output=True,
            encoding="utf-8",
        )
        self.assertEqual(cli_res.returncode, 0, cli_res.stderr)
        payload = json.loads(cli_res.stdout)
        self.assertEqual(payload["topic_pack"]["topic_pack_id"], "5fed66930d74")

        eval_res = subprocess.run(
            [sys.executable, "-m", "rag_workflow.eval", "--acceptance"],
            capture_output=True,
            encoding="utf-8",
        )
        self.assertEqual(eval_res.returncode, 0, eval_res.stderr)
        eval_payload = json.loads(eval_res.stdout)
        self.assertEqual(eval_payload["status"], "passed")


if __name__ == "__main__":
    unittest.main()

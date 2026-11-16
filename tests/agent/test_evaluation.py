from pathlib import Path

from exam_baseline.agent.evaluation import score


def test_curated_corpus_has_at_least_50_cases_and_no_injection_action():
    result = score(Path("evaluation/utterances_vi.jsonl"))
    assert result["total"] >= 50
    assert result["false_unsafe_actions"] == 0

"""Keep shared domain contracts free of transport and application dependencies."""

import ast

from tests.paths import ROOT


def test_core_does_not_import_runtime_features_or_transport():
    forbidden = (
        "exam_baseline.api",
        "exam_baseline.baseline",
        "exam_baseline.draft",
        "exam_baseline.pipeline",
        "exam_baseline.providers",
        "exam_baseline.benchmarks",
        "fastapi",
        "httpx",
        "PIL",
    )
    for path in (ROOT / "src/exam_baseline/core").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            imports = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else []
            )
            assert not any(
                name == prefix or name.startswith(prefix + ".")
                for name in imports
                for prefix in forbidden
            ), path


def test_runtime_agents_and_orchestration_do_not_import_benchmark_gold():
    for folder in ("pipeline/agents", "pipeline/orchestration", "pipeline/rendering", "api"):
        for path in (ROOT / "src/exam_baseline" / folder).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom):
                    assert not (node.module or "").startswith("exam_baseline.benchmarks"), path

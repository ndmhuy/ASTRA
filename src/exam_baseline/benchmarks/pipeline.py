"""Paired baseline/pipeline pilot runner. Human labels stay outside generation views."""

import argparse
import asyncio
import csv
import json
from pathlib import Path
from time import perf_counter

from exam_baseline.baseline.bootstrap import service_scope
from exam_baseline.benchmarks.models import HumanLabel, Manifest
from exam_baseline.benchmarks.scoring import summarize
from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion
from exam_baseline.pipeline.bootstrap import provider_scope, replay_providers, stage_settings
from exam_baseline.pipeline.contracts import PipelineRequest
from exam_baseline.pipeline.errors import PipelineFailure
from exam_baseline.pipeline.orchestration.orchestrator import Orchestrator


class BaselineReplay:
    name = "replay"
    model = "fixture-not-a-live-model"
    parameters = {}

    def __init__(self, path):
        self.exam = json.loads(path.read_text(encoding="utf-8"))["exam"]

    async def complete(self, request):
        return Completion(text=json.dumps(self.exam, ensure_ascii=False), model=self.model)


async def run(manifest_path: Path, output: Path, mode: str, labels_path: Path | None):
    manifest = Manifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    if len({c.id for c in manifest.cases}) != len(manifest.cases):
        raise ValueError("manifest case IDs must be unique")
    if output.exists():
        raise ValueError("benchmark output directory already exists")
    output.mkdir(parents=True)
    (output / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    attempts = []
    settings = Settings() if mode == "live" else Settings.for_offline()
    if mode == "live" and settings.provider != "chat_completions":
        raise ValueError("live benchmark requires a configured real provider")
    for case in manifest.cases:
        payload = PipelineRequest.model_validate_json(
            (manifest_path.parent / case.request).read_text(encoding="utf-8")
        )
        fixtures = manifest_path.parent / case.fixtures
        for repeat in range(1, manifest.repeats + 1):
            for system in ("baseline", "pipeline"):
                attempt_id = f"{system}/{case.id}/{repeat}"
                folder = output / system / case.id / str(repeat)
                record = dict(
                    attempt_id=attempt_id,
                    system=system,
                    track=case.track,
                    requested_questions=payload.request.matrix.question_count,
                    status="failed",
                    deterministic_passed=False,
                    accepted=False,
                    artifact_returned=False,
                    calls=0,
                    input_tokens=0,
                    output_tokens=0,
                    usage_unknown_calls=0,
                    known_cost_calls=0,
                    known_cost_usd=0.0,
                )
                start = perf_counter()
                try:
                    if system == "baseline" and case.track == "visual":
                        record["status"] = "unsupported"
                    elif system == "baseline":
                        provider = (
                            BaselineReplay(fixtures / "composer_01.json")
                            if mode == "replay"
                            else None
                        )
                        baseline_settings = stage_settings(settings, payload.workflow.composer)
                        async with service_scope(baseline_settings, provider) as service:
                            response = await service.generate(payload.request)
                        folder.mkdir(parents=True)
                        (folder / "response.json").write_text(
                            response.model_dump_json(indent=2), encoding="utf-8"
                        )
                        evaluation = response.evaluation
                        called = response.status != "context_failure"
                        record.update(
                            status="completed" if response.status == "success" else "failed",
                            deterministic_passed=bool(
                                response.validation and response.validation.passed
                            ),
                            accepted=response.status == "success",
                            artifact_returned=response.exam is not None,
                            question_ids=[q.id for q in response.exam.questions]
                            if response.exam is not None
                            else None,
                            calls=int(called),
                            models=evaluation.model,
                            input_tokens=evaluation.usage.input_tokens or 0,
                            output_tokens=evaluation.usage.output_tokens or 0,
                            usage_unknown_calls=int(
                                called
                                and (
                                    evaluation.usage.input_tokens is None
                                    or evaluation.usage.output_tokens is None
                                )
                            ),
                            known_cost_calls=int(evaluation.estimated_cost_usd is not None),
                            known_cost_usd=evaluation.estimated_cost_usd or 0.0,
                        )
                    else:
                        if mode == "replay":
                            result = await Orchestrator(replay_providers(fixtures)).run(
                                payload, folder
                            )
                        else:
                            async with provider_scope(payload, settings) as providers:
                                result = await Orchestrator(providers).run(payload, folder)
                        record.update(
                            status=result.execution_status,
                            deterministic_passed=result.deterministic_passed,
                            accepted=bool(result.machine_approved and result.final_latex),
                            artifact_returned=result.solutions is not None,
                            question_ids=[entry.question_id for entry in result.solutions.entries]
                            if result.solutions is not None
                            else None,
                            calls=len(result.calls),
                            input_tokens=sum(c.usage.input_tokens or 0 for c in result.calls),
                            output_tokens=sum(c.usage.output_tokens or 0 for c in result.calls),
                            usage_unknown_calls=sum(
                                c.usage.input_tokens is None or c.usage.output_tokens is None
                                for c in result.calls
                            ),
                            known_cost_calls=sum(
                                c.known_cost_usd is not None for c in result.calls
                            ),
                            known_cost_usd=sum(c.known_cost_usd or 0 for c in result.calls),
                            models=",".join(
                                sorted({c.model or c.requested_model for c in result.calls})
                            ),
                        )
                except (ValueError, OSError, PipelineFailure) as exc:
                    record["error"] = str(exc)
                record["latency_ms"] = (perf_counter() - start) * 1000
                attempts.append(record)
                with (output / "attempts.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    labels = (
        {
            k: HumanLabel.model_validate(v)
            for k, v in json.loads(labels_path.read_text(encoding="utf-8")).items()
        }
        if labels_path
        else {}
    )
    metrics = summarize(attempts, labels)
    report = {
        "mode": mode,
        "quality_measured": bool(labels),
        "live_quality_measured": mode == "live" and bool(labels),
        "note": "Replay verifies plumbing only. Human labels are required for accuracy. "
        "Compare text tracks directly; visual baseline is unsupported.",
        "metrics": metrics,
    }
    (output / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    columns = sorted({k for a in attempts for k in a})
    with (output / "attempts.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(attempts)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", choices=("replay", "live"), default="replay")
    parser.add_argument("--human-labels", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            asyncio.run(run(args.manifest, args.output, args.mode, args.human_labels)),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

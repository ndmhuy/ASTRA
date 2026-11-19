"""Print sanitized provider-call evidence after a UI-started live generation job."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import urlopen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("job_id", help="Job ID copied from the UI generation network response")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api")
    parser.add_argument("--run-root", type=Path, default=Path("runs/ui"))
    args = parser.parse_args()

    with urlopen(f"{args.base_url}/exams/{args.job_id}/status", timeout=10) as response:  # noqa: S310
        status = json.load(response)
    report_path = args.run_root / args.job_id / "_internal" / "result.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    safe_calls = [
        {
            key: call.get(key)
            for key in ("role", "revision", "status", "model", "usage", "latency_ms", "error")
            if call.get(key) is not None
        }
        for call in report.get("calls", [])
    ]
    print(
        json.dumps(
            {
                "jobId": args.job_id,
                "jobStatus": status.get("status"),
                "stage": status.get("stageName"),
                "error": status.get("error"),
                "executionStatus": report.get("execution_status"),
                "providerCalls": safe_calls,
                "providerCallCount": len(safe_calls),
                "containsCredentials": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

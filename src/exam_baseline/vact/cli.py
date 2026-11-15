"""Generate a 120-question V-ACT exam from the locked user template."""

from exam_baseline.thpt.cli import main as workflow_cli
from exam_baseline.vact.models import Request
from exam_baseline.vact.orchestrator import Orchestrator


def main():
    return workflow_cli(Orchestrator, Request, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

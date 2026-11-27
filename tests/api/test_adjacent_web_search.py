"""Verify allowlisted adjacent-topic web research and exam generation endpoints."""

import httpx
import pytest
from fastapi.testclient import TestClient

from exam_baseline.agent.contracts import VERSION
from exam_baseline.agent.research import (
    RESEARCH_VERSION,
    ResearchRequest,
    ResearchResponse,
    ResearchSource,
    search_adjacent_topic,
)
from exam_baseline.api.app import create_app
from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion
from exam_baseline.thpt.models import Question, Slot
from exam_baseline.ui.adjacent_workflow import AdjacentComposer, AdjacentRequest
from tests.api.test_ui_jobs import wait

HEADERS = {"X-Astra-Agent": VERSION}


def _research_payload(**changes):
    return {
        "schemaVersion": RESEARCH_VERSION,
        "workspaceId": "11111111-1111-1111-1111-111111111111",
        "clientMessageId": "22222222-2222-2222-2222-222222222222",
        "adjacentTopicId": "sat",
        "message": "Soạn đề SAT Math 4 câu",
        "count": 4,
        "minutes": 10,
        **changes,
    }


def test_agent_research_enforces_boundary_allowlist_and_returns_sources(tmp_path):
    calls = []

    async def fake_researcher(req: ResearchRequest) -> ResearchResponse:
        calls.append(req.adjacentTopicId)
        return ResearchResponse(
            clientMessageId=req.clientMessageId,
            adjacentTopicId=req.adjacentTopicId,
            topicLabel="SAT (Digital SAT)",
            formatId="adjacent-sat",
            subject="SAT",
            summary="Digital SAT Math practice summary.",
            suggestedCount=req.count or 10,
            suggestedMinutes=req.minutes or 20,
            sources=[
                ResearchSource(
                    title="Digital SAT Overview",
                    url="https://satsuite.collegeboard.org/digital",
                    snippet="Two sections: Reading & Writing and Math.",
                )
            ],
            searchMode="live_web",
        )

    app = create_app(
        Settings.for_offline().model_copy(update={"latex_cache_dir": tmp_path / "_tex-cache"}),
        ui_output_root=tmp_path,
        agent_researcher=fake_researcher,
    )
    with TestClient(app) as client:
        assert client.post("/agent/research", json=_research_payload()).status_code == 403
        assert (
            client.post(
                "/agent/research",
                json=_research_payload(adjacentTopicId="unknown_topic"),
                headers=HEADERS,
            ).status_code
            == 422
        )
        res = client.post("/agent/research", json=_research_payload(), headers=HEADERS)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["adjacentTopicId"] == "sat"
        assert data["suggestedCount"] == 4
        assert data["searchMode"] == "live_web"
        assert data["sources"][0]["url"] == "https://satsuite.collegeboard.org/digital"
        assert calls == ["sat"]


@pytest.mark.anyio
async def test_search_adjacent_topic_parses_ddg_and_falls_back_cleanly():
    ddg_html = (
        '<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fielts">'
        "IELTS <b>Format</b></a>"
        '<a class="result__snippet">Academic Reading includes 3 passages.</a>'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if "duckduckgo" in request.url.host:
            return httpx.Response(200, text=ddg_html)
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        req = ResearchRequest.model_validate(_research_payload(adjacentTopicId="ielts"))
        res = await search_adjacent_topic(req, client=client, allow_network=True)
    assert res.searchMode == "live_web"
    assert len(res.sources) == 1
    assert res.sources[0].title == "IELTS Format"
    assert res.sources[0].url == "https://example.org/ielts"

    offline = await search_adjacent_topic(req, allow_network=False)
    assert offline.searchMode == "offline_fallback"
    assert offline.sources == []
    assert "IELTS Academic" in offline.summary


def test_adjacent_exam_generation_works_in_demo_mode(tmp_path):
    app = create_app(
        Settings.for_offline().model_copy(
            update={"demo_mode": True, "latex_cache_dir": tmp_path / "_tex-cache"}
        ),
        ui_output_root=tmp_path,
    )
    with TestClient(app) as client:
        started = client.post(
            "/api/exams/generate",
            headers={"Idempotency-Key": "adj-demo-1"},
            json={
                "formatId": "adjacent-sat",
                "formatVersion": "1",
                "adjacentTopicId": "sat",
                "subject": "SAT",
                "grade": 12,
                "examType": "CUSTOM",
                "durationMinutes": 15,
                "itemCount": 4,
                "prompt": "Soạn đề SAT Math 4 câu",
                "uploadedFiles": [],
                "webSources": [
                    {
                        "title": "Digital SAT Math",
                        "url": "https://satsuite.collegeboard.org/digital",
                        "snippet": "Algebra and problem solving.",
                    }
                ],
            },
        )
        assert started.status_code == 202, started.text
        job_id = started.json()["jobId"]
        assert wait(client, job_id)["status"] == "completed"
        pkg = client.get(f"/api/exams/{job_id}").json()
        assert pkg["subject"] == "SAT"
        assert pkg["blueprint"]["examType"] == "CUSTOM"
        assert len(pkg["questions"]) == 4
        assert pkg["provenance"]["sourceType"] == "web_search"
        assert pkg["provenance"]["sources"][0]["url"] == "https://satsuite.collegeboard.org/digital"
        assert pkg["questions"][0]["sourceReference"] == "https://satsuite.collegeboard.org/digital"


class _ScriptedAdjacentProvider:
    name = model = "scripted"
    parameters = {}

    def __init__(self, role: str):
        self.role = role
        self.calls: list[dict] = []

    async def complete(self, request):
        import json

        payload = json.loads(request.user)
        self.calls.append(payload)
        if self.role == "composer":
            questions = [
                {
                    "id": slot["id"],
                    "stem": f"Practice IELTS question {idx + 1} on academic coherence.",
                    "choices": {"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"},
                    "statements": [],
                    "solution": f"Because Option A is right for item {idx + 1}.",
                    "answer": "A",
                    "illustration_request": None,
                }
                for idx, slot in enumerate(payload["slots"])
            ]
            return Completion(text=json.dumps({"questions": questions}), model="scripted")
        if self.role == "illustrator":
            return Completion(text=json.dumps({"drawings": []}), model="scripted")
        if self.role == "solver":
            entries = [
                {
                    "question_id": q["id"],
                    "reasoning": "Solved from stem and options only.",
                    "answer": "A",
                    "status": "solved",
                }
                for q in payload["questions"]
            ]
            return Completion(text=json.dumps({"entries": entries}), model="scripted")
        if self.role == "reviewer":
            ids = [q["id"] for q in payload["questions"]]
            return Completion(
                text=json.dumps({"decision": "approved", "checked_ids": ids, "issues": []}),
                model="scripted",
            )
        raise AssertionError(f"Unexpected role {self.role}")


def test_adjacent_exam_generation_live_providers_keeps_blind_solver(tmp_path):
    providers = {
        role: _ScriptedAdjacentProvider(role)
        for role in ("composer", "illustrator", "solver", "reviewer")
    }
    app = create_app(
        Settings.for_offline().model_copy(update={"latex_cache_dir": tmp_path / "_tex-cache"}),
        pipeline_providers=providers,
        ui_output_root=tmp_path,
    )
    with TestClient(app) as client:
        started = client.post(
            "/api/exams/generate",
            headers={"Idempotency-Key": "adj-live-1"},
            json={
                "formatId": "adjacent-ielts",
                "formatVersion": "1",
                "adjacentTopicId": "ielts",
                "subject": "IELTS",
                "grade": 12,
                "examType": "CUSTOM",
                "durationMinutes": 20,
                "itemCount": 4,
                "prompt": "Soạn đề IELTS Academic 4 câu",
                "uploadedFiles": [],
                "webSources": [
                    {
                        "title": "IELTS Academic Format",
                        "url": "https://ielts.org/take-a-test/test-types/ielts-academic-test",
                        "snippet": "Academic reading passages and MCQs.",
                    }
                ],
            },
        )
        assert started.status_code == 202, started.text
        job_id = started.json()["jobId"]
        assert wait(client, job_id)["status"] == "completed"
        pkg = client.get(f"/api/exams/{job_id}").json()
        assert pkg["subject"] == "IELTS"
        assert len(pkg["questions"]) == 4
        assert all(q["answerCheck"] == "matched" for q in pkg["questions"])
        assert pkg["provenance"]["sourceType"] == "web_search"
        assert any(w["code"] == "web_research_unverified" for w in pkg["warnings"])
        # Blind Solver must never receive the writer's key or private solution.
        solver_payload = providers["solver"].calls[0]
        assert all("answer" not in q and "solution" not in q for q in solver_payload["questions"])
        # Composer prompt data carries untrusted web sources for grounding.
        assert providers["composer"].calls[0]["web_sources"][0]["title"] == "IELTS Academic Format"
        # Unused import guard check
        assert AdjacentComposer and AdjacentRequest and Question and Slot

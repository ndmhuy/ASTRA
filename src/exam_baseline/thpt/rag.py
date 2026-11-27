"""Bind the THPT generation matrix to verified, per-question RAG evidence."""

from pathlib import Path
from textwrap import shorten

from exam_baseline.config import DEFAULT_RAG_CORPUS_REF
from exam_baseline.thpt.models import COUNTS, Request, Slot
from rag_workflow import default_toan_thpt_matrix, retrieve_exam_context
from rag_workflow.mas_adapter import render_thpt_prompt_evidence
from rag_workflow.models import CONFIG, VERSION, MatrixRetrievalResponse

DEFAULT_CORPUS_REF = DEFAULT_RAG_CORPUS_REF


class RagHandoffError(ValueError):
    def __init__(self, gaps):
        super().__init__("RAG could not supply context for the requested THPT matrix")
        self.gaps = gaps


def default_request() -> Request:
    ids = (f"{part}-{n}" for part, count in COUNTS.items() for n in range(1, count + 1))
    return Request(
        slots=[
            Slot(
                id=question_id,
                part=question["part"],
                topic=question["topic"],
                objective=question["learning_objective"],
                level=question.get("level") or "TH",
                statement_levels=[question["statement_levels"][label] for label in "abcd"]
                if question["part"] == "P2"
                else [],
            )
            for question_id, question in zip(
                ids, default_toan_thpt_matrix()["questions"], strict=True
            )
        ]
    )


def retrieval_matrix(request: Request) -> dict:
    return {
        "schema_version": VERSION,
        "subject": "toan",
        "vdc_policy": "fallback_with_warning",
        **({"allow_curriculum_only": True} if request.topic_review_instruction else {}),
        **CONFIG["thpt_mas_limits"],
        "questions": [
            {
                "question_id": slot.id,
                "part": slot.part,
                "topic": slot.topic,
                "learning_objective": slot.objective,
                "level": slot.level,
                "curriculum_unit_ids": slot.curriculum_unit_ids,
                **(
                    {"statement_levels": dict(zip("abcd", slot.statement_levels, strict=True))}
                    if slot.part == "P2"
                    else {}
                ),
            }
            for slot in request.slots
        ],
    }


def bind_retrieval(
    request: Request, retrieval: MatrixRetrievalResponse, *, variant_key: str = ""
) -> Request:
    if retrieval.status != "success" or retrieval.gaps:
        raise RagHandoffError(retrieval.gaps)
    contexts = {item["question_id"]: item for item in retrieval.question_contexts}
    entries = {item["question_id"]: item for item in retrieval.mas_intake_rag}
    expected = {slot.id for slot in request.slots}
    if (
        retrieval.schema_version != VERSION
        or contexts.keys() != expected
        or entries.keys() != expected
        or len(retrieval.question_contexts) != len(expected)
        or len(retrieval.mas_intake_rag) != len(expected)
    ):
        raise ValueError("Invalid RAG schema or THPT slot coverage")

    evidence = {}
    used_shapes: set[str] = set()
    for slot in request.slots:
        context, entry = contexts[slot.id], entries[slot.id]
        requested = context["requested"]
        statement_levels = dict(zip("abcd", slot.statement_levels, strict=False))
        curriculum_ids = [item["unit_id"] for item in context["curriculum_knowledge"]]
        if (
            context["status"] not in {"ready", "ready_with_warnings"}
            or requested["part"] != slot.part
            or requested["topic"] != slot.topic
            or requested["learning_objective"] != slot.objective
            or requested["level"] != slot.level
            or (requested["statement_levels"] or {}) != statement_levels
            or requested.get("curriculum_unit_ids", []) != slot.curriculum_unit_ids
            or (
                slot.curriculum_unit_ids
                and (not curriculum_ids or not set(curriculum_ids) <= set(slot.curriculum_unit_ids))
            )
            or entry["subject"] != "Toán"
            or entry["role"] != "content_support"
            or entry["text"] != context["reference_material_text"]
            or not entry["text"].strip()
            or entry["source_version"] != retrieval.release_info.get("corpus_snapshot")
        ):
            raise ValueError(f"Invalid RAG context for {slot.id}")
        evidence[slot.id] = {
            "text": render_thpt_prompt_evidence(context, used_shapes, variant_key=variant_key)
            if (
                context.get("construction_patterns")
                or context["curriculum_knowledge"]
                or context.get("construction_observations")
                or context.get("examples")
            )
            else shorten(
                entry["text"], width=CONFIG["thpt_prompt_limits"]["field_chars"], placeholder=" …"
            ),
            "source_ids": entry["topic_ids"],
            "source_locator": entry["locator"],
            "source_version": entry["source_version"],
            "curriculum_unit_ids": curriculum_ids,
            "warnings": context["warnings"],
        }
    return Request.model_validate({**request.model_dump(), "rag_evidence": evidence})


def retrieve_request(
    request: Request,
    *,
    corpus_ref: str = DEFAULT_CORPUS_REF,
    pack_dir: Path | None = None,
    variant_key: str = "",
) -> Request:
    retrieval = retrieve_exam_context(
        retrieval_matrix(request), ref=corpus_ref, repo=Path.cwd(), pack_dir=pack_dir
    )
    return bind_retrieval(request, retrieval, variant_key=variant_key)

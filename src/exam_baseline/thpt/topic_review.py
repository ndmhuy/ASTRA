"""Review independently scored units, then replace only those outside the requested scope."""

import re

from pydantic import ConfigDict, Field, create_model

from exam_baseline.core.models import Model, Text
from exam_baseline.thpt.agents import QUESTION_FORMAT, Agent
from exam_baseline.thpt.models import Question, Statement
from rag_workflow.query_parser import normalize

# For a single-topic integral worksheet, require an observable integral step in the
# private solution of each statement. The independent semantic verdict is still required.
_INTEGRAL_STEP = re.compile(
    r"\\(?:i{1,3}nt|oint)\s*(?:\\limits\s*)?[_^]"
    r"|∫\s*[₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹_^]|\btich phan xac dinh\b"
    r"|\bnewton\s*[-–]?\s*leibniz\b"
)


class Verdict(Model):
    reasoning: Text
    on_topic: bool = Field(strict=True)


class Finding(Verdict):
    address: Text


class Audit(Model):
    findings: list[Finding] = Field(min_length=1)


class AddressVerdicts(Model):
    # Earlier checkpoints stored the internal unit_N property names.
    model_config = ConfigDict(populate_by_name=True)


class TopicReviewer(Agent):
    role = "reviewer"
    response = Audit
    instruction = """Assess each supplied address independently. For each, state the actual
mathematical operation needed for its answer, then decide whether this tests the teacher's
requested topic (and the slot objective). A scenario's theme, an integral elsewhere in the
stem, or another subpart's reasoning never qualifies a statement. If a student can answer
using only a prerequisite such as a sign test, exponent algebra or taking a derivative,
mark false for an integral practice request. Genuine integral properties, interpretation
and area/volume/accumulation applications count. Respond once per supplied address.
Distinguish the shortest sufficient method for THIS claim from any method for the scenario.
For a definite integral request, finding or checking an antiderivative alone is outside scope.
For broad or stylistic requests judge against the assigned slot. Write reasoning in Vietnamese."""

    def contract(self, data):
        # Use required properties so the model cannot merge addresses into a single verdict.
        verdicts = create_model(
            "TopicVerdicts",
            __base__=AddressVerdicts,
            **{f"unit_{i}": (Verdict, Field(alias=addr)) for i, addr in enumerate(data["units"])},
        )
        return create_model("TopicReview", __base__=Model, verdicts=(verdicts, ...))

    @staticmethod
    def to_audit(response):
        return Audit(
            findings=[
                Finding(address=address, **verdict)
                for address, verdict in response.verdicts.model_dump(by_alias=True).items()
            ]
        )


class StatementWriter(Agent):
    role = "composer"
    response = Statement
    instruction = (
        """Rewrite ONLY target_address under the unchanged stem. Return one statement,
its truth value and worked solution. The replacement must require using the assigned topic,
respect the given level, and be independently judgeable without using sibling answers.
Use the shared givens; do not redefine their variables or functions in the statement.
Test a different quantity or property from each sibling, even if their phrasing differs.
For a definite integral request, include a definite
integral or a concrete application of one, beyond checking an antiderivative. Use Vietnamese.
"""
        + QUESTION_FORMAT
    )


class QuestionWriter(Agent):
    role = "composer"
    response = Question
    instruction = (
        """Rewrite this one off-topic question to require the assigned topic.
Preserve its ID, part and level. Supply its key and worked solution in Vietnamese.
"""
        + QUESTION_FORMAT
    )


def units(question):
    if question.statements:
        return {
            f"{question.id}.{label}": {"stem": question.stem, **statement.model_dump()}
            for label, statement in zip("abcd", question.statements, strict=True)
        }
    return {question.id: question.model_dump()}


async def review_topic(call, request, questions, revision, history):
    slots = {s.id: s for s in request.slots}
    context = {"teacher_request": request.topic_review_instruction}
    pending = {addr: data for q in questions for addr, data in units(q).items()}
    integral_only = all(normalize(s.topic).strip() == "tich phan" for s in slots.values())
    for attempt in range(request.topic_repair_limit + 1):
        reviewer = TopicReviewer()
        response = await call(
            reviewer,
            {
                **context,
                "units": pending,
                "slots": [
                    slots[key].model_dump()
                    for key in dict.fromkeys(a.split(".")[0] for a in pending)
                ],
            },
            revision,
        )
        audit = reviewer.to_audit(response)
        findings = {item.address: item for item in audit.findings}
        for addr, item in pending.items():
            if (
                integral_only
                and "." in addr
                and not _INTEGRAL_STEP.search(normalize(item["solution"]))
            ):
                findings[addr].on_topic = False
                findings[addr].reasoning = (
                    "Lời giải riêng của ý chưa thể hiện bước dùng tích phân. Viết lại ý để "
                    "phải lập, tính hoặc áp dụng một tính chất của tích phân; trình bày bước đó."
                )
        history.append(audit.model_dump())
        failed = {addr: f.reasoning for addr, f in findings.items() if not f.on_topic}
        if not failed:
            return questions
        if attempt == request.topic_repair_limit:
            raise ValueError("Vẫn còn câu hoặc ý ngoài chuyên đề: " + ", ".join(failed))
        pending = {}
        for index, q in enumerate(questions):
            feedback = {addr: failed[addr] for addr in units(q) if addr in failed}
            if not feedback:
                continue
            data = {
                **context,
                "slot": slots[q.id].model_dump(),
                "question": q.model_dump(),
                "rewrite": feedback,
            }
            if q.statements:
                statements = list(q.statements)
                for addr, reason in feedback.items():
                    label = addr[-1]
                    statements["abcd".index(label)] = await call(
                        StatementWriter(),
                        {
                            **context,
                            "slot": data["slot"],
                            "question": q.model_copy(
                                update={"statements": statements}
                            ).model_dump(),
                            "target_address": addr,
                            "reason": reason,
                            "target_level": slots[q.id].statement_levels["abcd".index(label)],
                        },
                        revision,
                    )
                summary = "\n".join(
                    f"{label}) {s.solution}" for label, s in zip("abcd", statements, strict=True)
                )
                revised = q.model_copy(update={"statements": statements, "solution": summary})
            else:
                revised = await call(QuestionWriter(), data, revision)
                if revised.id != q.id:
                    raise ValueError("Writer trả sai mã câu cần sửa.")
            questions[index] = revised
            pending.update({addr: unit for addr, unit in units(revised).items() if addr in failed})
    raise AssertionError("unreachable")

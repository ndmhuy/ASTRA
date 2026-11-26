"""Version 1 practice-paper profiles based on Decision 764/QĐ-BGDĐT."""

from dataclasses import dataclass
from typing import Literal

from pydantic import Field, model_validator

from exam_baseline.thpt.models import Request, Slot

FormatId = Literal[
    "thpt-physics",
    "thpt-chemistry",
    "thpt-biology",
    "thpt-history",
    "thpt-geography",
    "thpt-english",
]
SOURCE = (
    "https://locthanhbaoloc.lamdong.edu.vn/home/uploads/news/2024_09/quyet-dinh-so-764_qd-bgddt.pdf"
)
DURATION = 50
SECTION_SPEC = {
    "P1": ("mcq", "Trắc nghiệm nhiều lựa chọn", "Chọn một đáp án A, B, C hoặc D."),
    "P2": ("true_false", "Trắc nghiệm đúng/sai", "Chọn đúng hoặc sai cho từng ý a, b, c, d."),
    "P3": ("short_answer", "Trả lời ngắn", "Điền đáp án số vào ô trả lời."),
}


@dataclass(frozen=True)
class Profile:
    subject: str
    counts: tuple[int, int, int]
    topics: tuple[str, ...]
    checks: str

    @property
    def sections(self):
        return {part: n for part, n in zip(SECTION_SPEC, self.counts, strict=True) if n}

    @property
    def ids(self):
        return [f"{part}-{i}" for part, n in self.sections.items() for i in range(1, n + 1)]


SCIENCE_COUNTS = (18, 4, 6)
PROFILES = {
    "thpt-physics": Profile(
        "Vật Lý",
        SCIENCE_COUNTS,
        ("Vật lí nhiệt", "Khí lí tưởng", "Từ trường và cảm ứng điện từ", "Vật lí hạt nhân"),
        "Verify SI conversions, signs, graphs, units, and explicitly stated rounding. "
        "Supply constants and conventions. For motional emf, specify the rod's orientation "
        "relative to velocity and magnetic field. Keep nuclear items on classroom calculations.",
    ),
    "thpt-chemistry": Profile(
        "Hóa Học",
        SCIENCE_COUNTS,
        (
            "Ester và lipid",
            "Carbohydrate",
            "Hợp chất chứa nitrogen",
            "Polymer",
            "Pin điện và điện phân",
            "Kim loại và phức chất",
        ),
        "Check atom and charge balance, stoichiometry, stated conditions, concentration and units. "
        "Use ordinary classroom examples and theoretical problems.",
    ),
    "thpt-biology": Profile(
        "Sinh Học",
        SCIENCE_COUNTS,
        (
            "Di truyền phân tử",
            "Di truyền nhiễm sắc thể",
            "Di truyền quần thể",
            "Tiến hóa",
            "Sinh thái học",
        ),
        "Check inheritance assumptions, probabilities and biological terminology. "
        "Use textbook concepts and harmless organisms or fictional traits. "
        "Avoid pathogen work, engineering protocols, or DNA synthesis instructions.",
    ),
    "thpt-history": Profile(
        "Lịch Sử",
        (24, 4, 0),
        (
            "Liên hợp quốc và trật tự thế giới",
            "ASEAN",
            "Cách mạng tháng Tám",
            "Các cuộc kháng chiến Việt Nam",
            "Đổi mới và đối ngoại",
        ),
        "Verify chronology, names, and historical context. For true/false provide a short "
        "self-contained context; distinguish evidence from interpretation. "
        "Never fabricate quotations or source citations.",
    ),
    "thpt-geography": Profile(
        "Địa Lý",
        SCIENCE_COUNTS,
        (
            "Địa lí tự nhiên Việt Nam",
            "Dân cư và đô thị hóa",
            "Các ngành kinh tế",
            "Các vùng kinh tế",
            "Biển đảo Việt Nam",
        ),
        "Check units, data years, denominators, charts and rounding. "
        "Use clearly labelled hypothetical data or data supplied by the teacher. "
        "For a real named place, label synthetic figures as hypothetical in the stem itself. "
        "Do not invent official statistics or require unseen maps.",
    ),
    "thpt-english": Profile(
        "Tiếng Anh",
        (40, 0, 0),
        ("Cloze", "Text organization", "Reading comprehension"),
        "Write student materials in English with original passages. Check grammar, "
        "cohesion and evidence in the passage. Test every cloze option in context, especially "
        "competing verb tenses. Each item must have exactly one defensible answer.",
    ),
}

ENGLISH_GROUPS = (
    ("E1", 1, 6, "cloze", "Complete the numbered blanks in the advertisement."),
    ("E2", 7, 12, "cloze", "Complete the numbered blanks in the leaflet."),
    ("E3", 13, 17, "ordering", "Choose the best order of the sentences or lines."),
    ("E4", 18, 22, "cloze", "Complete the numbered blanks in the passage."),
    ("E5", 23, 30, "reading", "Read the passage and answer the following questions."),
    ("E6", 31, 40, "reading", "Read the passage and answer the following questions."),
)


def batches(format_id):
    if format_id == "thpt-english":
        return {
            group: [f"P1-{n}" for n in range(first, last + 1)]
            for group, first, last, _, _ in ENGLISH_GROUPS
        }
    result = {}
    for part, count in PROFILES[format_id].sections.items():
        for offset in range(0, count, 8):
            result[f"{part}_{offset + 1}"] = [
                f"{part}-{n}" for n in range(offset + 1, min(count, offset + 8) + 1)
            ]
    return result


class SubjectRequest(Request):
    template_id: Literal["thpt_subject_v1"] = "thpt_subject_v1"
    format_id: FormatId
    composer_concurrency: Literal[1] = 1
    slots: list[Slot] = Field(min_length=28, max_length=40)

    @model_validator(mode="after")
    def valid_matrix(self):
        if [slot.id for slot in self.slots] != PROFILES[self.format_id].ids:
            raise ValueError("Question IDs and order must match the subject profile")
        if self.rag_evidence:
            raise ValueError("This subject profile does not use the math RAG corpus")
        for slot in self.slots:
            if not slot.id.startswith(slot.part + "-") or len(slot.statement_levels) != (
                4 if slot.part == "P2" else 0
            ):
                raise ValueError("Wrong part or number of statement levels")
        return self


def subject_request(format_id, prompt):
    profile = PROFILES[format_id]
    slots = []
    group_topics = {
        "cloze": "Cloze",
        "ordering": "Text organization",
        "reading": "Reading comprehension",
    }
    english_topics = {
        f"P1-{n}": group_topics[kind]
        for _, first, last, kind, _ in ENGLISH_GROUPS
        for n in range(first, last + 1)
    }
    for index, qid in enumerate(profile.ids):
        part = qid.split("-")[0]
        slots.append(
            Slot(
                id=qid,
                part=part,
                topic=english_topics[qid]
                if format_id == "thpt-english"
                else profile.topics[index % len(profile.topics)],
                objective="Assess the slot topic with one clear, well-specified task.",
                level=("NB", "TH", "VD")[index % 3],
                statement_levels=["NB", "TH", "TH", "VD"] if part == "P2" else [],
            )
        )
    return SubjectRequest(format_id=format_id, slots=slots, requirements=[prompt] if prompt else [])


def subject_catalog():
    score_by_correct = [0, 0.1, 0.25, 0.5, 1]
    for format_id, profile in PROFILES.items():
        sections = []
        for part, count in profile.sections.items():
            kind, title, instructions = SECTION_SPEC[part]
            section = dict(id=part, title=title, type=kind, count=count, instructions=instructions)
            if part == "P2":
                section.update(statementsPerQuestion=4, scoreByCorrectStatements=score_by_correct)
            else:
                section["pointsPerQuestion"] = 0.25
            sections.append(section)
        yield {
            "schemaVersion": "exam-format-v1",
            "id": format_id,
            "version": "1",
            "displayName": f"{profile.subject} THPT",
            "examType": "THPT_STANDARD",
            "engine": "thpt_subject_v1",
            "subjects": [profile.subject],
            "grades": [12],
            "durationMinutes": DURATION,
            "totalQuestions": len(profile.ids),
            "totalScore": 10,
            "sections": sections,
            "available": True,
            "editableFields": ["prompt"],
            "lockedFields": ["subject", "grade", "durationMinutes", "itemCount", "sections"],
            "exportFormats": ["tex", "json", "pdf"],
            "requires": ["chat_completions_provider"],
        }

# MAS intake and reviewed exam export

## 1. Input policy

`exam_baseline.intake` accepts one JSON object with `schema_version=mas-intake-v1`,
`chatbot`, and `rag`. The chatbot must supply a resolved `generate_exam` intent:
grade (1–12), curriculum, textbook and publication year, language, subject,
title, topics and learning objectives, question count, exact topic/type/difficulty
distributions, score budget, duration, exam format, answer format, audience, and
optional accommodations. The existing `ExamMatrix` validates the numerical
constraints. Ambiguous or missing required fields cause a validation error; the
encoder does not guess them.

Each RAG passage needs an ID, text, role, source title, locator, subject, grade,
textbook, textbook year, and topic IDs. Its subject/grade/book/year must match the
chatbot scope; its topic IDs must belong to the matrix. Each requested topic must
have `content_support` evidence. `form_example` alone cannot support content.
Passage text is untrusted context, never a policy instruction. The adapter writes
the current `MiniRequest` contract; it does not require the RAG team's internal
schema to change.

```powershell
python -m exam_baseline.intake --input intake.json --output mini_request.json
python -m exam_baseline.mini_cli --request mini_request.json --output runs/exam1
python -m exam_baseline.intake --input intake.json --output pipeline_request.json --pipeline
python -m exam_baseline.pipeline.cli --request pipeline_request.json --output runs/pipeline1
```

See `examples/mas_intake.json` for a full input. The draft still needs Solver and
Reviewer work. Passing the structural checks does not prove the mathematics,
curriculum fit, grade level, factual accuracy, visual meaning, or answer key.

## 2. Review before export

```powershell
python -m exam_baseline.exporter --draft runs/exam1 --prepare-review runs/review.json
```

This copies the Composer's *proposed* answers and solutions into an unapproved
file. A reviewer checks every question, choice, solution, image, source, score,
and requested constraint; corrects the JSON; fills `reviewer`; and sets
`approved` to `true`. If a question or figure must change, generate a new draft
and review its new revision. Keep the review JSON private with the answer key.

```powershell
python -m exam_baseline.exporter --draft runs/exam1 --review runs/review.json --output runs/final1
```

The exporter writes `de_thi.pdf`, `de_thi.docx`, `dap_an.pdf`, and `dap_an.docx`.
It rejects an invalid draft, changed student view, changed or missing figure,
mismatched draft/revision/hash, missing answer, invalid multiple-choice key,
unapproved review, and LaTeX stems that cannot be faithfully rendered by this
PDF/DOCX backend. PDF and DOCX are built from the same section list, with no
answers or solutions in student files. The hash binds the review to exact student
JSON bytes; any edit to the JSON requires a new review file.

These checks guarantee structural consistency and file integrity, not independent
semantic correctness. A human or a later Solver/Reviewer stage must validate
content before setting `approved=true`.

## 3. Benchmark

The pipeline benchmark reports question accuracy as `correct_question_yield`, and
now also reports `format_question_yield`, `valid_question_yield`, and
`test_fit_question_yield`. Each uses reviewed question counts over requested
question counts; failed or missing artifacts score zero. Labels for each axis are
optional, and the corresponding audit coverage is reported separately. An
unlabeled axis remains `null`, never a fabricated perfect score. `valid` means
the question and key are internally consistent and answerable; `test_fit` means
the item matches the requested grade, curriculum, scope and difficulty. Labels
must be created independently of model generation. Replay fixtures test wiring,
not real-world accuracy or test fit.

# ASTRA: A Multi-Agent System for Exam Generation and Verification
**Team:** Trial and Success  
**Course:** CSC10014 - Computational Thinking | HCMUS / APCS  
**Original report date:** 21 October 2026 | **Prototype and roadmap update:** 21 November 2026

## Team Members
| Student ID | Full name |
|---|---|
| 25125004 | Tran Ngoc Tuan Anh |
| 25125061 | Chau Tan Phat |
| 25125087 | Le Tran Hoang Long |
| 25125083 | Nguyen Dinh Minh Huy |
| 25125017 | Nguyen Dang Khang |
| 25125067 | Nguyen Phu Trong |
| 25125071 | Le Quynh Anh |

---

## Cover / Purpose

A Multi-Agent System for Exam Generation and Verification | Computational Thinking | CSC10014 | 21 October 2026

### Purpose

This report is for course reviewers and project contributors. It records the October design decisions and computational thinking analysis, describes the working prototype, and sets out the next MVP milestones and evaluation plan.

### Evidence standard

The October notes document the team's reasoning. The repository and recorded runs support the implementation and evaluation claims in this update. Numerical thresholds from the planning notes remain targets. See the [evidence register](#evidence-register) for the sources.

<!-- PAGE BREAK -->

---

## 01 | Executive Summary

*ASTRA addresses the work of producing a trustworthy, usable examination.*

### Problem

Traditional exam preparation requires collecting material, selecting learning objectives, drafting questions, reviewing answers, balancing difficulty and formatting printable documents. Generic AI accelerates drafting but can create incorrect answers, unsupported information and inconsistent blueprints.

### Approach

ASTRA turns a structured exam blueprint into a draft and a review report. Its four-agent pipeline drafts questions, renders figures, solves the questions independently, and flags defects for review. The web backend retrieves THPT math evidence and passes it to generation. The general CLI accepts evidence through a separate intake step. The teacher decides whether to use the paper.

### CT contribution

Decomposition assigns each stage a clear job. Pattern recognition identifies a shared exam workflow across subjects. Abstraction captures common requirements in blueprints and profiles. Algorithm design governs validation, revision, and review.

### Status

On the integration branch, teachers can generate THPT math drafts in the browser, inspect the answers and PDF preview, and approve a revision for download. The repository also provides CLI workflows for THPT math and V-ACT, a general four-agent pipeline, and a single-agent baseline. Measured results cover fixture replay and retrieval. A matched live comparison with independently reviewed papers is the next step toward estimating quality, teacher effort, and cost. [Evaluation evidence](#measured-prototype-checks)

<!-- PAGE BREAK -->

---

## 02 | Background and Educational Context

*Why assessment preparation is an attractive automation problem.*

### Traditional workflow

Teachers collect items from question banks and previous papers, consult curricula, adjust difficulty, edit wording, create answer keys and export the result. Each handoff can require separate tools and repeated checking.

### The new bottleneck

A general-purpose chatbot can draft questions rapidly, but its fluency does not certify mathematical correctness, factual grounding, curriculum fit or practical completion time. The team called this failure mode “exam slop.”

### Access and responsibility

Both expert and inexperienced AI users can spend significant time specifying prompts and checking results. Reducing user effort must not mean removing teacher responsibility: final review remains part of the intended workflow.

### External context

The team collected education and AI-adoption reading, including TALIS-related material. The presentation references OECD TALIS 2024 statistics but notes that lesson-preparation measures are not direct measurements of exam-writing time.

<!-- PAGE BREAK -->

---

## 03 | Problem Definition

*From an ambiguous request to a bounded computational problem.*

### Working formulation

Given a teacher’s intent, syllabus, sample questions, blueprint and constraints, produce an exam package that is correct, appropriately balanced, traceable, formatted and ready for human approval.

### Constraint handling

A teacher's request may omit item counts, cognitive levels, topics, scoring rules, duration, or evidence requirements. ASTRA expresses these constraints in a blueprint and checks them in code. The benchmark will measure how often a direct prompt satisfies the same constraints.

### Failure categories

Content correctness: wrong reasoning or answers. Source integrity: invented passages or facts. Structure: incorrect counts, marks or question types. Pedagogy: mismatched objectives, repetitive items or poorly calibrated difficulty. Delivery: missing figures, malformed formatting or impractical length.

### Design principle

Treat exam creation as a sequence of transformations and checks, rather than as a single text-generation task.

<!-- PAGE BREAK -->

---

## 04 | Stakeholders, Boundaries and Priorities

*Scope decisions shaped the feasibility of the project.*

### Primary users

High-school teachers and tutors who repeatedly prepare structured assessments, including users with limited experience writing AI prompts. Students were considered as a secondary audience for practice and mock exams.

### Assessment scope

The team discussed Vietnamese high-school graduation practice, competency-assessment formats and blueprint-based multiple-choice examinations. Broader lesson-planning and school-management tasks were explored but moved outside the immediate core.

### Priorities

Accuracy and pedagogical validity; usability and low prompt burden; then manageable unit cost. These priorities must be considered together: fast but untrustworthy generation transfers work back to the teacher.

### Non-goals for the core demonstration

Fully autonomous grading of subjective writing, comprehensive personalized learning analytics, and replacing a teacher’s final decision are not required to demonstrate the central CT approach.

<!-- PAGE BREAK -->

---

## 05 | Early Brainstorming: Ideas Retained and Deferred

*The first phase deliberately explored a broader education assistant.*

### Original feature landscape

Meeting records list exam creation, sample matrices, lesson-plan generation, grading, an AI assistant for repeated teacher work and a wider educational automation ecosystem.

### Why breadth was problematic

Each function introduces a separate input model, success criterion and evaluation problem. A broad “AI for teachers” promise would obscure what the group actually intended to solve and make computational-thinking claims harder to verify.

### Decision

Center the assessed artifact on exam generation and verification. Preserve other features as future directions or related modules rather than treating them as delivered core functionality.

### What was learned

Scope reduction was not the absence of ambition. It was an abstraction decision: identify the common value proposition and prioritize a tractable workflow whose inputs, outputs and quality checks can be specified.

<!-- PAGE BREAK -->

---

## 06 | Prototype Status and Entry Points

The integration branch connects the React teacher workspace to FastAPI, pinned THPT retrieval, and the native exam engine. The local setup supports the integrated app and standalone CLI demos. [Run the web app](../../README.md#run-the-web-app)

| Component | Current behavior |
| --- | --- |
| Integrated web app | The browser starts a THPT math job with 22 questions and a 90-minute duration. It shows progress and retrieval warnings, supports editing or regenerating questions, and previews the PDF before revision approval. |
| Exam generation | The single-agent baseline returns a Markdown report. The four-agent CLI pipeline returns a LaTeX draft with a review checklist and intermediate artifacts. |
| Template workflows | Dedicated CLIs generate practice papers and answer material for THPT math and V-ACT using fixed templates and editable question matrices. |
| Retrieval and intake | The web job resolves the matrix, retrieves per-question Topic Packs from the pinned corpus, and passes part-specific evidence into the THPT engine. The standalone intake command validates evidence for the general CLI pipeline. |
| Teacher review and export | Web approval binds PDF, LaTeX, and answer JSON downloads to an exam revision. A separate exporter produces PDF and DOCX for supported Composer and Illustrator draft packages. |

[Connected THPT UI](../integration/CONNECTED_THPT_UI.md) · [THPT math CLI](../guides/THPT_TOAN.md) · [V-ACT CLI](../guides/VACT.md) · [Reviewed PDF/DOCX export](../MAS_INTAKE_AND_EXPORT.md)

<!-- PAGE BREAK -->

---

## 07 | Chronology: 20–21 October

*Feedback changed how the team explained its reasoning.*

### 20 October: pattern recognition

Discussion connected a classroom analogy about repeated musical patterns to a more consequential observation: official exam creation separates drafting from independent checking and approval. The team began treating this organizational pattern as reusable logic.

### 21 October: presentation revision

Messages discussed simplifying jargon, emphasizing the actual problem and explaining patterns in ordinary language. Team notes also raised unresolved dataset definitions, difficulty balance, figure generation and the need to start with reasoning rather than technology.

### Interpretation

The revisions show an important shift: a technology inventory is not a CT explanation. The report therefore traces observation → pattern → generalization → algorithmic response for each design decision.

### Evidence limitation

Dated notes support a sequence of discussions; they do not establish exact authorship or timing for every slide revision. Folder labels alone should not be treated as creation timestamps.

<!-- PAGE BREAK -->

---

## 08 | Computational Thinking I: Decomposition

*Break the task into independent responsibilities and explicit contracts.*

### Functional decomposition

1. Interpret teacher intent. 2. Parse constraints and syllabus. 3. Construct a question blueprint. 4. Retrieve relevant reference material. 5. Draft items and candidate keys. 6. Validate structure and content. 7. Independently solve. 8. Revise. 9. Assemble exam, solutions and export files. 10. Obtain teacher approval.

### Why it matters

A failure can be attributed to a stage rather than hidden inside one long AI answer. Question-count errors are checked deterministically; factual errors require source review; mathematical errors require independent solving.

### Interface contracts

Each stage should receive structured inputs and return structured outputs, including provenance, status and error messages. Explicit contracts allow each stage to reject invalid input before continuing.

### Trade-off

More stages add latency and cost. Decomposition is valuable only when the checks reduce expensive downstream revision.

<!-- PAGE BREAK -->

---

## 09 | Computational Thinking II: Pattern Recognition

*Look for repeated behavior, not merely repeated technologies.*

### Pattern A — exam committee

Across exam types, people draft, appraise, independently solve and approve. This supports separating Writer, Appraiser, Solver and Teacher roles rather than asking one agent to certify its own output.

### Pattern B — shared workflow, different subjects

Mathematics, language and competency exams assess different skills, yet the lifecycle of planning, drafting, checking and packaging remains comparable. Subject profiles can supply specialized rules and tools.

### Pattern C — student shortcut behavior

Students may reveal answers before fully attempting a problem. A proposed practice mode could provide staged hints, while mock-exam mode withholds answers until submission. This was an extension, not the core exam-authoring requirement.

### Pattern D — scoring variation

Point rules differ by item type and subject. A configurable scoring rule is more robust than hard-coding marks into every question or paper.

<!-- PAGE BREAK -->

---

## 10 | Computational Thinking III: Abstraction

*Preserve the essential structure while isolating subject-specific variation.*

### Core representations

ExamRequest: audience, subject, objectives, time limit and constraints. Blueprint: sections, item types, topics, difficulty bands and scoring. Question: stem, choices, key, rationale, evidence and validation status. ExamPackage: final paper, answer key, solutions, references and review flags.

### Subject profile

A subject profile may define allowed item forms, evidence expectations, permitted tools, formatting conventions, distractor rules and scoring logic. The shared orchestration remains unchanged.

### Separation of concerns

The blueprint specifies what must be produced; generation drafts content; validation checks whether it meets the specification; rendering decides how to display it. This prevents a formatting decision from altering educational meaning.

### Abstraction risk

Over-generalization can erase important differences. A mathematics item needs computational verification, whereas a literature passage may require exact quotation and source authentication.

<!-- PAGE BREAK -->

---

## 11 | Computational Thinking IV: Algorithm Design

*Turn the workflow into a controlled and testable procedure.*

### Proposed algorithm

Read request → identify missing constraints → normalize into blueprint → verify blueprint consistency → retrieve relevant content → generate candidate questions → apply deterministic structural checks → run subject-specific appraisal → solve independently → compare results → revise flagged questions → recompute blueprint totals → render outputs → request teacher approval.

### Revision control

Each failed item should carry an error type and revision history. The workflow should have bounded retry counts, escalation rules and a fallback to teacher review instead of looping indefinitely.

### Deterministic checks

Item count, section totals, allowed option labels, score totals, time budget and output schema can be checked in code. Open-ended truth and pedagogical quality require additional evidence or judgment.

### Human checkpoint

Approval is not a decorative final screen. It is the explicit boundary between automated assistance and assessment responsibility.

<!-- PAGE BREAK -->

---

## 12 | Multi-Agent Architecture

### Blueprint and intake

The October proposal called this responsibility the Planner. The web adapter evaluates the template request and resolves both the THPT and RAG matrices. General CLI requests take a caller-supplied blueprint, with an optional MAS intake step that checks resolved intent and source passages. The blueprint gives generation and validation a common specification.

### Composer and Illustrator

The Composer implements the proposed Writer role. It drafts questions, provisional keys, and explanations under the blueprint constraints. The Illustrator produces the figure code for the LaTeX draft.

### Solver and Reviewer

The Solver answers from the questions and figures with the Composer's keys kept separate. The Reviewer implements the appraisal role by inspecting the draft and solver output for problems. The general pipeline supports one Reviewer feedback round. If it triggers a revision, the pipeline runs the Composer, Illustrator, and Solver again and passes the resulting draft to the teacher.

### Orchestrator and teacher

The orchestrator controls call budgets, validation, and artifact recording. In the web app, question edits and regeneration invalidate the previous approval and PDF preview. A teacher approves the current revision before downloading the paper or teacher answers. [Pipeline design](../architecture/PIPELINE_PLAN_AND_BENCHMARK.md) · [Web approval contract](../integration/CONNECTED_THPT_UI.md#backend-contract)

<!-- PAGE BREAK -->

---

## 13 | Retrieval, Grounding and Subject Adaptation

*Different error classes require different verification methods.*

### Reference retrieval

The workbench supports keyword, embedding, and hybrid retrieval. For THPT math, it retrieves Topic Packs for individual blueprint slots and records source locators, coverage gaps, and warnings. The integrated THPT job binds the retrieved context to question IDs and groups the evidence by section. Callers of the standalone CLI use an explicit evidence handoff. [Retrieval and handoff guide](../rag-workflow.md)

### Natural sciences

Numerical items may be checked by recomputation, symbolic tools, unit checks and independent reasoning. Plausible distractors should be wrong for identifiable reasons rather than accidental arithmetic errors.

### Languages and social sciences

Passages, citations, historical facts and contextual claims require source integrity checks. A fluent paraphrase must not be misrepresented as an exact quotation.

### Visual materials

The Illustrator generates TikZ or PGFPlots source for graphs and diagrams in the LaTeX pipeline. Source checks can catch invalid code. Reviewers still inspect the rendered figure and its relationship to the question.

### Dataset scope

The measured retrieval run uses a versioned corpus snapshot and a held-out query set. Expanding to other subjects calls for approved references and benchmarks that reflect each subject's item types and evidence requirements.

<!-- PAGE BREAK -->

---

## 14 | Blueprint, Difficulty and Scoring

*Structural correctness is a separate, measurable property.*

### Blueprint constraints

Specify number of sections, topics, learning outcomes, item formats, difficulty targets, total score and examination duration. Validate sums and coverage before writing questions.

### Difficulty balancing

A requested easy/medium/hard distribution should be translated into integer item allocations. Estimated difficulty must later be checked against expert review or learner-response data; an LLM label alone is not empirical calibration.

### Dynamic scoring

The team considered multiple-choice, true/false with partial credit, and short-answer components. A scoring function should take a versioned exam rule profile, rather than assuming one fixed national-exam scheme applies universally.

### Feasibility

A paper can be formally correct yet impossible to finish in the allocated time. Duration, reading load and computational effort belong in the appraisal criteria.

<!-- PAGE BREAK -->

---

## 15 | Input, Output and User Experience

*Define the artifact before designing the interface.*

### Inputs

The generation entry points take an exam blueprint in JSON. The general intake can also accept an original request, resolved intent, and source passages. The pipeline CLI supports optional LaTeX templates, question banks, and reference material.

### Outputs

The general pipeline produces a LaTeX draft and item-level review notes. The template workflows also write separate answers and worked solutions. The reviewed draft exporter supports PDF and DOCX for compatible draft content. [Review and export guide](../MAS_INTAKE_AND_EXPORT.md)

### Interaction model

The integrated THPT workspace provides template selection, job progress, question editing, answer inspection, PDF preview, and revision approval. The next UI work simplifies that path and makes failures and recovery clearer. [MVP roadmap](#mvp-roadmap)

### A central distinction

Accuracy, usability and low cost are evaluation criteria; they are not output file types. The group’s slide revisions explicitly sought to clarify this distinction.

### Possible student modes

Mock examination and practice-with-hints modes were proposed as downstream uses of the generated questions, not prerequisites for the teacher-facing MVP.

<!-- PAGE BREAK -->

---

## 16 | Alternatives Considered and Trade-offs

*Decisions are more informative when the rejected routes remain visible.*

### Single chatbot prompt

A single prompt has low setup cost and serves as the baseline. The comparison will measure how often it misses constraints and how much teacher revision it requires.

### One separate system per subject

Advantage: maximum customization. Weakness: duplicated planning and review logic. The preferred proposal is a common workflow with subject profiles and specialized tools.

### All-in-one teacher assistant

Advantage: broad value proposition. Weakness: unclear scope and evaluation. Lesson planning, grading and analytics were deferred in favor of exam production.

### Fully autonomous publishing

Advantage: fewer user steps. Weakness: unacceptable risk when a plausible but incorrect question passes automated checks. Teacher sign-off remains required.

### Unrestricted agent debate

Advantage: potential error discovery. Weakness: latency, cost and correlated model failures. Bounded independent checks and deterministic rules are more defensible.

<!-- PAGE BREAK -->

---

## 17 | Evaluation Design and Benchmark Plan

### Measured prototype checks

At integration commit `8f12fbb`, the Python test suite passed 375 tests and seven subtests. The frontend passed 12 tests and its lint and production build commands. These checks cover job handling, preview and approval rules, and build compatibility.

The benchmark results below were reproduced on integration branch commit `8f12fbb`. The generation pilot replayed 10 synthetic requests twice for each of two systems. Both systems completed all 20 scheduled attempts. The run produced `attempts.jsonl`, `attempts.csv`, and `metrics.json`. Human audit coverage was zero, so correctness and the other human-scored yields were unreported.

The THPT math handoff passed all eight acceptance cases and resolved all 22 slots in the sample matrix. The held-out retrieval benchmark used corpus snapshot `8b8fb7b09182b3d9d1eee0b95818027f52ab004d` and 18 queries, including two expected coverage gaps. The ranking metrics below use the 16 queries with relevant material. All three methods handled both expected gaps correctly.

| Retrieval mode | Hit@5 | Recall@5 | Mean reciprocal rank |
| --- | ---: | ---: | ---: |
| Hybrid | 100% | 93.75% | 1.000 |
| BM25 | 93.75% | 86.98% | 0.938 |
| Embedding | 100% | 91.67% | 0.896 |

On this split, hybrid retrieval had the highest recall at five. These metrics describe how the workbench ranks references. The generation replay tests how the pipeline stages work together. [Retrieval evaluation](../../eval/README.md) · [Generation benchmark](../architecture/PIPELINE_PLAN_AND_BENCHMARK.md#benchmark)

From the repository root, use the environment installed in the README quickstart. The last two commands require the team corpus snapshot. Choose a fresh output directory for the generation pilot.

```powershell
$astraPython = '.\.venv-win\Scripts\python.exe'
& $astraPython -m exam_baseline.benchmarks.pipeline --manifest examples/pipeline/pilot.json --output runs/benchmark/pilot --mode replay
& $astraPython -m rag_workflow.eval --existing --mode all --split heldout --out runs/benchmark/rag-heldout.json | Out-Null
& $astraPython -m rag_workflow.eval --acceptance --out runs/benchmark/thpt-acceptance.json | Out-Null
```

### Planned live comparison

The study asks whether ASTRA improves exam quality or reduces teacher revision time at an acceptable cost. Compare live ASTRA against a direct single-agent prompt on matched blueprints and reference material. Use teacher-authored papers as an additional reference where available. Pair the model and settings where feasible, and record differences so the results can be interpreted.

Version the cases before running the comparison. Include supported subjects and question types, with a separate track for figure-dependent tasks when the baseline lacks figure support. For cases both variants can run, compare fixed reference material with retrieved context and inspect drafts before and after independent checks. These comparisons help attribute gains to retrieval or review.

Have reviewers score the outputs without seeing which system generated them. Use the same rubric for answer correctness, format, scope, source validity, and ambiguity. Record teacher revision time, export success, latency, model usage, and cost per approved paper. Keep failed attempts in the attempt totals, report the denominator and human audit coverage for each quality metric, and publish paired differences with uncertainty and examples of failures.

### Targets from the October plan

The early notes proposed at least 95% answer accuracy, 100% format compliance, at least 95% scope validity, and a unit cost around VND 2,000 per exam. The live study will report observed results against those targets when sufficient labels and cost data are available.

<!-- PAGE BREAK -->

---

## 18 | Risks, Limitations and Responsible Use

*Known unknowns should guide the next iteration.*

### Correlated failures

Multiple agents may share model biases or repeat the same mistaken assumption. Blind solving and external evidence reduce but do not eliminate this risk.

### Pedagogical judgment

Difficulty, fairness, creativity and distractor quality cannot be reduced to simple text checks. Teacher expertise and eventual learner-response evidence remain necessary.

### Copyright and privacy

Uploaded exams and student information require access controls, appropriate permissions and careful retention policies. Source retrieval must not imply permission to reproduce protected passages.

### Measurement gaps

The current evidence covers fixture replay and a finite retrieval corpus. A live, independently labeled exam benchmark, teacher revision timings, and complete model usage records are needed to estimate educational quality and cost.

### Provider and connectivity failures

The THPT math and V-ACT CLIs can resume a saved run from valid checkpoints. The web app persists completed jobs and records interrupted jobs as failures after a backend restart. The mock UI and local replay provide demonstration options during an outage. The next reliability work extends bounded retry behavior across workflows, adds a configured fallback provider, and preserves progress when every model is unavailable. [MVP roadmap](#mvp-roadmap)

<!-- PAGE BREAK -->

---

## 19 | Team Contributions and Working Method

*A collective reasoning process with documented responsibilities.*

### Research allocation

19 October: Huy, Khang, Long and Tuấn Anh investigated context, boundary and priorities; Quỳnh Anh, Trọng and Phát investigated inputs, outputs and benchmarks.

### Presentation and review

Subsequent notes assign slide work to Phát and Đăng Khang, core content to Tuấn Anh, critical review to Minh Huy, and presenting/reviewing to Quỳnh Anh, Trọng and Long. Quỳnh Anh temporarily coordinated the two-week phase.

### Evidence compilation

Long was assigned to synthesize the history of work; Trọng, Khang and Huy were to revise slides following feedback; Phát and Tuấn Anh were to contribute further ideas; Quỳnh Anh supported report drafting and review.

### Collaboration model

The notes describe repeated meetings, cross-review and debate. These assignments show planned and discussed responsibilities, not independently audited hours or an exclusive ownership map of every idea.

### What changed through collaboration

Critical feedback exposed weaknesses in the initial framing, shifted the story from technical components to CT claims, and motivated a clearer separation of final scope from deferred possibilities.

<!-- PAGE BREAK -->

---

## 20 | Conclusion, MVP Roadmap and Evidence Register

### Conclusion

The prototype shows how exam production can be decomposed into explicit generation, checking, and review stages. It gives the team concrete artifacts to test and teachers a draft to inspect. The proposed comparison will assess whether these stages improve exam quality or reduce teacher revision effort at an acceptable cost.

### MVP roadmap

The team proposed six workstreams for the next phase. The evidence column describes what to collect as each capability is built.

| Workstream | Planned capability | Evidence to collect |
| --- | --- | --- |
| All target subjects | Generate a paper and separate answer key or marking guide for every subject in the agreed scope. Define a profile for each subject's item types, scoring, and sources. | Show one reviewed end-to-end example per subject with its blueprint, paper, and answer material. |
| Custom exam formats | Let teachers configure sections, question counts, scoring, and layout through reusable format presets. Validate the settings and check that the rendered paper follows them. | Render the same fixture with the default format and a custom format, then compare both outputs with their requested rules. |
| Model and network outages | Use a consistent retry budget for transient failures and try a configured alternate provider if available. When all providers fail, preserve available checkpoints and identify the blocked stage so the user can resume where supported. | Simulate a primary provider failure and a complete outage. Check recovery behavior and confirm that an interrupted run cannot appear approved or complete. |
| Simpler teacher interface | Remove placeholder copy and redundant controls. Give teachers a clear path from blueprint to review and export, with visible progress, actionable errors, and recovery options. | Observe a teacher walkthrough on desktop and mobile. Record where they hesitate, miss a review step, or cannot recover. |
| Paper-style evaluation | Compare live ASTRA output with matched baselines and study the contribution of retrieval and independent checking. Report quality, teacher effort, latency, and cost together. | Preserve versioned cases, run settings, independent labels, failure examples, and a reproducible results table. [Benchmark plan](#planned-live-comparison) |
| Complete demo video | Record every implemented user-facing feature, including the RAG handoff, generation, review and export, and the path used during an outage. Keep a local copy and prepared artifacts for the presentation. | Check the video against the feature inventory, label live and replay segments, and confirm the local copy plays with the network disconnected. |

### Evidence register

- [S1] `NOTE.txt` and `NOTE.pdf` record the team notes from 18–21 October.
- [S2] `Note buổi họp hihi.pdf` and `21_10 - Idea cua Tanh_Phat.docx` record problem, scope, and pattern proposals.
- [S3] `Bản sao của ASTRA_ Computational Thinking for AI-Powered Exam Generation.pdf` records presentation and framing revisions.
- [S4] `ASTRA_Evidence_History_18-21_Oct_2026.pdf` records chronology, traceability, and limitations.
- [S5] `Meeting 14-10.pdf` records broader platform and strategy discussions.

The prototype update draws on the repository documentation and the reproducible runs in Section 17. The roadmap records the team's priorities for the next phase. [README](../../README.md) · [Connected THPT UI](../integration/CONNECTED_THPT_UI.md) · [RAG evaluation](../../eval/README.md) · [Measured prototype checks](#measured-prototype-checks)

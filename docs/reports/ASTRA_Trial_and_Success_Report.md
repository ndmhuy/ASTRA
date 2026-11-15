# ASTRA: A Multi-Agent System for Exam Generation and Verification
**Team:** Trial and Success  
**Course:** CSC10014 - Computational Thinking | HCMUS / APCS  
**Report date:** 21 October 2026

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

This report reconstructs the project’s conceptual development, decision-making, computational-thinking analysis, proposed architecture, evaluation design, and documented contributions. It deliberately includes exploratory ideas and proposals that did not survive the narrowing of scope.

### Evidence standard

A recorded discussion is evidence of reasoning, not proof of a working feature. Numerical thresholds in the notes are treated as goals unless experimental records establish actual results. Source references at the end identify the materials used.

<!-- PAGE BREAK -->

---

## 01 | Executive Summary

*The central problem is not how to make AI produce text; it is how to make an examination trustworthy and usable.*

### Problem

Traditional exam preparation requires collecting material, selecting learning objectives, drafting questions, reviewing answers, balancing difficulty and formatting printable documents. Generic AI accelerates drafting but can create incorrect answers, unsupported information and inconsistent blueprints.

### Proposed response

ASTRA is a controlled workflow: capture teacher intent, convert it into a blueprint, draft subject-aware questions, appraise their quality, independently solve them, revise failures and package teacher-reviewable outputs.

### CT contribution

Decomposition defines separable tasks; pattern recognition finds reusable processes across subjects; abstraction creates common representations and subject profiles; algorithm design makes validation and revision explicit.

### Status

The source set establishes sustained planning and evolving presentations, but does not independently establish deployment or achievement of target accuracy and cost.

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

### Why one prompt is insufficient

The teacher’s request may omit item counts, cognitive levels, topics, scoring rules, duration and evidence requirements. A single unconstrained generation step has no reliable mechanism to enforce all these simultaneously.

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

Each stage should receive structured inputs and return structured outputs, including provenance, status and error messages. The design prevents downstream formatting from silently accepting invalid content.

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

## 12 | Proposed Multi-Agent Architecture

*Specialization is justified by independent checks, not by the number of agents.*

### Planner / Blueprint Builder

Translates teacher instructions and documents into an explicit specification. Flags missing or contradictory requirements before generation.

### Writer

Drafts candidate items and rationales constrained by the blueprint and retrieved context. Its own answer key is provisional.

### Appraiser

Checks relevance, clarity, difficulty, ambiguity, distractor quality and consistency with the syllabus. Reports item-level findings.

### Blind Solver

Attempts to answer without access to the Writer’s key. A disagreement triggers rechecking rather than automatic acceptance of either answer.

### Orchestrator and teacher

The orchestrator manages states, tool calls, budgets and revision limits. The teacher reviews the final package and retains authority over approval and publication.

<!-- PAGE BREAK -->

---

## 13 | Retrieval, Grounding and Subject Adaptation

*Different error classes require different verification methods.*

### Reference retrieval

Syllabi, teacher-uploaded sources, sample papers and authorized external materials can anchor generation. Each item should retain a source reference when factual grounding is necessary.

### Natural sciences

Numerical items may be checked by recomputation, symbolic tools, unit checks and independent reasoning. Plausible distractors should be wrong for identifiable reasons rather than accidental arithmetic errors.

### Languages and social sciences

Passages, citations, historical facts and contextual claims require source integrity checks. A fluent paraphrase must not be misrepresented as an exact quotation.

### Visual materials

Graphs, geometry figures and diagrams require a standardized production and validation process. The 21 October notes identify figure generation as an unresolved design area.

### Open decision

Dataset selection and provenance were explicitly flagged for further clarification. No final validated dataset specification is established by the available notes.

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

Natural-language teacher request; sample examination; question bank; syllabus; assessment matrix; constraints; reference files and, where applicable, multimodal material.

### Outputs

Editable examination paper, printable PDF/DOCX, answer key, explanations or marking guide, item-level review flags, references and a blueprint summary.

### Interaction model

A low-friction web interface should let users state the educational objective, upload materials, inspect constraints, review flagged questions and approve export. Ease of use does not justify concealing uncertainty.

### A central distinction

Accuracy, usability and low cost are evaluation criteria; they are not output file types. The group’s slide revisions explicitly sought to clarify this distinction.

### Possible student modes

Mock examination and practice-with-hints modes were proposed as downstream uses of the generated questions, not prerequisites for the teacher-facing MVP.

<!-- PAGE BREAK -->

---

## 16 | Alternatives Considered and Trade-offs

*Decisions are more informative when the rejected routes remain visible.*

### Single chatbot prompt

Advantage: minimal implementation effort. Weakness: limited constraint enforcement, opaque checking and high revision burden. Retained as a baseline for comparison, not the target architecture.

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

*Proposed experiments to distinguish ambition from measured improvement.*

### Baselines

Compare manual authoring or teacher-edited outputs, a direct general-purpose LLM prompt, and the structured ASTRA workflow on matched tasks and reference materials.

### Metrics

Answer correctness; blueprint/format compliance; syllabus and source validity; difficulty distribution; ambiguity rate; teacher revision minutes; cost per approved paper; and successful export rate.

### Targets in early notes

The team proposed ≥95% answer accuracy, 100% format compliance and ≥95% scope validity. Earlier strategic notes also discuss a unit-cost target around VND 2,000 per exam. These are targets, not verified outcomes.

### Protocol

Pre-register a test set by subject and question type; blind human reviewers to generation method; record raw errors and disagreements; use the same scoring rubric across methods; report denominators and confidence intervals.

### Acceptance criterion

A meaningful result would show fewer serious errors or less teacher correction at a measured, acceptable cost. Faster first drafts alone do not establish success.

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

The supplied materials do not provide a reproducible benchmark dataset, complete run logs, cost ledger or independent teacher acceptance study. Claims of completed validation would therefore be premature.

### Operational priorities

Clarify dataset selection; standardize visual-question handling; establish scoring profiles; log item-level review; document all failure cases and keep a clear approval step.

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

## 20 | Conclusion, Evidence Register and Next Steps

*ASTRA’s central contribution is a disciplined way of thinking about exam reliability.*

### Conclusion

The team progressed from a broad AI education-assistant idea to a bounded, inspectable exam-generation workflow. The strongest CT insight is that exam production contains recurring stages that can be decomposed, abstracted and checked independently, while subject-specific rules remain configurable.

### Immediate next steps

Finalize scope and dataset; implement or instrument each stage; define versioned blueprints and scoring rules; construct subject-diverse benchmark cases; record failures and teacher edits; run baseline comparisons; report actual metrics separately from targets.

### Evidence register

[S1] NOTE.txt and NOTE.pdf — dated team notes, 18–21 October. [S2] Note buổi họp hihi.pdf and 21_10 - Idea cua Tanh_Phat.docx — problem, scope and pattern proposals. [S3] Bản sao của ASTRA_ Computational Thinking for AI-Powered Exam Generation.pdf — presentation and framing iterations. [S4] ASTRA_Evidence_History_18-21_Oct_2026.pdf — chronology, traceability and limitations. [S5] Meeting 14-10.pdf — broad educational platform and strategy discussions.

### Reading note

Sources contain working hypotheses, draft language and sometimes conflicting scope descriptions. This report preserves those distinctions and does not treat proposed functions, budget assumptions or aspirational performance as measured facts.

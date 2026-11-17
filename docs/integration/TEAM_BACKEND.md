# Backend / MAS handoff

Base: inspected `origin/main` `f6b7ea8`. Cached snapshot; refresh before implementation.
Shared decisions: [integration plan](INTEGRATION.md). Tasks below are proposed integration work.

## Our UI architecture: where you connect

`App.tsx` owns navigation/setup; `state/examSessions.ts` owns each workspace's messages,
questions, job ID and generation state. Components call `services/examService.ts` through
`IExamService`; `types/exam.ts` defines current UI data. This is the intended Backend seam.
The store starts a job, subscribes to progress/previews, then fetches its final package.
Results update the originating workspace even after navigation.

Quick setup uses `QuickPresetModal`; detailed setup opens a custom workspace directly.
Current format numbers are hardcoded placeholders (THPT 40/50, DGNL 30/40), not authoritative
exam specifications. Current question renderer assumes four-choice MCQ; uploads pass filenames.

## Our proposal: format JSON + service adapter

Backend owns versioned exam-format JSON files, exposed to UI/Chatbot as one catalog. We expect:

- Format ID/version, display name, supported subject/grade, duration and total score.
- Ordered sections: stable section ID, question type/count, scoring rule and instructions.
- Editable versus locked fields, allowed ranges/distributions and validation constraints.
- Availability/support status so UI never offers an unsupported format as operational.

UI uses the catalog for setup; submits format ID/version plus teacher overrides; Backend resolves
and validates the matrix. Proposed home: `config/exam-formats/*.json`; existing equivalent
configuration may be reused/exposed instead. Backend should correct unsupported assumptions,
propose field/path changes and show one format's resolved request before implementation.

Keep async jobs behind `IExamService`; adapt to the chosen engine rather than replacing UI
components. Agree structured question results as well as LaTeX artifacts. UI will adapt its types;
its existing camelCase shapes and endpoint names are proposals, not mandatory Backend internals.

## Deliver

- [ ] Agree first engine/scope with integration lead; distinguish generic `/v2` from THPT/VACT.
- [ ] Supply authoritative requirements/presets descriptor and draft evaluator producing validated `ExamMatrix` or missing-field/errors output for Chatbot.
- [ ] Wire RAG's `mas_intake_rag` through `intake.py` into the chosen engine; retain provenance/gaps.
- [ ] Agree async API with UI: idempotent start, status/progress, final structured package, errors.
- [ ] Own stable question IDs/revisions; implement edit/regenerate and review-bound export.

## Dependencies and acceptance

Needs RAG fixture/release and UI question model agreement. Give Chatbot evaluator fixtures first;
UI needs API schemas before wiring. Existing synchronous LaTeX response is incompatible with UI jobs.

Done: valid request reaches engine; invalid scope fails; repeated start returns same job;
edits invalidate approval; reviewed student export excludes answers. Publish one passing request/result fixture and reproduction commands.

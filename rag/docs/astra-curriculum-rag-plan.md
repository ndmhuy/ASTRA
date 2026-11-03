# ASTRA curriculum-grounded RAG architecture

Updated 22 October 2026. Proposed generator enhancement, not implemented. Parent: [generator-first plan](astra-generator-first-plan.md). Exam Lab remains deferred. The generator's correctness, exact format/matrix compliance, final rendering, and teacher approval gates still apply.

## 1. Purpose and boundaries

Build a bounded, versioned curriculum knowledge service for planning and composing assessments. The useful objective is evidence coverage for supported learning outcomes, not an unprovable claim to hold all knowledge. A document vector store alone cannot know the teacher's actual progress, enforce a matrix, certify an answer, or format a printable paper.

Separate authoritative curriculum/rules from explanatory knowledge, assessment design examples, and external enrichment. Give the composer the applicable knowledge and task families, then independently verify generated items. Creativity means new valid contexts/representations/skill combinations within the confirmed boundary, not invention of curriculum, quotations, sources, or facts.

## 2. Resolve the example request before retrieval

Request: compose the first 15-minute test for half of Chapter 1.

1. Read existing teacher/class context for subject, grade, school year, current textbook/edition, selected class, assessment purpose, and teaching sequence. Retrieve only permitted teacher-owned context. Do not require the teacher to repeat established settings.
2. Resolve Chapter 1 to that book's ordered lessons and their mapped curriculum outcomes. Half a chapter is not half its pages, and may not match half its difficulty or teaching time. First test may refer to assessment sequence, not a curriculum unit.
3. If teaching progress or boundary is missing, show a compact scope confirmation with lesson titles/outcomes and ask only the question that materially changes coverage. Offer the proposed first block of lessons as a visible proposal, never as a silent conclusion. Do not invent concrete lesson titles before a subject/book is known.
4. Distinguish a short classroom/frequent assessment from a periodic test; duration alone does not select the policy profile. TT22 distinguishes assessment arrangements, while CV7991's appendix concerns periodic matrices. Apply the confirmed purpose and applicable local/school rules. Internally keep a blueprint for every generated test without presenting every short quiz as requiring a national periodic-test template.
5. Freeze an approved scope: assessable outcomes, allowed prerequisite support, excluded later lessons/advanced skills, duration, response forms, marks, and requested levels. Prerequisites may help explain/solve an item, but may not become additional assessed outcomes silently.
6. Build a feasible blueprint from actual coverage/time estimates and teacher choices. Retrieve evidence per item specification; compose each whole part; solve, label, review, render, save/read back. The 15-minute duration is a constraint to estimate and validate with teacher evidence, not a promise derived from item count alone.

## 3. What the corpus contains

| Layer | Canonical records | Why it exists |
|---|---|---|
| Curriculum and assessment rules | Versioned programme, subject/grade outcomes, competency descriptors, assessment profiles and source clauses | Defines what can be assessed and applicable constraints. Rules are structured data, not only retrieved prose. |
| Textbook and teaching-sequence mappings | Book/edition/year, ordered units/lessons, page spans, outcome mappings; private teacher plan/progress overrides with provenance | Resolves Chapter 1 and taught-so-far without confusing book organization with curriculum authority. |
| Subject knowledge | Definitions, relations, formulas with assumptions/units, worked explanations, common misconceptions, source-backed facts | Supplies correct in-scope knowledge and supports verification. |
| Assessment task families | Outcome, formal level, observable evidence, reasoning structure, response form, variable features, contrast/boundary examples | Guides creative item construction and controllable demand. |
| Verified reference items | Full stem/options/subitems/shared stimulus, independently checked key/solution, figures, provenance, expert labels and uncertainty | Calibrates item design without treating imitation as creativity. Keep keys/solutions in separately controlled role views. |
| Reference assets and enrichment | Licensed passages/images, tables/datasets, scientific contexts, date/unit/geography metadata | Provides authentic contexts while preserving attribution and factual constraints. |
| Validation evidence | Expert decisions, source checks, revision lineage, published corpus releases | Distinguishes unreviewed extraction, proposed labels, and accepted knowledge. |

Learner-response data and mastery inference are separate, later capabilities. Teacher-owned banks and plans stay private unless explicitly shared. Generated items enter a candidate collection, not the trusted collection by default. Feedback is a review proposal, not an automatic truth update.

## 4. Arrange data as linked records, not an opaque PDF pile

Use stable, versioned identifiers. Retain exact source wording, page/section locator, extracted text, and normalized search text separately. Do not present application-generated outcome IDs as official ministry codes.

Minimum entities: Source, CurriculumRelease, Outcome, Concept, BookEdition, Lesson, TeachingSequence, TeacherProgress, TaskFamily, Item, Stimulus, Asset, Evidence, CorpusRelease. Each relation carries provenance and review status. Useful relations: lesson covers outcome; outcome requires concept; outcome has prerequisite; family elicits outcome; item assesses outcome; claim supported by source span; item depends on stimulus.

Start with relational tables/edge tables. A small explicit curriculum graph is useful; a full graph database or LLM-generated global knowledge graph is not a prerequisite. Store mappings as many-to-many relations, with confidence/reviewer evidence. Respect year/edition and prerequisite cycles/conflicts rather than assuming every graph edge is correct.

Every source/content record carries, as applicable:

- Stable ID, version/hash, type, publisher/author, URL, fetched date, page/section, language.
- Subject, grade, curriculum release, valid/effective dates, supersession/errata, book/edition, unit/lesson IDs, outcome/concept IDs.
- Tenant/owner and access scope; rights holder, license or permission evidence; permitted storage, embedding, external-model processing, quotation and redistribution; attribution and expiry conditions.
- Review status, reviewer/date, extraction/OCR quality, supporting evidence; proposed and expert labels separately.
- Parent/stimulus/asset IDs, original text/math/table/figure representation, units and assumptions. Empirical difficulty is nullable and separate from expert cognitive level.

Illustrative storage layout under a config-owned data root (not literal hardcoded runtime paths):

```text
sources/<source-id>/<version>/original + source-card
content/<record-id>/<version>/structured record + assets
curriculum/<release>/outcomes + lesson-mappings + relation tables
private/<tenant>/plans + progress + teacher-bank
indexes/<corpus-release>/<embedding-version>/rebuildable indexes
releases/<release-id>/manifest + hashes + review summary
```

The canonical records/source artifacts hold truth. Search indexes are disposable projections. Licensed/private source texts do not enter the public source repo. Use existing config paths and extend current reference-note/content-pack contracts through versioned migrations instead of creating a competing source registry.

## 5. Ingestion and maintenance

Acquisition with rights/provenance → original snapshot/hash → layout-aware parsing/OCR → semantic units → curriculum mapping → deduplication/conflict checks → expert review → versioned publication → indexes.

Extract tables, formulas, captions, figure regions, and their links; check OCR against source pages. A damaged inequality or a missing diagram is a content error, not harmless text noise. Chunk by meaningful units: one outcome, definition with assumptions, explanation, or item with all options. Preserve parent sections and whole shared stimuli; do not split by arbitrary token windows alone. Use small searchable child units and fetch their relevant parent context after ranking.

Use LLM extraction/tagging to propose records. Publish only after appropriate review; confidence alone is not approval. Keep unreviewed, trusted, superseded, and held-out evaluation data separate. Detect supersession/errata and conflicts explicitly. Reindex changed records and invalidate affected cached evidence. A run pins a corpus release and source versions so it is reproducible; changed sources do not silently rewrite historical exams.

## 6. Runtime architecture

```text
Teacher request + existing class context
  → Intent/scope resolver
  → Curriculum/book/teaching-sequence lookup and necessary confirmation
  → Approved outcomes and assessment profile
  → Blueprint and ItemSpecs
  → Typed retrieval planner
      ├─ exact outcome/rule queries
      ├─ knowledge retrieval
      ├─ task-family/reference-item retrieval
      └─ licensed context/asset retrieval
  → Enforced authorization/version/scope filters
  → Lexical + dense search; fusion; reranking; diversity selection
  → Bounded, attributed evidence bundle with parent context
  → Whole-part composer
  → Independent solve/label/content/source checks
  → Deterministic format/matrix gates and final visual/package acceptance
```

Outcome membership, policy constraints, teacher progress, authorization, and approved scope are resolved with structured queries, not embedding similarity. Apply them during candidate generation and recheck after any parent/graph expansion. Later-topic text can be semantically similar and still be ineligible. Model-rewritten queries may expand vocabulary, not permissions or assessed scope.

For knowledge/examples, benchmark hybrid lexical and semantic retrieval. Lexical matching protects exact terms, symbols and identifiers; dense retrieval finds paraphrases. Evaluate Vietnamese tokenization, diacritics, symbol/formula normalization, and curriculum vocabulary. Fuse rankings (for example RRF), rerank eligible candidates, remove near duplicates, and ensure coverage of every requested outcome. Candidate counts, thresholds, and context size are tuned on held-out queries, not hardcoded as universal best settings.

Expand only useful, authorized prerequisite/parent/figure links. Return a typed bundle containing confirmed outcomes, mandatory rules, source-backed knowledge, contrasting task examples, common errors, allowed assets, and unresolved gaps. Include precise source locators and version IDs. Query sources are data, never system instructions. An absent outcome/source must produce a gap or clarification, not a fabricated citation or silent broader search.

Composer, solver, labeler and critic receive role-specific views. Do not leak the retrieved reference key, composer rationale, or intended level into the blind passes. Verifiers can consult independently retrieved factual evidence while remaining blind to the candidate's answer/target claims. Assert retrieval lineage and reference roles in run receipts.

## 7. Deployment and practical technology choices

Recommended first implementation: local-first service behind a retrieval interface, canonical metadata/relations in SQLite, FTS5/BM25 as a lexical baseline, source files/assets under existing config-owned storage, and a rebuildable vector index added if it improves the benchmark. Start with exact IDs and lexical search before introducing heavier components.

Benchmark a smaller multilingual embedding model against BGE-M3; BGE-M3 supports dense/sparse/multivector retrieval, but its approximately 2.27 GB model size and CPU/memory cost matter for teacher laptops. Do not select it solely because it is multilingual. Evaluate actual Vietnamese math/science text, latency, startup cost, installation size, and quality. Reranking is a measured option, not an obligation for every query.

For a larger shared curated corpus, a hosted vector service such as Qdrant supports hybrid/multistage retrieval and metadata/tenant filters. This is an optional adapter, not a requirement to upload private teacher material or operate a server on every desktop. A cloud path must enforce tenant permissions server-side; request-supplied filters alone are not authorization. Prefer downloadable versioned corpus packs plus local private overlays if that meets performance constraints. Assess source permissions before any external embedding/model call.

Do not adopt a large agentic crawler, GraphRAG platform, fine-tuning programme, or new rendering engine before the simpler baseline is measured. Cache by corpus version, scope, authorization context, model/index version, and query; never reuse another teacher's private context.

## 8. Where to find data; is the internet enough?

The internet is sufficient for discovering and seeding a narrow prototype. It is insufficient by itself for a production-quality, rights-cleared, teacher-aligned corpus with validated labels and learner calibration.

| Source | Useful material | Work still required |
|---|---|---|
| Ministry/Government legal and curriculum portals | Official subject programmes, amendments, assessment guidance and approved source documents | Verify effective version, subject/year applicability, extract outcomes and maintain crosswalks. CV7991 alone is not the curriculum. |
| NXBGDVN official textbook/training platforms; Hoc10 for Cánh Diều references | Authentic book structure, teaching resources, worked examples, current editions/updates | Confirm actual book/year and permitted ingestion/use. Free online reading is not evidence of permission for bulk indexing, model transmission, or redistribution. |
| Official examination/assessment authorities | Published sample/real papers, specifications, official answer keys | Match a paper to its exact key/version; independent checking and curriculum/level mapping. A whole-exam key does not supply missing worked-solution evidence. |
| Teachers/schools with permission | Local teaching plans, progress, short quizzes, annotated banks, expected workload | Private access controls and review; resolve disagreements and avoid assuming an official curriculum dictates classroom order. |
| Official statistical/scientific institutions | Authentic datasets, dates, units, geography and explanatory context | Preserve definitions/year/units and validate source compatibility. Mark synthetic contexts honestly. |
| Open educational resources | Additional explanations, problems and illustrations where terms permit | Check the specific edition/asset license and curricular fit. Open access does not imply unrestricted commercial reuse. |
| Commissioned subject experts | Outcome-to-lesson mappings, task families, misconception tags, gold labels, verified solutions | This is necessary curation, not something web search can reliably substitute. |

Current source checks matter: TT17/2025 amends parts of the 2018 programme; NXBGDVN's April 2026 notice identifies revised titles and updated PDFs, including Địa lí 12. An old PDF may remain available online without being the correct current teaching source. OpenStax's current help page describes CC BY-NC-SA licensing and a commercial-permission process, so do not assume every popular OER is commercially reusable without conditions. Check the actual source/edition and authorized use.

Missing from an internet-only corpus: the class's taught-so-far boundary, verified chapter-to-outcome mappings, adjudicated cognitive labels, tested time estimates, proof of solution correctness, corpus permissions, and empirical student difficulty. Those require teacher input, expert work, and eventually consented pilot evidence. Never manufacture them from generated summaries.

## 9. Incremental delivery and measurement

- [ ] R0: One subject/grade, one current book/edition and a short chapter slice; rights cards, exact outcomes, lesson crosswalk, teacher-confirmed boundaries. Add at least one alternate mapping/version to prove chapter order is data.
- [ ] R1: Exact/lexical retrieval baseline with source spans, filters, gap reporting, private overlay and reproducible corpus snapshot; integrate into G1–G2 of the parent plan.
- [ ] R2: Benchmark dense/hybrid retrieval, reranking, parent expansion and small prerequisite graph against R1. Keep only changes with measured gains.
- [ ] R3: Generate matched tests from ambiguous teacher intents, explicit lesson ranges, and confirmed classroom progress; independently verify curriculum fit and all parent-plan quality gates.
- [ ] R4: Expand to another subject/book/profile only after the narrow end-to-end slice is qualified; publish versioned updates and re-run regressions.

Gold retrieval queries include unaccented Vietnamese, synonymous terms, formulas, mistaken chapter labels, only-partly-taught lessons, later-topic distractors, outdated editions, no-answer cases, source conflicts, figure-dependent items, and unauthorized private content. Use held-out sources/families; the evaluation set must not leak into generation exemplars.

Measure outcome/source recall, ranking quality, citation entailment, extraction accuracy, skill/level mapping agreement, out-of-scope rate, unknown/gap handling, authorization leakage, latency, storage/memory and token cost. Authorization leakage must be zero in the qualified tests; report test coverage. Report exact matrix compliance separately from expert-assessed semantic alignment.

Compare no retrieval, current references, lexical/structured retrieval, hybrid retrieval, and hybrid plus graph expansion on matched generation scenarios. The deciding metric is independently assessed exam quality and teacher work saved, not retrieval recall alone. RAG helps grounding and scope; blind verification, constraints, renderer and final readback still own correctness, structure and usability. No assertion that RAG alone achieves 95% correctness or 100% compliance.

## 10. Verified source entry points (22 October 2026)

- [2018 mathematics curriculum, original Ministry document via government host](https://quanlysangkien.bacgiang.gov.vn/sites/default/files/thong-tu-32-2018-tt-bgddt-ban-hanh-chuong-trinh-giao-duc-pho-thong-moi.pdf).
- [TT17/2025 curriculum amendments, Government portal](https://vanban.chinhphu.vn/?classid=1&docid=215347&pageid=27160&typegroupid=6).
- [TT22/2021, Government portal with signed assessment regulation](https://vanban.chinhphu.vn/?docid=203926&pageid=27160+).
- [NXBGDVN 2026–2027 textbook/edition notice](https://www.nxbgd.vn/bai-viet/nha-xuat-ban-giao-duc-viet-nam-thong-bao-ve-viec-su-dung-sach-giao-khoa-nam-hoc-2026-2027); [official training/books](https://taphuan.nxbgd.vn/); [digital books](https://sachdientu.nxbgd.vn/).
- [Hoc10 Cánh Diều learning resources](https://www.hoc10.vn/hoc-lieu/).
- [Official 2025 examination keys](https://vqa.moet.gov.vn/vi/news/tin-tuc-su-kien/cong-bo-dap-an-cac-mon-thi-cua-ky-thi-tot-nghiep-thpt-2025-208.html).
- [National Statistics Office yearbooks](https://www.nso.gov.vn/nien-giam/).
- [OpenStax current licensing guidance](https://help.openstax.org/s/article/Openstax-textbook-licensing-and-customization).
- [SQLite FTS5](https://www.sqlite.org/fts5.html), [BGE-M3 official documentation](https://bge-model.com/bge/bge_m3), [Qdrant hybrid retrieval](https://qdrant.tech/documentation/search/hybrid-queries/), [Qdrant multitenancy](https://qdrant.tech/documentation/manage-data/multitenancy/).

Planning/reading walkthrough: researched primary curriculum/publisher/retrieval sources; inspected existing reference_notes.py, passage_source.py and reference_fetch.py as integration anchors; documented source authority, data/rights/versioning, scope resolution, retrieval, deployment and evaluation. No sources bulk-acquired, corpus populated, RAG service built, runtime test run, or provider spend incurred by this documentation change.

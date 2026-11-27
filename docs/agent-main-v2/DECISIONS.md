# Agent V2 implementation decisions

For maintainers reviewing the local prototype. These decisions document implementation choices for this branch. The project decision register is reserved for team-approved decisions.

| Decision | Rationale |
| --- | --- |
| One semantic catalog | Python and TypeScript validate against the same versioned intent argument definitions. The React side resolves actual entity IDs, revisions and handler eligibility. |
| Loopback runtime and one transcript store | Main has no verified tenant identity. Browser persistence is scoped to the existing local storage and detected tab updates protect against overwrite. |
| Fresh confirmation after reload | React holds the runnable operation in memory. The stored transcript and intake survive. A new confirmation requires a fresh operation binding. |
| Existing UI performs business mutations | React owns generation, revision, approval and download. The Agent transport can return typed intents only. |
| Separate model settings and BYOK transports | Agent uses native Gemini structured output. MAS uses the existing OpenAI-compatible wire contract through the native OpenAI route when configured for BYOK. |
| Guard ambiguous language | Exact correction grammar permits the final target. General negated, hypothetical and quoted mutations require clarification. |
| Separate exam title | The sidebar title is conversation metadata. Manual names survive a package update. The canonical exam title remains in package metadata. |
| Review safety | A programmatic PDF view does not record a teacher review. Agent-applied question edits require a teacher-provided value and preserve the manual save path. |

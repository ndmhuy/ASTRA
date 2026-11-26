# Continue unified semantic workflow implementation

For the next coding session on feat/longlth2297/agent-main-v2 in the existing worktree. Read UNIFIED_SEMANTIC_WORKFLOW_SPEC.md and the latest PROGRESS.md entries first.

1. Finish Worker quota/circuit/replay regression evidence; the all-34-action fixture needs its explicit larger token budget.
2. Add structured dialogue context while preserving the legacy Worker hash.
3. Prepare a disabled Worker MAS provider behind the existing CompletionRequest interface. Preserve academic models and schemas. Do not expose an anonymous generic completion endpoint.
4. Build independent semantic/workflow/adversarial dataset partitions and an offline harness that clearly distinguishes oracle semantic fixtures from actual NLU predictions.
5. Verify safe keyless startup from an isolated checkout, update architecture/provider/operator/deployment evidence and release gates, run secret scans and make local milestone commits.

No authorization is needed for those local steps. No deployment, live inference, real generation, budget activation, push or merge is authorized. Current production remains the old disabled version; successful live THPT intake has not been demonstrated.

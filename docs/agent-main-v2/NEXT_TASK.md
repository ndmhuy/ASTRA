# Resume Worker integration

For the next ASTRA coding session on `feat/longlth2297/agent-main-v2` in the existing feature worktree. Fetch origin and inspect HEAD/status first. Implementation milestone commits are d51f89d and d323dae; subsequent validation/handoff changes are recorded in Git.

W0–W5 are implemented and locally exercised. W6 is waiting for owner actions. W7 has zero remote inference evidence. W8 documentation describes these limits.

1. Read PROGRESS.md and WORKER_RUNBOOK.md. Preserve the ignored private diagnostic .env and the existing Worker settings. Use start-astra-worker.bat to override private profile selection without rewriting it.
2. Obtain the exact non-secret Gemini structured-output model ID available to the stored BYOK project. The owner sets ASTRA_AGENT_MODEL centrally. Never request the Run Secret or Google key.
3. Complete Wrangler browser login from workers/astra-ai-proxy, confirm the intended account and existing astra-ai-proxy Worker. Secret list displays names only.
4. Obtain explicit approval for deployment adding ADMISSION and its SQLite migration. Deploy the production entry with forwarding false. Keep the stable global-v1 object identity.
5. Verify health, binding and existing settings. Only after live-test authorization enable the single global diagnostic allowance and perform exactly one natural turn through ASTRA. The target sentence is outside the anchored fast path. Record actual provider and browser evidence, with no retry/fallback/exam generation.
6. If a live failure occurs, diagnose offline and request a fresh authorization before another attempt. After success, arrange multi-turn manual acceptance and approved release budgets.
7. MAS remains demo. Academic inference uses Chat Completions with JSON/schema/tool modes, role retries and several calls per exam. Gemini compatibility and a separate credential/model need verification before exposing a bounded MAS operation.

The local app was restarted on port 8000 with Worker transport and demo MAS. An independent fresh checkout at sibling longlth2297-agent-worker-fresh was installed and tested on port 8011, then stopped. It contains DO_NOT_DELETE.txt and should be preserved. Fresh compiler/corpus installation and remote AI acceptance remain unverified.

The Worker package requires operator-only Wrangler. Ordinary users need Git, Python, Node and local application resources. They receive no shared credentials. Anonymous endpoint access can consume its centralized allowance.

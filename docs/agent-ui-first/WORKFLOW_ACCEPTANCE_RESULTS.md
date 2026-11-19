# Workflow Acceptance Results

| Scenario | Evidence | Result |
|---|---|---|
| A. Multi-step UI navigation | `AgentTaskController` test creates workspace then opens setup; second step is rebased to a newer state version and both receipts succeed | **IMPLEMENTED AND VERIFIED** |
| B. Guided intake | real catalog is exposed in compact context; configure action creates a generation confirmation; start rejects missing/mismatched confirmation | **IMPLEMENTED AND VERIFIED** offline; no live job |
| C. Stale/changed state | executor stale-context test and per-step fresh capture | **IMPLEMENTED AND VERIFIED** |
| D. During-generation notes | store tests cover create/edit/cancel, completion review message and no automatic mutation | **IMPLEMENTED AND VERIFIED** |
| E. Sequential revision | focused test approves one note, calls existing regenerate once, refreshes and observes revision 1 -> 2 | **IMPLEMENTED AND VERIFIED** with fake service |
| F. Unsupported capability | invented Backend action is rejected before handler invocation; offline unsupported responses retained | **IMPLEMENTED AND VERIFIED** |
| G. Provider error | missing key/quota and fake SDK tests are explicit; no deterministic fallback in Gemini mode | **IMPLEMENTED AND VERIFIED** offline |
| H. Duplicate request/receipt | executor receipt cache, store generation guard, note dedupe and controller loop stop | **IMPLEMENTED AND VERIFIED** |

Commands run:

```text
astra-frontend: npm test -> 20 passed
astra-frontend: npm run lint -> passed
astra-frontend: npm run build -> passed
repository: .venv-agent-ui\Scripts\python.exe -m pytest tests\test_agent_ui_service.py -q -> 36 passed
```

No Gemini inference, Backend model call or complete generation job was run. HTTP health is not counted as model evidence.

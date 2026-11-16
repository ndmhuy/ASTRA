# Offline vertical-slice demo

Run from repository root:

```powershell
.\.venv-agent\Scripts\python.exe -m exam_baseline.agent.demo
```

The JSON trace deterministically demonstrates:

1. “Tạo đề Toán lớp 12” retains subject/grade and asks topic/count/duration together.
2. “Chọn gợi ý mẫu, phần đạo hàm” applies only the accepted fixture preset.
3. A typed trusted mock approval matching draft revision/hash starts exactly one mock job.
4. App help and status questions continue during the mock job.
5. “Câu 3 khó quá” creates no edit.
6. “Sửa câu 3 dễ hơn” maps display index 3 to fixture stable ID `question-stable-42`.
7. “Đổi còn 15 câu” records a structural pending change without touching the run.
8. “Thôi giữ câu 3” cancels only the pending question edit.
9. A second generation request in the same workspace is blocked.
10. Mock completion plus final package emits one consolidated proposal and `applied=false`.

The harness does not call FastAPI, React, RAG, a model provider, or the real generation
pipeline. IDs and status are fixtures. It demonstrates the protocol and state invariants only.

An independent navigation path is covered in `test_ui02_enabled_navigation_waits_for_receipt`:
the mock registry must explicitly enable `ui.navigate`; stale and disabled contexts fail before
effects, and the agent does not say navigation completed until the executor receipt exists.

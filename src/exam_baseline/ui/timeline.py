"""Teacher-facing chat messages backed by saved exam changes."""


def change_messages(change: dict) -> list[dict]:
    job_id = change["jobId"]
    change_id = change["id"]
    question = f"[Câu {change['questionId']}]"
    request = change["request"]
    messages = [
        {
            "id": f"change:{job_id}:{change_id}:request",
            "role": "user",
            "content": f"{question} {request}",
            "timestamp": change["startedAt"],
            "examVersion": {"jobId": job_id, "revision": change["beforeRevision"]},
            "recorded": True,
        }
    ]
    status = change["status"]
    if status == "pending":
        content = "Đang xử lý yêu cầu."
    elif status == "failed":
        content = change["error"]["message"]
    elif change["kind"] == "regenerated":
        content = f"Đã chỉnh theo yêu cầu: “{request}”."
    elif change["kind"] == "undone":
        content = "Đã hoàn tác thay đổi."
    else:
        content = "Đã lưu chỉnh sửa câu hỏi."
    messages.append(
        {
            "id": f"change:{job_id}:{change_id}:result",
            "role": "assistant",
            "content": f"{question} {content}",
            "timestamp": change.get("finishedAt", change["startedAt"]),
            "examVersion": {
                "jobId": job_id,
                "revision": change.get("afterRevision") or change["beforeRevision"],
            },
            "recorded": True,
            **(
                {"changeId": change_id}
                if status == "completed" and change["kind"] != "undone"
                else {}
            ),
        }
    )
    return messages

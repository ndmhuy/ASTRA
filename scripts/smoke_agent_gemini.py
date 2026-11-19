"""Credential-safe live smoke for an already running Gemini-mode Agent service."""

from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def post(url: str, payload: dict | None, headers: dict[str, str]) -> dict:
    body = json.dumps(payload).encode() if payload is not None else b""
    request = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310 - explicit local URL
            return json.load(response)
    except HTTPError as error:
        detail = json.loads(error.read().decode("utf-8"))
        raise SystemExit(f"Agent smoke failed with HTTP {error.code}: {detail}") from error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8010")
    parser.add_argument("--origin", default="http://127.0.0.1:5173")
    args = parser.parse_args()
    headers = {"Content-Type": "application/json", "Origin": args.origin}
    session = post(f"{args.base_url}/agent/session", None, headers)
    headers["X-ASTRA-Agent-Session"] = session["token"]
    response = post(
        f"{args.base_url}/agent/interpret",
        {
            "turnId": "live-agent-gemini-smoke",
            "message": (
                "Thầy cô đang ở trang bắt đầu; hãy giải thích ngắn gọn "
                "có thể làm gì tiếp theo."
            ),
            "context": {
                "workspaceId": None,
                "screen": "start",
                "activeModal": None,
                "sidebarCollapsed": False,
                "stateVersion": 1,
                "activeJob": None,
                "examRevision": None,
                "sessions": [],
                "notes": [],
                "capabilities": [
                    {
                        "id": "ui.session.create",
                        "description": "Mở workspace soạn đề mới.",
                        "status": "available_real",
                        "callable": True,
                        "requiresConfirmation": False,
                    }
                ],
            },
        },
        headers,
    )
    if response.get("provider") != "gemini":
        raise SystemExit(f"Expected provider=gemini, received {response.get('provider')!r}")
    safe = {
        "turnId": response.get("turnId"),
        "provider": response.get("provider"),
        "decisions": [
            {
                "kind": item.get("kind"),
                "text": item.get("text"),
                "capabilityId": item.get("capabilityId"),
            }
            for item in response.get("decisions", [])
        ],
        "uiActionExecuted": False,
    }
    print(json.dumps(safe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

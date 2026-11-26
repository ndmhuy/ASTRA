"""Public ASTRA interpretation transport. Credentials remain at the Worker."""

import json
import logging
import re
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from pydantic import ValidationError

from .contracts import VERSION, Decision, Turn
from .provider import ProviderFailure
from .semantics import VERSION as SEMANTIC_VERSION
from .semantics import SemanticFrame, normalize_frame

logger = logging.getLogger(__name__)
WORKER_URL = "https://astra-ai-proxy.letranhoanglong2227.workers.dev"
CONTRACT_HASH = json.loads(
    (Path(__file__).parents[1] / "resources/agent/worker-contract.json").read_text(encoding="utf-8")
)["contractHash"]
ERRORS = {
    "disabled",
    "configuration",
    "transient",
    "quota",
    "schema",
    "budget",
    "auth",
    "model",
    "timeout",
    "rejected",
}
SEMANTIC_HASH = json.loads(
    (Path(__file__).parents[1] / "resources/agent/semantic-contract.json").read_text("utf-8")
)["contractHash"]


class WorkerInterpretationProvider:
    def __init__(self, client: httpx.AsyncClient, endpoint: str, *, semantic: bool = False):
        url = urlsplit(endpoint)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in ("", "/")
        ):
            raise ValueError("Worker endpoint must be an HTTPS origin")
        self.client = client
        self.semantic = semantic
        self.url = endpoint.rstrip("/") + (
            "/v2/agent/interpret" if semantic else "/v1/agent/interpret"
        )

    async def interpret(self, turn: Turn, timeout: float) -> Decision | SemanticFrame:
        try:
            body = turn.model_dump(exclude_none=True)
            body["context"] = turn.context.model_dump(exclude_defaults=True, exclude_none=True)
            if not self.semantic:
                body["context"].pop("dialogue", None)
            async with self.client.stream(
                "POST",
                self.url,
                json=body,
                headers={"X-Astra-Contract": SEMANTIC_HASH if self.semantic else CONTRACT_HASH},
                timeout=timeout,
                follow_redirects=False,
            ) as response:
                raw = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(raw) + len(chunk) > 65536:
                        raise ProviderFailure("schema")
                    raw.extend(chunk)
                payload = json.loads(raw)
                logger.info("agent_worker_http status=%d", response.status_code)
                if response.status_code != 200:
                    reason = payload.get("error") if isinstance(payload, dict) else None
                    raise ProviderFailure(reason if reason in ERRORS else "transient")
                if (
                    payload.get("schemaVersion") != (SEMANTIC_VERSION if self.semantic else VERSION)
                    or payload.get("clientMessageId") != turn.clientMessageId
                ):
                    raise ProviderFailure("schema")
                decision = (
                    normalize_frame(payload["frame"])
                    if self.semantic
                    else Decision.model_validate(payload["decision"])
                )
                evidence = payload.get("evidence", {})
                worker_id = evidence.get("requestId", "")
                if not isinstance(worker_id, str) or not re.fullmatch(r"[a-f0-9-]{36}", worker_id):
                    worker_id = "unavailable"
                # Only fixed-category/status diagnostics. No remote prose or prompt logging.
                status = evidence.get("upstreamStatus")
                logger.info(
                    "agent_worker_result turn_id=%s worker_id=%s upstream_status=%s attempts=%s",
                    turn.clientMessageId,
                    worker_id,
                    status if type(status) is int else None,
                    1 if evidence.get("attempts") == 1 else 0,
                )
                return decision
        except httpx.TimeoutException:
            raise ProviderFailure("timeout") from None
        except httpx.TransportError:
            raise ProviderFailure("transient") from None
        except (ValueError, KeyError, TypeError, ValidationError):
            raise ProviderFailure("schema") from None

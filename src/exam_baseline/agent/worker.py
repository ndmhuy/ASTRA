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


def log_evidence(turn: Turn, payload: dict) -> None:
    evidence = payload.get("evidence", {})
    if not isinstance(evidence, dict):
        return
    diagnostics = evidence.get("diagnostics", payload.get("diagnostics", {}))
    if not isinstance(evidence, dict) or not isinstance(diagnostics, dict):
        return
    safe = {"turnId": turn.clientMessageId}
    request_id = evidence.get("requestId", payload.get("requestId"))
    if isinstance(request_id, str) and re.fullmatch(r"[a-f0-9-]{36}", request_id):
        safe["requestId"] = request_id
    for key in ("attempts", "upstreamStatus", "elapsedMs", "providerElapsedMs"):
        value = evidence.get(key)
        if type(value) is int and 0 <= value < 10_000_000:
            safe[key] = value
    for key in (
        "promptTokenCount",
        "candidatesTokenCount",
        "thoughtsTokenCount",
        "totalTokenCount",
        "textBytes",
    ):
        value = diagnostics.get(key)
        if type(value) is int and 0 <= value < 10_000_000:
            safe[key] = value
    for key in ("schemaStage", "finishReason", "dialogueAct"):
        value = diagnostics.get(key)
        if isinstance(value, str) and re.fullmatch(r"[A-Za-z_]{1,60}", value):
            safe[key] = value
    stage = evidence.get("requestStage")
    if isinstance(stage, str) and re.fullmatch(r"[a-z_]{1,40}", stage):
        safe["requestStage"] = stage
    # Field paths have already been restricted by the Worker; never forward arbitrary prose.
    paths = diagnostics.get("validationPaths")
    if isinstance(paths, list):
        safe["validationPaths"] = [
            path
            for path in paths
            if isinstance(path, str) and re.fullmatch(r"/[A-Za-z0-9_/]{0,150}", path)
        ][:8]
    logger.info("agent_worker_evidence %s", json.dumps(safe, separators=(",", ":")))


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
    def __init__(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        *,
        semantic: bool = False,
        semantic_version: str = "astra-semantic-v1",
        caller_token: str | None = None,
    ):
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
        if caller_token is not None and not re.fullmatch(r"[a-f0-9]{64}", caller_token):
            raise ValueError("invalid Worker caller credential")
        self.caller_token = caller_token
        self.semantic = semantic
        self.semantic_version = semantic_version
        self.url = endpoint.rstrip("/") + (
            "/v2/agent/interpret" if semantic else "/v1/agent/interpret"
        )

    async def interpret(self, turn: Turn, timeout: float) -> Decision | SemanticFrame:
        try:
            body = turn.model_dump(exclude_none=True)
            body["context"] = turn.context.model_dump(exclude_defaults=True, exclude_none=True)
            from .v3 import TurnV3
            from .v3 import normalize_frame as normalize_v3

            v3 = (
                isinstance(turn, TurnV3)
                and self.semantic
                and self.semantic_version == "astra-semantic-v3"
            )
            contract_hash = SEMANTIC_HASH if self.semantic else CONTRACT_HASH
            if v3:
                contract_hash = json.loads(
                    (
                        Path(__file__).parents[1] / "resources/agent/semantic-v3-contract.json"
                    ).read_text("utf-8")
                )["contractHash"]
            else:
                body["context"].pop("grounded", None)
            if not self.semantic:
                body["context"].pop("dialogue", None)
            async with self.client.stream(
                "POST",
                self.url.replace("/v2/", "/v3/") if v3 else self.url,
                json=body,
                headers={
                    "X-Astra-Contract": contract_hash,
                    **({"X-Astra-Caller": self.caller_token} if self.caller_token else {}),
                },
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
                if isinstance(payload, dict):
                    log_evidence(turn, payload)
                if response.status_code != 200:
                    reason = payload.get("error") if isinstance(payload, dict) else None
                    evidence = payload.get("evidence", {}) if isinstance(payload, dict) else {}
                    # Repeating the same logical turn after admission can be duplicate
                    # inference. Only explicit pre-admission failures are safe to retry.
                    safe = (
                        reason == "transient"
                        and isinstance(evidence, dict)
                        and evidence.get("admitted") is False
                        and evidence.get("attempts") == 0
                    )
                    raise ProviderFailure(
                        reason if reason in ERRORS else "transient", safe_retry=safe
                    )
                if (
                    payload.get("schemaVersion")
                    != (
                        "astra-semantic-v3"
                        if v3
                        else SEMANTIC_VERSION
                        if self.semantic
                        else VERSION
                    )
                    or payload.get("clientMessageId") != turn.clientMessageId
                ):
                    raise ProviderFailure("schema")
                decision = (
                    (normalize_v3(payload["frame"]) if v3 else normalize_frame(payload["frame"]))
                    if self.semantic
                    else Decision.model_validate(payload["decision"])
                )
                evidence = payload.get("evidence", {})
                if not isinstance(evidence, dict):
                    raise ProviderFailure("schema")
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
        except httpx.ConnectTimeout:
            raise ProviderFailure("timeout", safe_retry=True) from None
        except httpx.ConnectError:
            raise ProviderFailure("transient", safe_retry=True) from None
        except httpx.TimeoutException:
            raise ProviderFailure("timeout") from None
        except httpx.TransportError:
            raise ProviderFailure("transient") from None
        except (ValueError, KeyError, TypeError, ValidationError):
            raise ProviderFailure("schema") from None

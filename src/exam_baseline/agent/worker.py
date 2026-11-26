"""Public ASTRA interpretation transport. Credentials remain at the Worker."""

import json
import logging
from urllib.parse import urlsplit

import httpx
from pydantic import ValidationError

from .contracts import VERSION, Decision, Turn
from .provider import ProviderFailure

logger = logging.getLogger(__name__)
WORKER_URL = "https://astra-ai-proxy.letranhoanglong2227.workers.dev"
ERRORS = {"disabled", "configuration", "transient", "quota", "schema",
          "budget", "auth", "model", "timeout", "rejected"}


class WorkerInterpretationProvider:
    def __init__(self, client: httpx.AsyncClient, endpoint: str):
        url = urlsplit(endpoint)
        if (url.scheme != "https" or not url.hostname or url.username or url.password
                or url.query or url.fragment or url.path not in ("", "/")):
            raise ValueError("Worker endpoint must be an HTTPS origin")
        self.client = client
        self.url = endpoint.rstrip("/") + "/v1/agent/interpret"

    async def interpret(self, turn: Turn, timeout: float) -> Decision:
        try:
            async with self.client.stream(
                "POST", self.url, json=turn.model_dump(exclude_none=True),
                timeout=timeout, follow_redirects=False,
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
                if (payload.get("schemaVersion") != VERSION
                        or payload.get("clientMessageId") != turn.clientMessageId):
                    raise ProviderFailure("schema")
                decision = Decision.model_validate(payload["decision"])
                evidence = payload.get("evidence", {})
                # Only fixed-category/status diagnostics. No remote prose or prompt logging.
                status = evidence.get("upstreamStatus")
                logger.info("agent_worker_result upstream_status=%s attempts=%s",
                            status if type(status) is int else None,
                            1 if evidence.get("attempts") == 1 else 0)
                return decision
        except httpx.TimeoutException:
            raise ProviderFailure("timeout") from None
        except httpx.TransportError:
            raise ProviderFailure("transient") from None
        except (ValueError, KeyError, TypeError, ValidationError):
            raise ProviderFailure("schema") from None

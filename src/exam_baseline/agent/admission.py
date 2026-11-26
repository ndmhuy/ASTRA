"""Bounded local Agent admission with replay and one active turn per workspace."""

import unicodedata
from collections import OrderedDict, deque
from time import monotonic

from fastapi import HTTPException

from .contracts import Decision, Turn


class Admission:
    WINDOW = 60
    REPLAY_TTL = 300
    REPLAY_CAP = 256
    PER_IP_LIMIT = 12
    BURST_WINDOW = 2
    BURST_LIMIT = 4
    GLOBAL_LIMIT = 60
    PER_IP_CONCURRENT = 2
    GLOBAL_CONCURRENT = 8

    def __init__(self):
        self.recent: deque[tuple[float, str]] = deque()
        self.active: dict[str, str] = {}
        self.inflight: set[tuple[str, str]] = set()
        self.cached: OrderedDict[tuple[str, str], tuple[float, str, Decision]] = OrderedDict()

    def enter(self, peer: str, turn: Turn, fingerprint: str) -> Decision | None:
        now = monotonic()
        while self.recent and now - self.recent[0][0] >= self.WINDOW:
            self.recent.popleft()
        while self.cached and now - next(iter(self.cached.values()))[0] >= self.REPLAY_TTL:
            self.cached.popitem(last=False)
        key = (peer, turn.clientMessageId)
        if key in self.cached:
            _, previous, decision = self.cached[key]
            if fingerprint != previous:
                raise HTTPException(409, "agent_message_conflict")
            return decision
        used = [stamp for stamp, ip in self.recent if ip == peer]
        burst = [stamp for stamp in used if now - stamp < self.BURST_WINDOW]
        if len(burst) >= self.BURST_LIMIT:
            raise HTTPException(429, "agent_rate_limited", {"Retry-After": str(self.BURST_WINDOW)})
        if (
            turn.workspaceId in self.active
            or key in self.inflight
            or len(self.active) >= self.GLOBAL_CONCURRENT
            or list(self.active.values()).count(peer) >= self.PER_IP_CONCURRENT
            or len(self.recent) >= self.GLOBAL_LIMIT
            or len(used) >= self.PER_IP_LIMIT
        ):
            retry = max(1, int(self.WINDOW - (now - used[0]))) if used else 1
            raise HTTPException(429, "agent_rate_limited", {"Retry-After": str(retry)})
        self.recent.append((now, peer))
        self.active[turn.workspaceId] = peer
        self.inflight.add(key)
        return None

    def leave(self, peer: str, turn: Turn) -> None:
        self.active.pop(turn.workspaceId, None)
        self.inflight.discard((peer, turn.clientMessageId))

    def finish(self, peer: str, turn: Turn, fingerprint: str, decision: Decision) -> None:
        self.cached[(peer, turn.clientMessageId)] = (monotonic(), fingerprint, decision)
        if len(self.cached) > self.REPLAY_CAP:
            self.cached.popitem(last=False)


def normalize_message(message: str) -> str:
    text = unicodedata.normalize("NFC", message).strip()
    if len(text.encode("utf-8")) > 24 * 1024:
        raise HTTPException(413, "agent_message_limit")
    if (
        not any(char.isalnum() for char in text)
        or any(unicodedata.category(char) == "Cc" and char not in "\n\r\t" for char in text)
        or (len(text) >= 12 and len(set(text)) == 1)
    ):
        raise HTTPException(422, "agent_invalid_message")
    return text

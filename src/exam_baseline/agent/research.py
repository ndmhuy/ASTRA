"""Allowlist-gated internet research for hardcoded adjacent exam topics."""

import html
import re
from typing import Annotated, Literal
from urllib.parse import parse_qs, unquote, urlsplit

import httpx
from pydantic import Field, StringConstraints, model_validator

from .contracts import Contract, Id
from .knowledge import DOMAIN

RESEARCH_VERSION = "astra-web-research-v1"
ADJACENT_TOPICS: dict[str, dict] = DOMAIN.get("adjacentTopics", {})
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_DDG_BLOCK_RE = re.compile(
    r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>'
    r'(?:.*?<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(?P<snippet>.*?)</a>)?',
    re.S | re.I,
)


def _clean_text(value: str, *, max_length: int) -> str:
    stripped = _TAG_RE.sub(" ", html.unescape(value or ""))
    no_ctrl = "".join(ch if ord(ch) >= 32 else " " for ch in stripped)
    compact = _SPACE_RE.sub(" ", no_ctrl).strip()
    return compact[:max_length]


def _clean_https_url(raw_url: str) -> str | None:
    candidate = html.unescape(raw_url or "").strip()
    if candidate.startswith("//"):
        candidate = "https:" + candidate
    parsed = urlsplit(candidate)
    if parsed.path.startswith("/l/") and "uddg" in parse_qs(parsed.query):
        candidate = unquote(parse_qs(parsed.query)["uddg"][0]).strip()
        parsed = urlsplit(candidate)
    if parsed.scheme != "https" or not parsed.hostname or len(candidate) > 500:
        return None
    if parsed.username or parsed.password:
        return None
    return candidate


class ResearchRequest(Contract):
    schemaVersion: Literal["astra-web-research-v1"]
    workspaceId: Id
    clientMessageId: Id
    adjacentTopicId: Annotated[str, StringConstraints(min_length=1, max_length=40)]
    message: Annotated[str, StringConstraints(min_length=1, max_length=2000)]
    count: Annotated[int, Field(ge=4, le=20)] | None = None
    minutes: Annotated[int, Field(ge=5, le=120)] | None = None

    @model_validator(mode="after")
    def validate_topic(self):
        if self.adjacentTopicId not in ADJACENT_TOPICS:
            raise ValueError("unsupported_adjacent_topic")
        return self


class ResearchSource(Contract):
    title: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    url: Annotated[str, StringConstraints(min_length=10, max_length=500)]
    snippet: Annotated[str, StringConstraints(min_length=0, max_length=600)] = ""


class ResearchResponse(Contract):
    schemaVersion: Literal["astra-web-research-v1"] = RESEARCH_VERSION
    clientMessageId: Id
    adjacentTopicId: str
    topicLabel: str
    formatId: str
    subject: str
    summary: str
    suggestedCount: int
    suggestedMinutes: int
    sources: list[ResearchSource] = Field(default_factory=list, max_length=8)
    searchMode: Literal["live_web", "offline_fallback"]


def _build_query(topic: dict, message: str) -> str:
    base = topic["searchQueries"][0]
    words = re.findall(r"[A-Za-z0-9À-ỹ]+", message)
    stop = {"soan", "tao", "de", "cho", "toi", "cau", "phut", "tim", "mang", "minh", "nhe"}
    extra = [
        word
        for word in words
        if word.casefold() not in stop and not word.isdigit() and len(word) > 2
    ][:4]
    return f"{base} {' '.join(extra)}".strip() if extra else base


def _parse_ddg_results(body: str) -> list[ResearchSource]:
    sources: list[ResearchSource] = []
    seen_urls: set[str] = set()
    for match in _DDG_BLOCK_RE.finditer(body):
        url = _clean_https_url(match.group("href"))
        title = _clean_text(match.group("title"), max_length=180)
        snippet = _clean_text(match.group("snippet") or "", max_length=420)
        if not url or not title or url in seen_urls:
            continue
        seen_urls.add(url)
        sources.append(ResearchSource(title=title, url=url, snippet=snippet))
        if len(sources) >= 5:
            break
    return sources


async def _fetch_ddg(client: httpx.AsyncClient, query: str) -> list[ResearchSource]:
    response = await client.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers={"User-Agent": "ASTRA-Exam-Research/1.0 (+https://example.local)"},
    )
    response.raise_for_status()
    return _parse_ddg_results(response.text)


async def _fetch_wikipedia(client: httpx.AsyncClient, query: str) -> list[ResearchSource]:
    response = await client.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 5,
            "format": "json",
            "utf8": 1,
        },
        headers={"User-Agent": "ASTRA-Exam-Research/1.0 (+https://example.local)"},
    )
    response.raise_for_status()
    items = response.json().get("query", {}).get("search", [])
    sources: list[ResearchSource] = []
    for item in items:
        title = _clean_text(item.get("title", ""), max_length=180)
        snippet = _clean_text(item.get("snippet", ""), max_length=420)
        if not title:
            continue
        slug = title.replace(" ", "_")
        sources.append(
            ResearchSource(
                title=f"{title} — Wikipedia",
                url=f"https://en.wikipedia.org/wiki/{slug}",
                snippet=snippet,
            )
        )
    return sources


async def search_adjacent_topic(
    request: ResearchRequest,
    *,
    client: httpx.AsyncClient | None = None,
    allow_network: bool = True,
) -> ResearchResponse:
    """Fetch public overview sources for an allowlisted topic with safe offline fallback."""
    topic = ADJACENT_TOPICS[request.adjacentTopicId]
    suggested_count = request.count or int(topic["defaultCount"])
    suggested_minutes = request.minutes or int(topic["defaultMinutes"])
    sources: list[ResearchSource] = []
    search_mode: Literal["live_web", "offline_fallback"] = "offline_fallback"

    if allow_network:
        query = _build_query(topic, request.message)
        try:
            if client is None:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(6.0, connect=3.0), follow_redirects=True
                ) as owned:
                    sources = await _fetch_ddg(owned, query)
                    if not sources:
                        sources = await _fetch_wikipedia(owned, f"{topic['subject']} exam format")
            else:
                sources = await _fetch_ddg(client, query)
                if not sources:
                    sources = await _fetch_wikipedia(client, f"{topic['subject']} exam format")
        except httpx.HTTPError:
            sources = []
        if sources:
            search_mode = "live_web"

    if sources:
        highlights = "; ".join(
            f"{src.title}: {src.snippet}" if src.snippet else src.title for src in sources[:3]
        )
        summary = (
            f"{topic['sectionGuidance']} "
            f"Đã tổng hợp từ {len(sources)} nguồn công khai trên mạng: {highlights[:650]}"
        )
    else:
        summary = (
            f"{topic['sectionGuidance']} "
            "(Hiện dùng mô tả cấu trúc tích hợp sẵn vì chưa lấy được kết quả web.)"
        )

    return ResearchResponse(
        clientMessageId=request.clientMessageId,
        adjacentTopicId=request.adjacentTopicId,
        topicLabel=topic["label"],
        formatId=topic["formatId"],
        subject=topic["subject"],
        summary=summary,
        suggestedCount=suggested_count,
        suggestedMinutes=suggested_minutes,
        sources=sources,
        searchMode=search_mode,
    )

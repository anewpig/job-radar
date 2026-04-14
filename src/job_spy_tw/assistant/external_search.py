"""Optional external web search support for assistant general chat."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Protocol
from urllib.parse import parse_qs, quote_plus, unquote, urlsplit

from ..utils import CachedFetcher, normalize_text
from .models import KnowledgeChunk

try:
    from bs4 import BeautifulSoup
except Exception:  # noqa: BLE001
    BeautifulSoup = None


@dataclass(slots=True)
class ExternalSearchResult:
    title: str
    url: str
    snippet: str
    source: str = "duckduckgo"


class ExternalSearchClient(Protocol):
    def search(self, *, query: str) -> list[ExternalSearchResult]: ...


class DuckDuckGoHTMLSearchClient:
    def __init__(
        self,
        *,
        cache_dir: Path,
        timeout_seconds: float,
        max_results: int,
        cache_ttl_seconds: int,
        user_agent: str = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    ) -> None:
        self.fetcher = CachedFetcher(
            cache_dir=cache_dir,
            timeout=max(1.0, float(timeout_seconds)),
            delay_seconds=0.0,
            user_agent=user_agent,
        )
        self.max_results = max(0, int(max_results))
        self.cache_ttl_seconds = max(0, int(cache_ttl_seconds))

    def search(self, *, query: str) -> list[ExternalSearchResult]:
        normalized_query = normalize_text(query)
        if not normalized_query or self.max_results <= 0:
            return []
        if BeautifulSoup is None:
            raise RuntimeError("BeautifulSoupUnavailable")

        url = f"https://duckduckgo.com/html/?q={quote_plus(normalized_query)}"
        try:
            html = self.fetcher.fetch(
                url,
                headers={"Referer": "https://duckduckgo.com/"},
                delay_seconds=0.0,
                cache_ttl_seconds=self.cache_ttl_seconds,
            )
        except Exception:  # noqa: BLE001
            return []

        soup = BeautifulSoup(html, "lxml")
        results: list[ExternalSearchResult] = []
        seen_urls: set[str] = set()
        for block in soup.select("div.result"):
            link = block.select_one("a.result__a")
            if link is None:
                continue
            title = normalize_text(link.get_text(" ", strip=True))
            href = str(link.get("href") or "").strip()
            resolved_url = _unwrap_duckduckgo_href(href)
            if not title or not resolved_url or resolved_url in seen_urls:
                continue
            seen_urls.add(resolved_url)
            snippet_node = block.select_one(".result__snippet")
            snippet = normalize_text(
                snippet_node.get_text(" ", strip=True) if snippet_node is not None else ""
            )
            results.append(
                ExternalSearchResult(
                    title=title,
                    url=resolved_url,
                    snippet=snippet,
                )
            )
            if len(results) >= self.max_results:
                break
        return results


def build_external_search_chunks(
    *,
    query: str,
    results: list[ExternalSearchResult],
) -> list[KnowledgeChunk]:
    normalized_query = normalize_text(query)[:180]
    chunks: list[KnowledgeChunk] = []
    for rank, result in enumerate(results, start=1):
        domain = _extract_domain(result.url)
        text = "\n".join(
            line
            for line in (
                f"標題：{result.title}",
                f"摘要：{result.snippet}" if result.snippet else "",
                f"來源：{domain}" if domain else "",
                f"查詢：{normalized_query}" if normalized_query else "",
            )
            if line
        )
        chunks.append(
            KnowledgeChunk(
                chunk_id=_chunk_id(result=result, rank=rank),
                source_type="external-web",
                label=f"外部搜尋 #{rank}：{result.title}",
                text=text,
                url=result.url,
                metadata={
                    "provider": result.source,
                    "rank": rank,
                    "domain": domain,
                },
            )
        )
    return chunks


def _unwrap_duckduckgo_href(href: str) -> str:
    if not href:
        return ""
    parts = urlsplit(href)
    encoded_target = parse_qs(parts.query).get("uddg", [""])[0]
    if encoded_target:
        return unquote(encoded_target)
    return href


def _extract_domain(url: str) -> str:
    return urlsplit(url).netloc.lower().removeprefix("www.")


def _chunk_id(*, result: ExternalSearchResult, rank: int) -> str:
    digest = hashlib.sha256(f"{rank}:{result.url}:{result.title}".encode("utf-8")).hexdigest()
    return f"external-web-{digest[:16]}"

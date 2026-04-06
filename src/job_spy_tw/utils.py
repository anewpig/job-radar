"""Shared low-level utilities used across connectors and pipelines."""

from __future__ import annotations

import hashlib
import json
import re
import ssl
import time
from pathlib import Path
from typing import Iterable, Iterator, TypeVar
from urllib.error import URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen


T = TypeVar("T")

TAIWAN_LOCATION_PATTERN = re.compile(
    r"(台北市|新北市|桃園市|新竹市|新竹縣|台中市|臺中市|台南市|臺南市|高雄市|"
    r"基隆市|宜蘭縣|花蓮縣|台東縣|臺東縣|彰化縣|南投縣|雲林縣|嘉義縣|嘉義市|"
    r"屏東縣|苗栗縣|澎湖縣|金門縣|連江縣|Taipei|New Taipei|Hsinchu|"
    r"Taichung|Tainan|Kaohsiung|Taiwan)"
)
SALARY_PATTERN = re.compile(
    r"(月薪\s*[\d,]+(?:~[\d,]+)?元(?:以上)?|"
    r"年薪\s*[\d,]+(?:~[\d,]+)?元(?:以上)?|"
    r"待遇面議|面議（經常性薪資達4萬元或以上）|"
    r"時薪\s*[\d,]+(?:~[\d,]+)?元(?:以上)?|"
    r"薪資[^。]{0,18})"
)
POSTED_AT_PATTERN = re.compile(
    r"(\d+\s*(?:分鐘|小時|天|週|個月|月|年)前|\d{1,2}\s*/\s*\d{1,2})"
)


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text or "")
    return cleaned.strip()


def strip_query_params(url: str, keep: set[str] | None = None) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url
    keep = keep or set()
    query = [(key, value) for key, value in parse_qsl(parts.query) if key in keep]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def absolutize_url(base_url: str, href: str) -> str:
    return urljoin(base_url, href)


def first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return normalize_text(match.group(1)) if match else ""


def unique_preserving_order(items: Iterable[T]) -> list[T]:
    seen: set[T] = set()
    result: list[T] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def chunked(items: list[T], size: int) -> Iterator[list[T]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


class FileSystemCacheBackend:
    """檔案系統快取後端，負責 HTML 與對應 metadata 的讀寫與清理。"""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = ensure_directory(cache_dir)

    def entry_paths(self, cache_key: str) -> tuple[Path, Path]:
        html_path = self.cache_dir / f"{cache_key}.html"
        meta_path = self.cache_dir / f"{cache_key}.meta.json"
        return html_path, meta_path

    def read(self, cache_key: str) -> tuple[str | None, dict | None]:
        html_path, meta_path = self.entry_paths(cache_key)
        html = html_path.read_text(encoding="utf-8") if html_path.exists() else None
        meta = load_json(meta_path) if meta_path.exists() else None
        return html, meta

    def write(
        self,
        cache_key: str,
        *,
        html: str,
        meta: dict[str, object],
    ) -> None:
        html_path, meta_path = self.entry_paths(cache_key)
        html_path.write_text(html, encoding="utf-8")
        dump_json(meta_path, meta)

    def write_meta(self, cache_key: str, meta: dict[str, object]) -> None:
        _, meta_path = self.entry_paths(cache_key)
        dump_json(meta_path, meta)

    def delete(self, cache_key: str) -> None:
        html_path, meta_path = self.entry_paths(cache_key)
        if html_path.exists():
            html_path.unlink()
        if meta_path.exists():
            meta_path.unlink()

    def iter_entry_keys(self) -> list[str]:
        return sorted(path.stem for path in self.cache_dir.glob("*.html"))


class CachedFetcher:
    def __init__(
        self,
        cache_dir: Path,
        timeout: float,
        delay_seconds: float,
        user_agent: str,
        allow_insecure_ssl_fallback: bool = True,
        backend: str = "filesystem",
    ) -> None:
        self.cache_dir = ensure_directory(cache_dir)
        self.timeout = timeout
        self.delay_seconds = delay_seconds
        self.user_agent = user_agent
        self.allow_insecure_ssl_fallback = allow_insecure_ssl_fallback
        if backend != "filesystem":
            raise ValueError(f"Unsupported cache backend: {backend}")
        self.backend = FileSystemCacheBackend(self.cache_dir)

    def fetch(
        self,
        url: str,
        force_refresh: bool = False,
        headers: dict[str, str] | None = None,
        delay_seconds: float | None = None,
        cache_ttl_seconds: float | None = None,
    ) -> str:
        cache_key = hashlib.sha256(url.encode()).hexdigest()
        cached_html, meta = self.backend.read(cache_key)
        if cached_html is not None and not force_refresh:
            cache_meta = self._normalize_cache_meta(
                cache_key=cache_key,
                url=url,
                meta=meta,
                fallback_path=self.backend.entry_paths(cache_key)[0],
                cache_ttl_seconds=cache_ttl_seconds,
            )
            if self._is_cache_fresh(cache_meta):
                self._touch_cache_entry(cache_key, cache_meta)
                return cached_html

        request = Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
                **(headers or {}),
            },
        )
        raw = self._open_with_fallback(request)
        html = raw.decode("utf-8", errors="ignore")
        effective_ttl = (
            0.0 if cache_ttl_seconds is None else max(0.0, float(cache_ttl_seconds))
        )
        now_ts = time.time()
        self.backend.write(
            cache_key,
            html=html,
            meta={
                "url": url,
                "created_at_ts": now_ts,
                "last_accessed_at_ts": now_ts,
                "ttl_seconds": effective_ttl,
            },
        )
        effective_delay = self.delay_seconds if delay_seconds is None else delay_seconds
        if effective_delay and effective_delay > 0:
            time.sleep(effective_delay)
        return html

    def purge_cache(self, *, max_bytes: int, max_files: int) -> None:
        """依 TTL、檔案數與總容量清理檔案系統快取。"""
        entries: list[tuple[str, int, dict[str, object]]] = []
        now_ts = time.time()
        for meta_path in self.cache_dir.glob("*.meta.json"):
            cache_key = meta_path.name[: -len(".meta.json")]
            html_path, _ = self.backend.entry_paths(cache_key)
            if not html_path.exists():
                meta_path.unlink()
        for cache_key in self.backend.iter_entry_keys():
            html_path, meta_path = self.backend.entry_paths(cache_key)
            cached_html, meta = self.backend.read(cache_key)
            if cached_html is None:
                self.backend.delete(cache_key)
                continue
            cache_meta = self._normalize_cache_meta(
                cache_key=cache_key,
                url=str((meta or {}).get("url") or ""),
                meta=meta,
                fallback_path=html_path,
                cache_ttl_seconds=None,
            )
            if self._is_cache_expired(cache_meta, now_ts):
                self.backend.delete(cache_key)
                continue
            entry_size = html_path.stat().st_size
            if meta_path.exists():
                entry_size += meta_path.stat().st_size
            entries.append((cache_key, entry_size, cache_meta))

        total_bytes = sum(size for _, size, _ in entries)
        max_files = max(0, int(max_files))
        max_bytes = max(0, int(max_bytes))
        if (max_files and len(entries) <= max_files) and (max_bytes and total_bytes <= max_bytes):
            return
        if not max_files:
            max_files = len(entries)
        if not max_bytes:
            max_bytes = total_bytes
        entries.sort(
            key=lambda item: float(item[2].get("last_accessed_at_ts") or item[2].get("created_at_ts") or 0.0)
        )
        while entries and (len(entries) > max_files or total_bytes > max_bytes):
            cache_key, size, _ = entries.pop(0)
            self.backend.delete(cache_key)
            total_bytes -= size

    def _build_ssl_context(self) -> ssl.SSLContext:
        try:
            import certifi

            return ssl.create_default_context(cafile=certifi.where())
        except Exception:  # noqa: BLE001
            return ssl.create_default_context()

    def _open_with_fallback(self, request: Request) -> bytes:
        ssl_context = self._build_ssl_context()
        try:
            with urlopen(request, timeout=self.timeout, context=ssl_context) as response:
                return response.read()
        except URLError as exc:
            message = str(exc)
            if (
                self.allow_insecure_ssl_fallback
                and "CERTIFICATE_VERIFY_FAILED" in message
            ):
                insecure_context = ssl._create_unverified_context()
                with urlopen(
                    request, timeout=self.timeout, context=insecure_context
                ) as response:
                    return response.read()
            raise

    def _normalize_cache_meta(
        self,
        *,
        cache_key: str,
        url: str,
        meta: dict | None,
        fallback_path: Path,
        cache_ttl_seconds: float | None,
    ) -> dict[str, object]:
        if meta:
            normalized = dict(meta)
            if cache_ttl_seconds is not None:
                normalized["ttl_seconds"] = max(0.0, float(cache_ttl_seconds))
            return normalized
        fallback_stat = fallback_path.stat()
        fallback_ts = float(fallback_stat.st_mtime)
        normalized = {
            "url": url,
            "created_at_ts": fallback_ts,
            "last_accessed_at_ts": fallback_ts,
            "ttl_seconds": 0.0 if cache_ttl_seconds is None else max(0.0, float(cache_ttl_seconds)),
        }
        cached_html = fallback_path.read_text(encoding="utf-8")
        self.backend.write(cache_key, html=cached_html, meta=normalized)
        return normalized

    def _is_cache_expired(self, meta: dict[str, object], now_ts: float | None = None) -> bool:
        ttl_seconds = float(meta.get("ttl_seconds") or 0.0)
        if ttl_seconds <= 0:
            return False
        now_ts = time.time() if now_ts is None else now_ts
        created_at_ts = float(meta.get("created_at_ts") or 0.0)
        return created_at_ts + ttl_seconds <= now_ts

    def _is_cache_fresh(self, meta: dict[str, object]) -> bool:
        return not self._is_cache_expired(meta)

    def _touch_cache_entry(
        self,
        cache_key: str,
        meta: dict[str, object],
    ) -> None:
        updated_meta = dict(meta)
        updated_meta["last_accessed_at_ts"] = time.time()
        self.backend.write_meta(cache_key, updated_meta)


def dump_json(path: Path, payload: dict) -> None:
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

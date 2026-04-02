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


class CachedFetcher:
    def __init__(
        self,
        cache_dir: Path,
        timeout: float,
        delay_seconds: float,
        user_agent: str,
        allow_insecure_ssl_fallback: bool = True,
    ) -> None:
        self.cache_dir = ensure_directory(cache_dir)
        self.timeout = timeout
        self.delay_seconds = delay_seconds
        self.user_agent = user_agent
        self.allow_insecure_ssl_fallback = allow_insecure_ssl_fallback

    def fetch(
        self,
        url: str,
        force_refresh: bool = False,
        headers: dict[str, str] | None = None,
    ) -> str:
        cache_path = self.cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()}.html"
        if cache_path.exists() and not force_refresh:
            return cache_path.read_text(encoding="utf-8")

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
        cache_path.write_text(html, encoding="utf-8")
        time.sleep(self.delay_seconds)
        return html

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


def dump_json(path: Path, payload: dict) -> None:
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

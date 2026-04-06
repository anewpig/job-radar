"""Helpers for splitting raw job descriptions into structured sections."""

from __future__ import annotations

from html import unescape
import json
import re
from collections.abc import Iterable

from bs4 import BeautifulSoup

from .utils import normalize_text, unique_preserving_order

NOISE_LINES = {
    "展開全部",
    "收合內容",
    "查看更多",
    "查看全部",
    "職缺描述",
    "工作內容",
    "要求條件",
    "工作技能",
    "附加條件",
    "【工作內容】",
    "【相關條件】",
    "【其他條件】",
    "Job Description",
    "Requirements",
    "Qualifications",
    "Education",
    "Work Experience",
    "Language",
}

NUMBERED_ITEM_PATTERN = re.compile(r"^\s*\d{1,2}[.)、．]\s*(.+)$")
BULLET_ITEM_PATTERN = re.compile(r"^\s*(?:[-*•●▪■○oO·‧])\s*(.+)$")
REQUIREMENT_CUE_PATTERN = re.compile(
    r"(具備|熟悉|了解|精通|experience|require|qualification|must|skill|"
    r"knowledge|proficient|able to|工作經驗|學歷|英文|語文|SQL|API|LLM|Python|"
    r"Java|Docker|Kubernetes|Prompt|RAG|ChatGPT|NLP|Machine Learning|"
    r"\bAI\b|生成式|法遵|需求分析|資訊安全|資料隱私)",
    re.IGNORECASE,
)
ACTION_OR_REQUIREMENT_PREFIX_PATTERN = re.compile(
    r"^(具備|熟悉|了解|精通|規劃|推動|協助|蒐集|作為|評估|配合|追蹤|提升|"
    r"運用|串接|開發|撰寫|分析|建立|負責|支援|設計|導入|能|可|對)",
    re.IGNORECASE,
)


def merge_unique_items(*groups: Iterable[str]) -> list[str]:
    items: list[str] = []
    for group in groups:
        items.extend(item for item in group if item)
    return unique_preserving_order(items)


def split_structured_items(text: str, keep_unspecified: bool = False) -> list[str]:
    if not text:
        return []

    prepared = _normalize_structured_source_text(text)
    prepared = prepared.replace("\r\n", "\n").replace("\r", "\n")
    prepared = re.sub(r"<br\s*/?>", "\n", prepared, flags=re.IGNORECASE)
    prepared = re.sub(r"(?<!\n)(\d{1,2}[.)、．]\s*)", r"\n\1", prepared)
    lines = [line.strip() for line in prepared.splitlines()]

    items: list[str] = []
    current_prefix = ""
    for index, raw_line in enumerate(lines):
        line = normalize_text(raw_line)
        if not line:
            continue
        line = line.replace("展開全部", "").replace("收合內容", "").strip()
        if not line or line in NOISE_LINES:
            continue

        numbered = NUMBERED_ITEM_PATTERN.match(line)
        if numbered:
            content = normalize_text(numbered.group(1))
            next_line = _next_meaningful_line(lines, index + 1)
            if next_line and _should_be_prefix(content) and not _starts_structured_item(next_line):
                current_prefix = content.rstrip("：:")
            else:
                items.append(content)
                current_prefix = ""
            continue

        bullet = BULLET_ITEM_PATTERN.match(line)
        if bullet:
            content = normalize_text(bullet.group(1))
            if content:
                items.append(_apply_prefix(current_prefix, content))
            continue

        if line.endswith(("：", ":")) and len(line) <= 80:
            current_prefix = line.rstrip("：:")
            continue

        if current_prefix:
            items.append(_apply_prefix(current_prefix, line))
        else:
            items.append(line)

    deduped = unique_preserving_order(
        item for item in items if item and (keep_unspecified or item != "不拘")
    )
    return deduped


def extract_labeled_section(
    text: str,
    label: str,
    next_labels: list[str],
) -> str:
    if not text or label not in text:
        return ""
    remainder = text.split(label, 1)[1]
    end_indexes = [remainder.find(next_label) for next_label in next_labels]
    positive_indexes = [index for index in end_indexes if index != -1]
    if positive_indexes:
        remainder = remainder[: min(positive_indexes)]
    return remainder.strip("；; \n")


def extract_jobposting_description(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        job_posting = _find_job_posting(payload)
        if job_posting:
            description = normalize_text(str(job_posting.get("description", "")))
            if description:
                return description
    return ""


def select_requirement_like_items(items: list[str]) -> list[str]:
    return unique_preserving_order(
        item for item in items if REQUIREMENT_CUE_PATTERN.search(item)
    )


def _find_job_posting(payload):
    if isinstance(payload, dict):
        if payload.get("@type") == "JobPosting":
            return payload
        for value in payload.values():
            found = _find_job_posting(value)
            if found:
                return found
        return None
    if isinstance(payload, list):
        for item in payload:
            found = _find_job_posting(item)
            if found:
                return found
    return None


def _apply_prefix(prefix: str, content: str) -> str:
    cleaned_prefix = normalize_text(prefix).rstrip("：:")
    cleaned_content = normalize_text(content)
    if not cleaned_prefix:
        return cleaned_content
    if cleaned_content.startswith(cleaned_prefix):
        return cleaned_content
    return f"{cleaned_prefix}：{cleaned_content}"


def _should_be_prefix(content: str) -> bool:
    if content.endswith(("：", ":")):
        return True
    if ACTION_OR_REQUIREMENT_PREFIX_PATTERN.search(content):
        return False
    return len(content) <= 32 and not re.search(r"[。；;!?！？]", content)


def _normalize_structured_source_text(text: str) -> str:
    prepared = unescape(text).replace("\u3000", " ")
    if "<" not in prepared or ">" not in prepared:
        return prepared

    soup = BeautifulSoup(prepared, "lxml")
    if soup.find(["li", "br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "ol", "ul"]):
        return soup.get_text("\n", strip=False)
    return prepared


def _next_meaningful_line(lines: list[str], start_index: int) -> str:
    for raw_line in lines[start_index:]:
        normalized = normalize_text(raw_line).replace("展開全部", "").replace("收合內容", "").strip()
        if normalized and normalized not in NOISE_LINES:
            return normalized
    return ""


def _starts_structured_item(line: str) -> bool:
    if not line:
        return False
    return bool(NUMBERED_ITEM_PATTERN.match(line) or BULLET_ITEM_PATTERN.match(line))

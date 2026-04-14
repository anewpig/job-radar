"""Canonical normalization and duplicate-merge helpers for job records."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import re
from urllib.parse import urlsplit, urlunsplit

from .models import JobListing
from .utils import normalize_text, unique_preserving_order


FULLWIDTH_TRANSLATION = str.maketrans(
    {
        "（": "(",
        "）": ")",
        "【": "[",
        "】": "]",
        "／": "/",
        "－": "-",
        "—": "-",
        "：": ":",
        "，": ",",
        "。": ".",
        "　": " ",
    }
)
ALNUM_CJK_PATTERN = re.compile(r"[^0-9a-z\u4e00-\u9fff]+")
PAREN_CONTENT_PATTERN = re.compile(r"\(([^()]*)\)")
TITLE_CONTEXT_HINTS = (
    "台北",
    "新北",
    "桃園",
    "新竹",
    "台中",
    "台南",
    "高雄",
    "taipei",
    "taichung",
    "tainan",
    "kaohsiung",
    "北部",
    "中部",
    "南部",
    "總公司",
    "分公司",
    "區域",
    "remote",
    "hybrid",
)
COMPANY_SUFFIX_TOKENS = (
    "股份有限公司",
    "有限公司",
    "股份有限",
    "公司",
    "corporation",
    "corp",
    "incorporated",
    "inc",
    "co ltd",
    "co.,ltd",
    "co., ltd",
    "limited",
    "ltd",
)
CITY_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("新北市", ("new taipei city", "new taipei", "新北市")),
    ("台北市", ("taipei city", "taipei", "台北市", "臺北市")),
    ("桃園市", ("taoyuan city", "taoyuan", "桃園市")),
    ("新竹市", ("hsinchu city", "hsinchu city/taiwan", "新竹市")),
    ("新竹縣", ("hsinchu county", "新竹縣")),
    ("台中市", ("taichung city", "taichung", "台中市", "臺中市")),
    ("台南市", ("tainan city", "tainan", "台南市", "臺南市")),
    ("高雄市", ("kaohsiung city", "kaohsiung", "高雄市")),
    ("基隆市", ("keelung", "基隆市")),
    ("宜蘭縣", ("yilan", "宜蘭縣")),
    ("花蓮縣", ("hualien", "花蓮縣")),
    ("台東縣", ("taitung", "台東縣", "臺東縣")),
    ("彰化縣", ("changhua", "彰化縣")),
    ("南投縣", ("nantou", "南投縣")),
    ("雲林縣", ("yunlin", "雲林縣")),
    ("嘉義市", ("chiayi city", "嘉義市")),
    ("嘉義縣", ("chiayi county", "嘉義縣")),
    ("屏東縣", ("pingtung", "屏東縣")),
    ("苗栗縣", ("miaoli", "苗栗縣")),
    ("澎湖縣", ("penghu", "澎湖縣")),
    ("金門縣", ("kinmen", "金門縣")),
    ("連江縣", ("lienchiang", "連江縣")),
)


def normalize_job_listing(job: JobListing) -> JobListing:
    """Normalize lightweight display text and attach canonical match metadata."""
    job.title = _normalize_display_text(job.title)
    job.company = _normalize_display_text(job.company)
    job.location = _normalize_display_text(job.location)
    job.url = normalize_job_url(job.url)
    job.summary = _normalize_display_text(job.summary)
    job.description = _normalize_multiline_text(job.description)
    job.salary = _normalize_display_text(job.salary)
    job.posted_at = _normalize_display_text(job.posted_at)
    job.matched_role = _normalize_display_text(job.matched_role)
    job.extracted_skills = _normalize_list(job.extracted_skills)
    job.work_content_items = _normalize_list(job.work_content_items)
    job.required_skill_items = _normalize_list(job.required_skill_items)
    job.requirement_items = _normalize_list(job.requirement_items)
    job.tags = _normalize_list(job.tags)
    job.detail_sections = {
        _normalize_display_text(name): _normalize_multiline_text(value)
        for name, value in job.detail_sections.items()
        if _normalize_display_text(name) and _normalize_multiline_text(value)
    }
    canonical_title = canonicalize_title(job.title)
    canonical_company = canonicalize_company(job.company)
    canonical_location = canonicalize_location(job.location)
    canonical_salary = canonicalize_salary(job.salary)
    canonical_url = normalize_job_url(job.url)
    canonical_identity_key = build_canonical_identity_key(
        title=canonical_title,
        company=canonical_company,
        location=canonical_location,
    )
    source_record_id = build_source_record_id(
        job=job,
        canonical_url=canonical_url,
        canonical_title=canonical_title,
        canonical_company=canonical_company,
        canonical_location=canonical_location,
    )
    lineage_entry = build_lineage_entry(
        job=job,
        source_record_id=source_record_id,
        canonical_identity_key=canonical_identity_key,
        canonical_url=canonical_url,
    )
    job.source_record_id = source_record_id
    job.canonical_identity_key = canonical_identity_key
    job.lineage_trail = [lineage_entry]
    job.metadata = {
        **dict(job.metadata or {}),
        "canonical_title": canonical_title,
        "canonical_company": canonical_company,
        "canonical_location": canonical_location,
        "canonical_salary": canonical_salary,
        "canonical_url": canonical_url,
        "canonical_identity_key": canonical_identity_key,
        "source_record_id": source_record_id,
        "lineage_trail": [lineage_entry],
    }
    return job


def merge_duplicate_jobs(jobs: list[JobListing]) -> list[JobListing]:
    """Merge same-source and cross-source duplicates after canonical normalization."""
    normalized_jobs = [normalize_job_listing(deepcopy(job)) for job in jobs]
    exact_groups: dict[str, list[JobListing]] = {}
    leftovers: list[JobListing] = []
    for job in normalized_jobs:
        exact_key = _exact_duplicate_key(job)
        if exact_key:
            exact_groups.setdefault(exact_key, []).append(job)
        else:
            leftovers.append(job)

    exact_merged = [_merge_job_group(group) for group in exact_groups.values()]
    candidates = [*exact_merged, *leftovers]
    buckets: dict[tuple[str, str, str], list[JobListing]] = {}
    passthrough: list[JobListing] = []
    for job in candidates:
        identity_key = _canonical_bucket_key(job)
        if identity_key is None:
            passthrough.append(job)
            continue
        buckets.setdefault(identity_key, []).append(job)

    merged: list[JobListing] = []
    for bucket_jobs in buckets.values():
        clusters: list[list[JobListing]] = []
        for job in bucket_jobs:
            for cluster in clusters:
                if _should_merge_identity_match(cluster[0], job):
                    cluster.append(job)
                    break
            else:
                clusters.append([job])
        merged.extend(_merge_job_group(cluster) for cluster in clusters)
    merged.extend(passthrough)
    return merged


def canonicalize_title(title: str) -> str:
    normalized = _normalize_for_match(title, lower=True)

    def _replace_context(match: re.Match[str]) -> str:
        inner = _normalize_for_match(match.group(1), lower=True)
        if any(token in inner for token in TITLE_CONTEXT_HINTS):
            return ""
        return match.group(0)

    normalized = PAREN_CONTENT_PATTERN.sub(_replace_context, normalized)
    return ALNUM_CJK_PATTERN.sub("", normalized)


def canonicalize_company(company: str) -> str:
    normalized = _normalize_for_match(company, lower=True)
    normalized = PAREN_CONTENT_PATTERN.sub("", normalized)
    normalized = ALNUM_CJK_PATTERN.sub("", normalized)
    while True:
        previous = normalized
        for suffix in COMPANY_SUFFIX_TOKENS:
            compact_suffix = ALNUM_CJK_PATTERN.sub("", _normalize_for_match(suffix, lower=True))
            if compact_suffix and normalized.endswith(compact_suffix):
                normalized = normalized[: -len(compact_suffix)]
        if normalized == previous:
            break
    return normalized


def canonicalize_location(location: str) -> str:
    normalized = _normalize_for_match(location, lower=True)
    for canonical, aliases in CITY_ALIASES:
        if any(alias in normalized for alias in aliases):
            return canonical
    if "taiwan" in normalized or "台灣" in normalized:
        return "台灣"
    return ALNUM_CJK_PATTERN.sub("", normalized)


def canonicalize_salary(salary: str) -> str:
    normalized = _normalize_for_match(salary, lower=True)
    if not normalized:
        return ""
    if "面議" in normalized:
        return "negotiable"
    kind = "salary"
    if "月薪" in normalized:
        kind = "monthly"
    elif "年薪" in normalized:
        kind = "annual"
    elif "時薪" in normalized:
        kind = "hourly"
    numbers = re.findall(r"\d[\d,]*", normalized)
    compact = "-".join(number.replace(",", "") for number in numbers[:2])
    return f"{kind}:{compact}" if compact else kind


def normalize_job_url(url: str) -> str:
    normalized = _normalize_display_text(url)
    if not normalized:
        return ""
    try:
        parts = urlsplit(normalized)
    except Exception:  # noqa: BLE001
        return normalized
    if not parts.scheme or not parts.netloc:
        return normalized
    path = re.sub(r"/{2,}", "/", parts.path or "").rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def build_canonical_identity_key(*, title: str, company: str, location: str) -> str:
    if not title or not company or not location or location == "台灣":
        return ""
    return f"{company}|{title}|{location}"


def build_source_record_id(
    *,
    job: JobListing,
    canonical_url: str,
    canonical_title: str,
    canonical_company: str,
    canonical_location: str,
) -> str:
    metadata = job.metadata or {}
    for key in ("source_record_id", "job_no", "job_code", "job_id", "record_id"):
        value = str(metadata.get(key, "")).strip()
        if value:
            return f"{job.source}:{value}"
    if canonical_url:
        return f"{job.source}:{canonical_url}"
    raw = "|".join(
        [
            str(job.source or "").strip(),
            canonical_company,
            canonical_title,
            canonical_location,
        ]
    )
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"{job.source}:{digest}"


def build_lineage_entry(
    *,
    job: JobListing,
    source_record_id: str,
    canonical_identity_key: str,
    canonical_url: str,
) -> dict[str, str]:
    return {
        "source": str(job.source or "").strip(),
        "source_record_id": source_record_id,
        "source_url": str(job.url or "").strip(),
        "canonical_url": canonical_url,
        "canonical_identity_key": canonical_identity_key,
        "title": str(job.title or "").strip(),
        "company": str(job.company or "").strip(),
        "location": str(job.location or "").strip(),
    }


def _normalize_display_text(text: str) -> str:
    return normalize_text(str(text or "").translate(FULLWIDTH_TRANSLATION).replace("臺", "台"))


def _normalize_multiline_text(text: str) -> str:
    lines = [_normalize_display_text(line) for line in str(text or "").splitlines()]
    return "\n".join(line for line in lines if line)


def _normalize_list(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    for value in values or []:
        item = _normalize_display_text(value)
        if not item:
            continue
        stripped = item.strip("[]()（）【】").strip()
        stripped = stripped.rstrip(":：").strip()
        if stripped == "工作條件":
            continue
        cleaned.append(item)
    return unique_preserving_order(cleaned)


def _normalize_for_match(text: str, *, lower: bool) -> str:
    normalized = _normalize_display_text(text)
    return normalized.lower() if lower else normalized


def _exact_duplicate_key(job: JobListing) -> str:
    metadata = job.metadata or {}
    canonical_url = str(metadata.get("canonical_url", "")).strip()
    if canonical_url:
        return canonical_url
    title = str(metadata.get("canonical_title", "")).strip()
    company = str(metadata.get("canonical_company", "")).strip()
    location = str(metadata.get("canonical_location", "")).strip()
    if title and company and location and location != "台灣":
        return f"{job.source}|{company}|{title}|{location}"
    return ""


def _canonical_bucket_key(job: JobListing) -> tuple[str, str, str] | None:
    metadata = job.metadata or {}
    company = str(metadata.get("canonical_company", "")).strip()
    title = str(metadata.get("canonical_title", "")).strip()
    location = str(metadata.get("canonical_location", "")).strip()
    if not company or not title or not location or location == "台灣":
        return None
    return (company, title, location)


def _salary_compatible(left: JobListing, right: JobListing) -> bool:
    left_salary = str((left.metadata or {}).get("canonical_salary", "")).strip()
    right_salary = str((right.metadata or {}).get("canonical_salary", "")).strip()
    if not left_salary or not right_salary:
        return True
    return left_salary == right_salary


def _should_merge_identity_match(existing: JobListing, candidate: JobListing) -> bool:
    existing_bucket = _canonical_bucket_key(existing)
    candidate_bucket = _canonical_bucket_key(candidate)
    if existing_bucket is None or candidate_bucket is None or existing_bucket != candidate_bucket:
        return False
    if not _salary_compatible(existing, candidate):
        return False
    existing_url = str((existing.metadata or {}).get("canonical_url", "")).strip()
    candidate_url = str((candidate.metadata or {}).get("canonical_url", "")).strip()
    if existing.source == candidate.source and existing_url and candidate_url and existing_url != candidate_url:
        return False
    return True


def _job_richness_score(job: JobListing) -> tuple[float, int, int, int]:
    metadata = job.metadata or {}
    text_score = (
        len(job.description)
        + len(job.summary)
        + len(job.salary)
        + len(job.posted_at)
        + sum(len(value) for value in job.detail_sections.values())
    )
    list_score = (
        len(job.extracted_skills)
        + len(job.work_content_items)
        + len(job.required_skill_items)
        + len(job.requirement_items)
        + len(job.tags)
    )
    filled_fields = sum(
        1
        for value in (
            job.title,
            job.company,
            job.location,
            job.url,
            job.summary,
            job.description,
            job.salary,
            job.posted_at,
        )
        if value
    )
    relevance = float(job.relevance_score or 0.0)
    if metadata.get("detail_enriched"):
        text_score += 200
    return (relevance, text_score + list_score * 12 + filled_fields * 8, len(job.detail_sections), len(job.metadata))


def _merge_job_group(jobs: list[JobListing]) -> JobListing:
    primary = max(jobs, key=_job_richness_score)
    merged = deepcopy(primary)
    source_values: list[str] = []
    url_values: list[str] = []
    canonical_url_values: list[str] = []
    source_record_ids: list[str] = []
    lineage_entries: list[dict[str, str]] = []
    for job in jobs:
        if job.source:
            source_values.append(job.source)
        source_values.extend(str(value) for value in (job.metadata or {}).get("source_aliases", []) if str(value).strip())
        if job.url:
            url_values.append(job.url)
        url_values.extend(str(value) for value in (job.metadata or {}).get("source_urls", []) if str(value).strip())
        canonical_url = str((job.metadata or {}).get("canonical_url", "")).strip()
        if canonical_url:
            canonical_url_values.append(canonical_url)
        canonical_url_values.extend(
            str(value) for value in (job.metadata or {}).get("canonical_urls", []) if str(value).strip()
        )
        if job.source_record_id:
            source_record_ids.append(job.source_record_id)
        source_record_ids.extend(
            str(value)
            for value in (job.metadata or {}).get("source_record_ids", [])
            if str(value).strip()
        )
        existing_lineage = job.lineage_trail or list((job.metadata or {}).get("lineage_trail", []))
        if existing_lineage:
            lineage_entries.extend(
                entry
                for entry in existing_lineage
                if isinstance(entry, dict)
            )
        elif job.source_record_id:
            lineage_entries.append(
                build_lineage_entry(
                    job=job,
                    source_record_id=job.source_record_id,
                    canonical_identity_key=job.canonical_identity_key or str((job.metadata or {}).get("canonical_identity_key", "")),
                    canonical_url=str((job.metadata or {}).get("canonical_url", "")).strip(),
                )
            )
    sources = unique_preserving_order(source_values)
    urls = unique_preserving_order(url_values)
    canonical_urls = unique_preserving_order(canonical_url_values)
    unique_source_record_ids = unique_preserving_order(source_record_ids)
    for job in jobs:
        if job is primary:
            continue
        merged.summary = _prefer_richer_text(merged.summary, job.summary)
        merged.description = _prefer_richer_text(merged.description, job.description)
        merged.salary = _prefer_richer_text(merged.salary, job.salary)
        merged.posted_at = _prefer_richer_text(merged.posted_at, job.posted_at)
        merged.matched_role = _prefer_richer_text(merged.matched_role, job.matched_role)
        merged.extracted_skills = unique_preserving_order([*merged.extracted_skills, *job.extracted_skills])
        merged.work_content_items = unique_preserving_order([*merged.work_content_items, *job.work_content_items])
        merged.required_skill_items = unique_preserving_order([*merged.required_skill_items, *job.required_skill_items])
        merged.requirement_items = unique_preserving_order([*merged.requirement_items, *job.requirement_items])
        merged.tags = unique_preserving_order([*merged.tags, *job.tags])
        for section_name, section_text in job.detail_sections.items():
            merged.detail_sections[section_name] = _prefer_richer_text(
                merged.detail_sections.get(section_name, ""),
                section_text,
            )
        for key, value in (job.metadata or {}).items():
            if key not in merged.metadata or not merged.metadata.get(key):
                merged.metadata[key] = value

    merged.metadata.update(
        {
            "source_aliases": sources,
            "source_urls": urls,
            "canonical_urls": canonical_urls,
            "source_record_ids": unique_source_record_ids,
            "lineage_trail": _unique_lineage_entries(lineage_entries),
            "merged_job_count": len(jobs),
            "cross_source_merged": len(set(sources)) > 1,
            "lineage_record_count": len(_unique_lineage_entries(lineage_entries)),
        }
    )
    merged.source_record_id = primary.source_record_id or (unique_source_record_ids[0] if unique_source_record_ids else "")
    merged.canonical_identity_key = (
        primary.canonical_identity_key
        or str(merged.metadata.get("canonical_identity_key", "")).strip()
    )
    merged.lineage_trail = _unique_lineage_entries(lineage_entries)
    return merged


def _prefer_richer_text(existing: str, candidate: str) -> str:
    existing_text = _normalize_display_text(existing)
    candidate_text = _normalize_display_text(candidate)
    if len(candidate_text) > len(existing_text):
        return candidate_text
    return existing_text


def _unique_lineage_entries(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    ordered: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in entries:
        source_record_id = str(entry.get("source_record_id", "")).strip()
        source_url = str(entry.get("source_url", "")).strip()
        key = source_record_id or source_url
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(
            {
                "source": str(entry.get("source", "")).strip(),
                "source_record_id": source_record_id,
                "source_url": source_url,
                "canonical_url": str(entry.get("canonical_url", "")).strip(),
                "canonical_identity_key": str(entry.get("canonical_identity_key", "")).strip(),
                "title": str(entry.get("title", "")).strip(),
                "company": str(entry.get("company", "")).strip(),
                "location": str(entry.get("location", "")).strip(),
            }
        )
    return ordered

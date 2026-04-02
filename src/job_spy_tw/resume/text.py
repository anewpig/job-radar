from __future__ import annotations

from io import BytesIO
import re
from typing import Iterable
import unicodedata

from ..utils import TAIWAN_LOCATION_PATTERN, normalize_text, unique_preserving_order


DOMAIN_TAXONOMY: dict[str, tuple[str, ...]] = {
    "生成式 AI": ("生成式 ai", "genai", "gpt", "copilot"),
    "企業 AI 導入": ("企業 ai", "ai 導入", "數位轉型", "digital transformation"),
    "資料分析": ("資料分析", "data analysis", "analytics", "bi"),
    "資料工程": ("資料工程", "etl", "data pipeline", "資料管線"),
    "產品 / PM": ("product", "roadmap", "prd", "產品規劃", "產品管理"),
    "專案管理": ("project", "milestone", "scrum", "專案管理"),
    "流程自動化": ("automation", "自動化", "流程優化", "效率提升"),
    "雲端 / 維運": ("cloud", "aws", "gcp", "azure", "docker", "kubernetes"),
    "客戶 / 技術支援": ("客戶", "client", "support", "售前", "fae"),
}

COMMON_ENCODINGS = ("utf-8-sig", "utf-8", "utf-16", "big5", "cp950")
TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+/#.-]{1,}|[\u4e00-\u9fff]{2,}")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.\w+", re.IGNORECASE)
PHONE_PATTERN = re.compile(
    r"(?:(?:\+886[-\s]?)?0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{3,4}|\d{2,4}[-\s]?\d{6,8})"
)
URL_PATTERN = re.compile(r"https?://|linkedin\.com|github\.com", re.IGNORECASE)
ADDRESS_PATTERN = re.compile(
    r"(?:台北市|新北市|桃園市|新竹市|新竹縣|台中市|臺中市|台南市|臺南市|高雄市|"
    r"基隆市|宜蘭縣|花蓮縣|台東縣|臺東縣|彰化縣|南投縣|雲林縣|嘉義縣|嘉義市|"
    r"屏東縣|苗栗縣|澎湖縣|金門縣|連江縣).{0,12}(?:區|鄉|鎮|市).{0,24}"
    r"(?:路|街|大道|段|巷|弄|號|樓)"
)
LICENSE_PATTERN = re.compile(r"(?:駕照|普通重型機車|普通小型車|職業小客車)", re.IGNORECASE)
ADDRESS_FRAGMENT_PATTERN = re.compile(r"(?:地址|縣市|市區|區域|路|街|巷|弄|段|號|樓)")
LICENSE_FRAGMENT_PATTERN = re.compile(r"(?:重型|小型車|機車|汽車|駕照)")
PROFILE_META_PATTERN = re.compile(
    r"(?:\b男\b|\b女\b|性別|年齡|歲|出生|生日|兵役|婚姻|聯絡方式|手機|電話|地址|email|e-mail)",
    re.IGNORECASE,
)
GARBLED_CHAR_PATTERN = re.compile(r"[�□■￼]")
ACTION_PREFIX_PATTERN = re.compile(r"^(?:曾|負責|參與|熟悉|具備|協助|主導|完成|規劃|推動)")
NAME_LABEL_PATTERN = re.compile(r"(姓名\s*[:：]?\s*)([A-Za-z\u4e00-\u9fff]{2,20})")
SAFE_SHORT_DOMAIN_TERMS = {
    "金融",
    "醫療",
    "教育",
    "製造",
    "零售",
    "電商",
    "雲端",
    "資安",
    "半導體",
}
SAFE_DOMAIN_ACRONYMS = {"AI", "LLM", "RAG", "NLP", "CV", "AWS", "GCP", "BI", "ETL", "PM"}
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "have",
    "using",
    "used",
    "ability",
    "experience",
    "skills",
    "skill",
    "resume",
    "work",
    "job",
    "project",
    "projects",
    "years",
    "year",
    "team",
    "teams",
    "履歷",
    "經驗",
    "專案",
    "工作",
    "技能",
    "能力",
    "熟悉",
    "具備",
    "負責",
    "email",
    "mail",
    "gmail",
    "yahoo",
    "hotmail",
    "outlook",
    "com",
    "tw",
    "地址",
    "電話",
    "手機",
    "聯絡",
    "駕照",
    "兵役",
    "出生",
    "生日",
    "年齡",
    "男",
    "女",
}


def extract_resume_text(file_name: str, raw_bytes: bytes) -> tuple[str, list[str]]:
    suffix = ""
    if "." in file_name:
        suffix = file_name.rsplit(".", 1)[-1].lower()
    notes: list[str] = []

    if suffix in {"txt", "md"}:
        text = _decode_text_bytes(raw_bytes)
    elif suffix == "pdf":
        text, message = _extract_pdf_text(raw_bytes)
        if message:
            notes.append(message)
    elif suffix == "docx":
        text, message = _extract_docx_text(raw_bytes)
        if message:
            notes.append(message)
    else:
        text = _decode_text_bytes(raw_bytes)
        if not text:
            notes.append(
                "這個檔案格式目前沒有自動解析，建議改上傳 TXT / MD，或把履歷文字直接貼上。"
            )

    text = _sanitize_extracted_text(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        notes.append("沒有讀到可分析的履歷文字內容。")
    return text, unique_preserving_order(notes)


def _decode_text_bytes(raw_bytes: bytes) -> str:
    for encoding in COMMON_ENCODINGS:
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="ignore")


def _sanitize_extracted_text(text: str) -> str:
    sanitized = unicodedata.normalize("NFKC", text or "")
    sanitized = re.sub(r"[\u200b-\u200f\ufeff]", "", sanitized)
    sanitized = GARBLED_CHAR_PATTERN.sub(" ", sanitized)
    sanitized = re.sub(r"[ \t]{2,}", " ", sanitized)
    sanitized = re.sub(r"\n[ \t]+", "\n", sanitized)
    return sanitized


def mask_personal_text(text: str) -> str:
    masked = text or ""
    masked = EMAIL_PATTERN.sub(_mask_email, masked)
    masked = PHONE_PATTERN.sub(_mask_phone, masked)
    masked = NAME_LABEL_PATTERN.sub(r"\1***", masked)
    return masked


def mask_personal_items(items: Iterable[str]) -> list[str]:
    return [mask_personal_text(item) for item in items if item]


def describe_resume_source(source_name: str) -> str:
    normalized = normalize_text(source_name)
    if not normalized:
        return ""
    lowered = normalized.lower()
    if normalized == "手動貼上的履歷文字":
        return normalized
    if lowered.endswith(".pdf"):
        return "已上傳 PDF 履歷"
    if lowered.endswith(".docx"):
        return "已上傳 DOCX 履歷"
    if lowered.endswith(".txt"):
        return "已上傳 TXT 履歷"
    if lowered.endswith(".md"):
        return "已上傳 MD 履歷"
    return "已上傳履歷檔"


def _clean_resume_lines(text: str) -> list[str]:
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = normalize_text(_sanitize_extracted_text(raw_line))
        if len(line) < 4:
            continue
        if line.startswith(("http://", "https://")):
            continue
        cleaned_lines.append(line)
    return cleaned_lines


def _contains_personal_info(text: str) -> bool:
    return any(
        pattern.search(text)
        for pattern in (
            EMAIL_PATTERN,
            PHONE_PATTERN,
            URL_PATTERN,
            ADDRESS_PATTERN,
            LICENSE_PATTERN,
            PROFILE_META_PATTERN,
        )
    )


def _looks_garbled(text: str) -> bool:
    if GARBLED_CHAR_PATTERN.search(text):
        return True
    strange_chars = sum(
        1
        for char in text
        if not (
            char.isalnum()
            or "\u4e00" <= char <= "\u9fff"
            or char in " /-+&.,:;()[]{}%#@_"
        )
    )
    return strange_chars / max(len(text), 1) > 0.18


def _is_excluded_domain_token(token: str) -> bool:
    token_lower = token.lower()
    if EMAIL_PATTERN.search(token) or PHONE_PATTERN.search(token):
        return True
    if URL_PATTERN.search(token) or LICENSE_PATTERN.search(token):
        return True
    if ACTION_PREFIX_PATTERN.search(token):
        return True
    if TAIWAN_LOCATION_PATTERN.fullmatch(token):
        return True
    if token_lower.endswith((".com", ".tw", ".net")):
        return True
    if any(part.isdigit() for part in token):
        return True
    if token_lower in {"gmail", "yahoo", "hotmail", "outlook", "city", "road"}:
        return True
    return False


def _sanitize_domain_keywords(items: Iterable[str]) -> list[str]:
    sanitized: list[str] = []
    for item in items:
        candidate = normalize_text(_sanitize_extracted_text(item)).strip("、,;:/")
        if not candidate:
            continue
        if not _is_safe_domain_keyword(candidate):
            continue
        sanitized.append(candidate)
    return unique_preserving_order(sanitized)


def _sanitize_match_keywords(items: Iterable[str]) -> list[str]:
    sanitized: list[str] = []
    for item in items:
        candidate = normalize_text(_sanitize_extracted_text(item)).strip("、,;:/")
        if not candidate:
            continue
        if _contains_personal_info(candidate) or _looks_garbled(candidate):
            continue
        if _is_excluded_domain_token(candidate):
            continue
        sanitized.append(candidate)
    return unique_preserving_order(sanitized)


def _is_safe_domain_keyword(candidate: str) -> bool:
    if not candidate:
        return False
    if _contains_personal_info(candidate) or _looks_garbled(candidate):
        return False
    if _is_excluded_domain_token(candidate):
        return False
    if ADDRESS_FRAGMENT_PATTERN.search(candidate):
        return False
    if LICENSE_FRAGMENT_PATTERN.search(candidate):
        return False

    if candidate in DOMAIN_TAXONOMY:
        return True

    if re.fullmatch(r"[A-Za-z]{1,4}", candidate):
        return candidate.upper() in SAFE_DOMAIN_ACRONYMS

    if re.fullmatch(r"[\u4e00-\u9fff]{2,}", candidate):
        return candidate in SAFE_SHORT_DOMAIN_TERMS or len(candidate) >= 3

    if re.fullmatch(r"[A-Za-z][A-Za-z0-9+/# .-]{3,}", candidate):
        return True

    if re.search(r"[\u4e00-\u9fff]", candidate):
        return len(re.sub(r"[^\u4e00-\u9fff]", "", candidate)) >= 3

    return False


def _mask_email(match: re.Match[str]) -> str:
    value = match.group(0)
    local, _, domain = value.partition("@")
    local_masked = (local[:1] + "***") if local else "***"
    domain_name, dot, suffix = domain.partition(".")
    domain_masked = (domain_name[:1] + "***") if domain_name else "***"
    suffix_masked = dot + suffix if dot and suffix else ""
    return f"{local_masked}@{domain_masked}{suffix_masked}"


def _mask_phone(match: re.Match[str]) -> str:
    digits = [char for char in match.group(0) if char.isdigit()]
    if len(digits) < 6:
        return "***"
    return f"{''.join(digits[:2])}****{''.join(digits[-2:])}"


def _extract_pdf_text(raw_bytes: bytes) -> tuple[str, str]:
    try:
        from pypdf import PdfReader
    except Exception:  # noqa: BLE001
        return "", "目前環境尚未安裝 pypdf，所以 PDF 檔無法抽字。請先安裝相依套件，或暫時改貼上履歷文字。"

    reader = PdfReader(BytesIO(raw_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if not normalize_text(text):
        return "", "PDF 已讀取，但沒有擷取到可分析文字。這通常代表 PDF 是掃描影像檔，還需要 OCR 才能分析。"
    return text, ""


def _extract_docx_text(raw_bytes: bytes) -> tuple[str, str]:
    try:
        from docx import Document
    except Exception:  # noqa: BLE001
        return "", "目前環境尚未安裝 python-docx，DOCX 需先貼上文字或安裝相依套件。"

    document = Document(BytesIO(raw_bytes))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    if not normalize_text(text):
        return "", "DOCX 已讀取，但沒有擷取到可分析文字。"
    return text, ""

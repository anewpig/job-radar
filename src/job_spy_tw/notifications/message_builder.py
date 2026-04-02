from __future__ import annotations

from ..settings import Settings


def resolve_recipient_emails(settings: Settings, recipients_text: str = "") -> list[str]:
    raw = recipients_text.strip() or settings.notification_email_to
    return [
        item.strip()
        for item in raw.replace("\n", ",").replace(";", ",").split(",")
        if item.strip()
    ]


def resolve_line_target(settings: Settings, line_target: str = "") -> str:
    return line_target.strip() or settings.line_to.strip()


def is_valid_line_target(settings: Settings, line_target: str = "") -> bool:
    target = resolve_line_target(settings, line_target)
    return len(target) >= 10 and target[:1] in {"U", "C", "R"}


def build_alert_message(search_name: str, new_jobs: list[dict]) -> str:
    lines = [f"【職缺雷達】搜尋「{search_name}」有 {len(new_jobs)} 筆新職缺。", ""]
    for job in new_jobs[:8]:
        lines.append(
            f"- {job.get('title', '')}｜{job.get('company', '')}｜"
            f"{job.get('source', '')}｜{job.get('location', '') or '地點未提供'}"
        )
        if job.get("salary"):
            lines.append(f"  薪資：{job['salary']}")
        if job.get("url"):
            lines.append(f"  {job['url']}")
    if len(new_jobs) > 8:
        lines.append(f"... 另有 {len(new_jobs) - 8} 筆新職缺可到追蹤中心查看。")
    return "\n".join(lines)[:4500]

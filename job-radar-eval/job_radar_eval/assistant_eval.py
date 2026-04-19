"""AI 助理 baseline 評估。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from time import perf_counter
from typing import Any, Callable

from .fake_clients import FakeOpenAIClient
from .fixtures import build_market_snapshot_fixture, build_resume_profile_fixture, load_assistant_questions
from .metrics import average, keyword_recall, p95, precision_recall_f1


@dataclass(slots=True)
class AssistantCaseResult:
    """單一測題的聚合結果。"""

    case_id: str
    question: str
    answer_mode: str
    iterations: int
    build_chunks_ms_mean: float
    retrieve_ms_mean: float
    llm_ms_mean: float
    total_ms_mean: float
    total_ms_p95: float
    keyword_precision_mean: float
    keyword_recall_mean: float
    keyword_f1_mean: float
    source_type_precision_mean: float
    source_type_recall_mean: float
    source_type_f1_mean: float
    citation_min_count_accuracy: float
    citation_ok_rate: float
    structured_output_rate: float
    top_citation_type_hit_rate: float
    citation_keyword_recall_mean: float
    evidence_sufficiency_rate: float
    used_chunks_mean: float
    latest_answer: str


def _strip_code_fence(text: str) -> str:
    stripped = str(text or "").strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _normalize_list_field(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    splitter = "|" if "|" in text else "\n"
    return [item.strip(" -") for item in text.split(splitter) if item.strip(" -")]


def _parse_structured_answer(answer_text: str) -> dict[str, Any] | None:
    cleaned = _strip_code_fence(answer_text)
    if not cleaned:
        return None
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        normalized = {
            "summary": str(payload.get("summary", "")).strip(),
            "key_points": _normalize_list_field(payload.get("key_points")),
            "limitations": _normalize_list_field(payload.get("limitations")),
            "next_step": str(payload.get("next_step", "")).strip(),
        }
        if normalized["summary"] and normalized["key_points"] and normalized["next_step"]:
            return normalized

    summary_match = re.search(r"(?:^|\n)(?:結論|summary)[:：]?\s*(.+)", cleaned, flags=re.IGNORECASE)
    key_points_match = re.search(
        r"(?:^|\n)(?:重點|key_points?)[:：]?\s*(.+?)(?:\n(?:限制|limitations?)[:：]|\Z)",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    next_step_match = re.search(
        r"(?:^|\n)(?:下一步|next_step)[:：]?\s*(.+)",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    normalized = {
        "summary": summary_match.group(1).strip() if summary_match else "",
        "key_points": _normalize_list_field(key_points_match.group(1) if key_points_match else ""),
        "next_step": next_step_match.group(1).strip() if next_step_match else "",
    }
    if normalized["summary"] and normalized["key_points"] and normalized["next_step"]:
        return normalized
    return None


def _normalize_source_type(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return ""
    if normalized in {"job", "job-summary"}:
        return "job-summary"
    if normalized.startswith("job-skill"):
        return "job-skills"
    if normalized.startswith("job-work"):
        return "job-work-content"
    if normalized.startswith("market-skill-insight"):
        return "market-skill-insight"
    if normalized.startswith("market-skill"):
        return "market-skill"
    return normalized


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    kept: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value or "").strip()
        lowered = normalized.lower()
        if not normalized or lowered in seen:
            continue
        seen.add(lowered)
        kept.append(normalized)
    return kept


def _mentioned_keywords(text: str, vocabulary: list[str]) -> list[str]:
    lowered = str(text or "").lower()
    return _dedupe_preserve_order([keyword for keyword in vocabulary if keyword.lower() in lowered])


def _citation_text(label: str, text: str, source_type: str) -> str:
    return " ".join(part.strip() for part in (label, text, source_type) if str(part).strip())


class InstrumentedJobMarketRAGAssistant:
    """不改正式程式碼，直接在外部複刻流程並量測各階段耗時。"""

    def __init__(
        self,
        answer_model: str,
        embedding_model: str,
        cache_dir: Path | None = None,
        *,
        api_key: str,
        base_url: str = "",
        client: Any | None = None,
        embedding_api_key: str | None = None,
        embedding_base_url: str = "",
        embedding_client: Any | None = None,
    ) -> None:
        from job_spy_tw.assistant.service import JobMarketRAGAssistant
        from job_spy_tw.assistant.retrieval import EmbeddingRetriever

        self._assistant = JobMarketRAGAssistant(
            api_key=api_key,
            answer_model=answer_model,
            embedding_model=embedding_model,
            base_url=base_url,
            client=client,
            cache_dir=cache_dir,
        )
        if embedding_client is not None or embedding_base_url or embedding_api_key:
            try:
                from openai import OpenAI
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError("需要 openai 套件才能建立獨立 embedding client。") from exc
            if embedding_client is not None:
                embedding_client_instance = embedding_client
            else:
                client_kwargs = {"api_key": embedding_api_key or api_key}
                effective_base_url = embedding_base_url or base_url
                if effective_base_url:
                    client_kwargs["base_url"] = effective_base_url
                embedding_client_instance = OpenAI(**client_kwargs)
            self._assistant.retriever = EmbeddingRetriever(
                client=embedding_client_instance,
                embedding_model=embedding_model,
                cache_dir=self._assistant.embedding_cache_dir,
            )

    def answer_question(self, question, snapshot, resume_profile, top_k=8):
        timings = {}
        answer_mode = self._assistant.classify_answer_mode(
            question=question,
            resume_profile=resume_profile,
        )
        routed_top_k = 10 if answer_mode == "job_comparison" else 7 if answer_mode == "personalized_guidance" else top_k

        started = perf_counter()
        stage_started = perf_counter()
        chunks = self._assistant._build_chunks(snapshot=snapshot, resume_profile=resume_profile)
        timings["build_chunks_ms"] = (perf_counter() - stage_started) * 1000

        stage_started = perf_counter()
        retrieved = self._assistant._retrieve(question=question, chunks=chunks, top_k=routed_top_k)
        timings["retrieve_ms"] = (perf_counter() - stage_started) * 1000

        prompt = self._assistant._build_answer_prompt(
            question=question,
            snapshot=snapshot,
            resume_profile=resume_profile,
            conversation_context=None,
            answer_mode=answer_mode,
            chunks=retrieved,
        )

        stage_started = perf_counter()
        response = self._assistant.client.responses.create(
            model=self._assistant.answer_model,
            temperature=0.2,
            max_output_tokens=1200,
            input=f"問題：{question}\n\n{prompt}",
        )
        timings["llm_ms"] = (perf_counter() - stage_started) * 1000
        timings["total_ms"] = (perf_counter() - started) * 1000

        answer_text = getattr(response, "output_text", "").strip()
        citations = [chunk.label for chunk in retrieved[:5]]
        citation_source_types = [
            _normalize_source_type(getattr(chunk, "source_type", ""))
            for chunk in retrieved[:5]
        ]
        citation_text = "\n".join(
            _citation_text(
                getattr(chunk, "label", ""),
                getattr(chunk, "text", ""),
                _normalize_source_type(getattr(chunk, "source_type", "")),
            )
            for chunk in retrieved[:5]
        )
        return {
            "answer": answer_text,
            "citations": citations,
            "citation_source_types": _dedupe_preserve_order(citation_source_types),
            "citation_text": citation_text,
            "used_chunks": len(retrieved),
            "answer_mode": answer_mode,
            "top_citation_type": citation_source_types[0] if citation_source_types else "",
            "timings": timings,
        }


def evaluate_assistant(
    config,
    iterations: int,
    cache_dir: Path | None = None,
    *,
    case_limit: int | None = None,
    answer_model: str = "fake-answer",
    embedding_model: str = "fake-embedding",
    api_key: str = "fake",
    base_url: str = "",
    use_fake_client: bool = True,
    client: Any | None = None,
    embedding_api_key: str | None = None,
    embedding_base_url: str = "",
    embedding_client: Any | None = None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict:
    """執行 AI 助理 baseline 並回傳原始資料與聚合統計。"""
    snapshot = build_market_snapshot_fixture()
    resume_profile = build_resume_profile_fixture()
    questions = load_assistant_questions(config)
    if case_limit is not None:
        questions = questions[:case_limit]
    keyword_vocabulary = sorted(
        {
            str(keyword).strip()
            for case in questions
            for keyword in case.get("expected_keywords", [])
            if str(keyword).strip()
        },
        key=len,
        reverse=True,
    )
    assistant = InstrumentedJobMarketRAGAssistant(
        answer_model=answer_model,
        embedding_model=embedding_model,
        cache_dir=cache_dir or (config.results_dir / ".cache" / "assistant"),
        api_key=api_key,
        base_url=base_url,
        client=client if client is not None else (FakeOpenAIClient() if use_fake_client else None),
        embedding_api_key=embedding_api_key,
        embedding_base_url=embedding_base_url,
        embedding_client=embedding_client,
    )

    case_rows = []
    summaries: list[AssistantCaseResult] = []
    total_cases = len(questions)
    if progress_callback is not None:
        progress_callback(
            {
                "event": "stage_started",
                "total_cases": total_cases,
                "iterations": iterations,
                "answer_model": answer_model,
            }
        )

    for case_index, case in enumerate(questions, start=1):
        answer_mode = assistant._assistant.classify_answer_mode(
            question=case["question"],
            resume_profile=resume_profile,
        )
        if progress_callback is not None:
            progress_callback(
                {
                    "event": "case_started",
                    "case_index": case_index,
                    "total_cases": total_cases,
                    "case_id": case.get("id", ""),
                    "question": case.get("question", ""),
                    "answer_mode": answer_mode,
                }
            )
        expected_keywords = [str(item).strip() for item in case.get("expected_keywords", []) if str(item).strip()]
        expected_source_types = [
            _normalize_source_type(item)
            for item in case.get("expected_source_types", [])
            if str(item).strip()
        ]
        min_citations = int(case.get("min_citations", 0) or 0)
        build_chunks_values = []
        retrieve_values = []
        llm_values = []
        total_values = []
        keyword_precision_values = []
        keyword_recall_values = []
        keyword_f1_values = []
        source_type_precision_values = []
        source_type_recall_values = []
        source_type_f1_values = []
        citation_min_hits = []
        structured_hits = []
        top_type_hits = []
        citation_keyword_recalls = []
        evidence_hits = []
        used_chunks_values = []
        latest_answer = ""

        for iteration in range(iterations):
            result = assistant.answer_question(
                question=case["question"],
                snapshot=snapshot,
                resume_profile=resume_profile,
                top_k=8,
            )
            latest_answer = result["answer"]
            actual_keywords = _mentioned_keywords(result["answer"], keyword_vocabulary)
            keyword_precision, keyword_recall_value, keyword_f1 = precision_recall_f1(
                actual_keywords,
                expected_keywords,
            )
            source_type_precision, source_type_recall, source_type_f1 = precision_recall_f1(
                result["citation_source_types"],
                expected_source_types,
            )
            citation_min_ok = len(result["citations"]) >= min_citations
            structured_ok = _parse_structured_answer(result["answer"]) is not None
            top_citation_type_hit = bool(
                result["top_citation_type"]
                and result["top_citation_type"] in expected_source_types
            )
            citation_keyword_recall_value = (
                keyword_recall(result["citation_text"], expected_keywords)
                if expected_keywords
                else 1.0
            )
            citation_source_type_set = {
                _normalize_source_type(source_type)
                for source_type in result["citation_source_types"]
            }
            evidence_sufficient = bool(
                citation_min_ok
                and any(source_type in citation_source_type_set for source_type in expected_source_types)
                and citation_keyword_recall_value >= 1.0
            )
            timings = result["timings"]
            build_chunks_values.append(timings["build_chunks_ms"])
            retrieve_values.append(timings["retrieve_ms"])
            llm_values.append(timings["llm_ms"])
            total_values.append(timings["total_ms"])
            keyword_precision_values.append(keyword_precision)
            keyword_recall_values.append(keyword_recall_value)
            keyword_f1_values.append(keyword_f1)
            source_type_precision_values.append(source_type_precision)
            source_type_recall_values.append(source_type_recall)
            source_type_f1_values.append(source_type_f1)
            citation_min_hits.append(1.0 if citation_min_ok else 0.0)
            structured_hits.append(1.0 if structured_ok else 0.0)
            top_type_hits.append(1.0 if top_citation_type_hit else 0.0)
            citation_keyword_recalls.append(citation_keyword_recall_value)
            evidence_hits.append(1.0 if evidence_sufficient else 0.0)
            used_chunks_values.append(float(result["used_chunks"]))
            case_rows.append(
                {
                    "case_id": case["id"],
                    "answer_mode": answer_mode,
                    "iteration": iteration + 1,
                    "question": case["question"],
                    "build_chunks_ms": round(timings["build_chunks_ms"], 3),
                    "retrieve_ms": round(timings["retrieve_ms"], 3),
                    "llm_ms": round(timings["llm_ms"], 3),
                    "total_ms": round(timings["total_ms"], 3),
                    "keyword_precision": round(keyword_precision, 4),
                    "keyword_recall": round(keyword_recall_value, 4),
                    "keyword_f1": round(keyword_f1, 4),
                    "source_type_precision": round(source_type_precision, 4),
                    "source_type_recall": round(source_type_recall, 4),
                    "source_type_f1": round(source_type_f1, 4),
                    "citation_min_count_accuracy": citation_min_ok,
                    "citation_ok": citation_min_ok,
                    "structured_output": structured_ok,
                    "top_citation_type_hit": top_citation_type_hit,
                    "citation_keyword_recall": round(citation_keyword_recall_value, 4),
                    "evidence_sufficient": evidence_sufficient,
                    "used_chunks": result["used_chunks"],
                    "top_citation_type": result["top_citation_type"],
                    "citation_count": len(result["citations"]),
                    "citation_labels": result["citations"],
                    "citation_source_types": result["citation_source_types"],
                    "answer": result["answer"],
                }
            )

        summary = AssistantCaseResult(
                case_id=case["id"],
                question=case["question"],
                answer_mode=answer_mode,
                iterations=iterations,
                build_chunks_ms_mean=round(average(build_chunks_values), 3),
                retrieve_ms_mean=round(average(retrieve_values), 3),
                llm_ms_mean=round(average(llm_values), 3),
                total_ms_mean=round(average(total_values), 3),
                total_ms_p95=round(p95(total_values), 3),
                keyword_precision_mean=round(average(keyword_precision_values), 4),
                keyword_recall_mean=round(average(keyword_recall_values), 4),
                keyword_f1_mean=round(average(keyword_f1_values), 4),
                source_type_precision_mean=round(average(source_type_precision_values), 4),
                source_type_recall_mean=round(average(source_type_recall_values), 4),
                source_type_f1_mean=round(average(source_type_f1_values), 4),
                citation_min_count_accuracy=round(average(citation_min_hits), 4),
                citation_ok_rate=round(average(citation_min_hits), 4),
                structured_output_rate=round(average(structured_hits), 4),
                top_citation_type_hit_rate=round(average(top_type_hits), 4),
                citation_keyword_recall_mean=round(average(citation_keyword_recalls), 4),
                evidence_sufficiency_rate=round(average(evidence_hits), 4),
                used_chunks_mean=round(average(used_chunks_values), 3),
                latest_answer=latest_answer,
            )
        summaries.append(summary)
        if progress_callback is not None:
            progress_callback(
                {
                    "event": "case_finished",
                    "case_index": case_index,
                    "total_cases": total_cases,
                    "case_id": summary.case_id,
                    "answer_mode": summary.answer_mode,
                    "total_ms_mean": summary.total_ms_mean,
                    "keyword_f1_mean": summary.keyword_f1_mean,
                }
            )

    mode_breakdown: dict[str, dict[str, float | int]] = {}
    for answer_mode in sorted({item.answer_mode for item in summaries}):
        bucket = [item for item in summaries if item.answer_mode == answer_mode]
        mode_breakdown[answer_mode] = {
            "case_count": len(bucket),
            "build_chunks_ms_mean": round(average([item.build_chunks_ms_mean for item in bucket]), 3),
            "retrieve_ms_mean": round(average([item.retrieve_ms_mean for item in bucket]), 3),
            "llm_ms_mean": round(average([item.llm_ms_mean for item in bucket]), 3),
            "total_ms_mean": round(average([item.total_ms_mean for item in bucket]), 3),
            "total_ms_p95": round(p95([item.total_ms_p95 for item in bucket]), 3),
            "keyword_precision_mean": round(average([item.keyword_precision_mean for item in bucket]), 4),
            "keyword_recall_mean": round(average([item.keyword_recall_mean for item in bucket]), 4),
            "keyword_f1_mean": round(average([item.keyword_f1_mean for item in bucket]), 4),
            "source_type_precision_mean": round(average([item.source_type_precision_mean for item in bucket]), 4),
            "source_type_recall_mean": round(average([item.source_type_recall_mean for item in bucket]), 4),
            "source_type_f1_mean": round(average([item.source_type_f1_mean for item in bucket]), 4),
            "citation_min_count_accuracy": round(average([item.citation_min_count_accuracy for item in bucket]), 4),
            "citation_ok_rate": round(average([item.citation_ok_rate for item in bucket]), 4),
            "structured_output_rate": round(average([item.structured_output_rate for item in bucket]), 4),
            "top_citation_type_hit_rate": round(average([item.top_citation_type_hit_rate for item in bucket]), 4),
            "citation_keyword_recall_mean": round(average([item.citation_keyword_recall_mean for item in bucket]), 4),
            "evidence_sufficiency_rate": round(average([item.evidence_sufficiency_rate for item in bucket]), 4),
            "used_chunks_mean": round(average([item.used_chunks_mean for item in bucket]), 3),
        }

    payload = {
        "rows": case_rows,
        "summary": [asdict(item) for item in summaries],
        "aggregate": {
            "case_count": len(summaries),
            "build_chunks_ms_mean": round(average([item.build_chunks_ms_mean for item in summaries]), 3),
            "retrieve_ms_mean": round(average([item.retrieve_ms_mean for item in summaries]), 3),
            "llm_ms_mean": round(average([item.llm_ms_mean for item in summaries]), 3),
            "total_ms_mean": round(average([item.total_ms_mean for item in summaries]), 3),
            "total_ms_p95": round(p95([item.total_ms_p95 for item in summaries]), 3),
            "keyword_precision_mean": round(average([item.keyword_precision_mean for item in summaries]), 4),
            "keyword_recall_mean": round(average([item.keyword_recall_mean for item in summaries]), 4),
            "keyword_f1_mean": round(average([item.keyword_f1_mean for item in summaries]), 4),
            "source_type_precision_mean": round(average([item.source_type_precision_mean for item in summaries]), 4),
            "source_type_recall_mean": round(average([item.source_type_recall_mean for item in summaries]), 4),
            "source_type_f1_mean": round(average([item.source_type_f1_mean for item in summaries]), 4),
            "citation_min_count_accuracy": round(average([item.citation_min_count_accuracy for item in summaries]), 4),
            "citation_ok_rate": round(average([item.citation_ok_rate for item in summaries]), 4),
            "structured_output_rate": round(average([item.structured_output_rate for item in summaries]), 4),
            "top_citation_type_hit_rate": round(average([item.top_citation_type_hit_rate for item in summaries]), 4),
            "citation_keyword_recall_mean": round(average([item.citation_keyword_recall_mean for item in summaries]), 4),
            "evidence_sufficiency_rate": round(average([item.evidence_sufficiency_rate for item in summaries]), 4),
            "used_chunks_mean": round(average([item.used_chunks_mean for item in summaries]), 3),
        },
        "mode_breakdown": mode_breakdown,
    }
    if progress_callback is not None:
        progress_callback(
            {
                "event": "stage_finished",
                "total_cases": total_cases,
                "aggregate": payload["aggregate"],
            }
        )
    return payload

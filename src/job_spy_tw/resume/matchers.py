from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..analysis import JobAnalyzer
from ..models import JobListing, ResumeJobMatch, ResumeProfile, TargetRole
from ..utils import chunked, ensure_directory, normalize_text, unique_preserving_order
from .scoring import (
    EXACT_SKILL_WEIGHT,
    EXACT_TASK_WEIGHT,
    KEYWORD_WEIGHT,
    MARKET_FIT_TOTAL,
    ROLE_WEIGHT,
    SEMANTIC_TOTAL,
    SKILL_SEMANTIC_WEIGHT,
    TASK_SEMANTIC_WEIGHT,
    _build_fit_summary,
    _cosine_similarity,
    _dice_coefficient,
    _normalize_score,
    _prepare_embedding_text,
    _saturating_hit_ratio,
    _stable_hash,
)
from .schemas import OpenAI, TitleSimilarityBatch


class OpenAIResumeMatcher:
    def __init__(
        self,
        role_targets: list[TargetRole],
        fallback_matcher: ResumeMatcher,
        api_key: str,
        title_model: str,
        embedding_model: str,
        base_url: str = "",
        cache_dir: Path | None = None,
        client: Any | None = None,
    ) -> None:
        if OpenAI is None or TitleSimilarityBatch is None:
            raise RuntimeError("OpenAI 或 Pydantic 套件不可用，無法啟用 AI 匹配。")
        if client is None and not api_key:
            raise RuntimeError("沒有提供 OPENAI_API_KEY。")

        if client is not None:
            self.client = client
        else:
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = OpenAI(**client_kwargs)

        self.role_targets = role_targets
        self.fallback_matcher = fallback_matcher
        self.title_model = title_model
        self.embedding_model = embedding_model
        self.cache_dir = ensure_directory(cache_dir) if cache_dir else None
        self.embedding_cache_dir = (
            ensure_directory(self.cache_dir / "resume_match_embeddings")
            if self.cache_dir
            else None
        )
        self.title_cache_dir = (
            ensure_directory(self.cache_dir / "resume_match_titles")
            if self.cache_dir
            else None
        )

    def match_jobs(
        self,
        profile: ResumeProfile,
        jobs: list[JobListing],
    ) -> list[ResumeJobMatch]:
        if not jobs:
            return []

        title_scores = self._score_titles(profile, jobs)
        semantic_scores = self._score_semantics(profile, jobs)
        resume_skills = set(profile.core_skills + profile.tool_skills)
        resume_tasks = set(profile.preferred_tasks)
        resume_keywords = unique_preserving_order(
            profile.match_keywords + profile.domain_keywords + profile.target_roles
        )[:20]

        matches: list[ResumeJobMatch] = []
        for index, job in enumerate(jobs):
            job_skill_set = self.fallback_matcher._job_skills(job)
            job_task_set = self.fallback_matcher._job_tasks(job)
            matched_skills = sorted(resume_skills & job_skill_set)
            matched_tasks = sorted(resume_tasks & job_task_set)
            matched_keywords = self.fallback_matcher._matched_keywords(job, resume_keywords)
            missing_skills = sorted(job_skill_set - resume_skills)
            missing_tasks = sorted(job_task_set - resume_tasks)
            missing_keywords = [
                keyword
                for keyword in self.fallback_matcher._job_keywords(job)
                if keyword not in resume_keywords
            ]

            title_similarity = title_scores.get(index, {}).get(
                "similarity", self.fallback_matcher._role_similarity(profile, job)
            )
            title_reason = title_scores.get(index, {}).get("reason", "")

            skill_similarity = semantic_scores["skill"][index]
            task_similarity = semantic_scores["task"][index]
            keyword_similarity = semantic_scores["keyword"][index]
            semantic_similarity = (
                (skill_similarity * SKILL_SEMANTIC_WEIGHT)
                + (task_similarity * TASK_SEMANTIC_WEIGHT)
                + (keyword_similarity * KEYWORD_WEIGHT)
            ) / SEMANTIC_TOTAL

            role_score = round(ROLE_WEIGHT * title_similarity, 2)
            skill_score = round(SKILL_SEMANTIC_WEIGHT * skill_similarity, 2)
            task_score = round(TASK_SEMANTIC_WEIGHT * task_similarity, 2)
            keyword_score = round(KEYWORD_WEIGHT * keyword_similarity, 2)
            exact_skill_score = round(
                EXACT_SKILL_WEIGHT * _saturating_hit_ratio(len(matched_skills), saturation=3),
                2,
            )
            exact_task_score = round(
                EXACT_TASK_WEIGHT * _saturating_hit_ratio(len(matched_tasks), saturation=2),
                2,
            )
            exact_match_score = round(exact_skill_score + exact_task_score, 2)
            market_base_score = role_score + skill_score + task_score + keyword_score
            market_fit_score = round(_normalize_score(market_base_score, MARKET_FIT_TOTAL), 2)
            overall_score = round(market_base_score + exact_match_score, 2)

            reasons: list[str] = []
            if title_reason:
                reasons.append(f"職稱相近：{title_reason}")
            elif title_similarity >= 0.55:
                reasons.append(f"職稱相近度：{round(title_similarity * 100)}%")
            if matched_skills:
                reasons.append(f"精確技能命中：{'、'.join(matched_skills[:5])}")
            elif skill_similarity >= 0.65:
                reasons.append(f"技能語意相似：{round(skill_similarity * 100)}%")
            if matched_tasks:
                reasons.append(f"精確工作內容命中：{'、'.join(matched_tasks[:4])}")
            elif task_similarity >= 0.65:
                reasons.append(f"工作內容語意相似：{round(task_similarity * 100)}%")
            if matched_keywords:
                reasons.append(f"關鍵字 / 領域命中：{'、'.join(matched_keywords[:4])}")
            fit_summary = _build_fit_summary(
                title_reason=title_reason,
                matched_skills=matched_skills,
                matched_tasks=matched_tasks,
                missing_skills=missing_skills,
                missing_tasks=missing_tasks,
            )

            matches.append(
                ResumeJobMatch(
                    job_url=job.url,
                    title=job.title,
                    company=job.company,
                    source=job.source,
                    matched_role=job.matched_role,
                    overall_score=overall_score,
                    role_score=role_score,
                    skill_score=skill_score,
                    task_score=task_score,
                    keyword_score=keyword_score,
                    market_fit_score=market_fit_score,
                    exact_match_score=exact_match_score,
                    exact_skill_score=exact_skill_score,
                    exact_task_score=exact_task_score,
                    title_similarity=round(title_similarity * 100, 2),
                    semantic_similarity=round(semantic_similarity * 100, 2),
                    title_reason=title_reason,
                    scoring_method="llm_embedding",
                    matched_skills=matched_skills,
                    matched_tasks=matched_tasks,
                    matched_keywords=matched_keywords,
                    missing_skills=missing_skills[:6],
                    missing_tasks=missing_tasks[:4],
                    missing_keywords=missing_keywords[:5],
                    fit_summary=fit_summary,
                    reasons=reasons[:3],
                )
            )

        matches.sort(key=lambda item: item.overall_score, reverse=True)
        return matches

    def _score_titles(
        self,
        profile: ResumeProfile,
        jobs: list[JobListing],
    ) -> dict[int, dict[str, Any]]:
        if not profile.target_roles:
            return {}

        results: dict[int, dict[str, Any]] = {}
        for batch in chunked(list(enumerate(jobs)), 20):
            payload = {
                "roles": profile.target_roles,
                "jobs": [
                    {
                        "job_index": index,
                        "title": job.title,
                        "matched_role": job.matched_role,
                    }
                    for index, job in batch
                ],
            }
            cache_key = _stable_hash({"model": self.title_model, **payload})
            cached = self._read_cache(self.title_cache_dir, cache_key)
            if cached is None:
                response = self.client.responses.parse(
                    model=self.title_model,
                    temperature=0,
                    max_output_tokens=1200,
                    input=(
                        "你是求職職稱比對器。請只根據候選人的目標角色與職缺職稱相近度評分。\n"
                        "similarity 請輸出 0 到 1 之間的小數：\n"
                        "1.0 = 幾乎同職稱；0.8 = 很接近；0.5 = 有關聯但不同；0.2 = 差異很大；0 = 無關。\n"
                        "reason 請用 18 字內繁中短句。\n"
                        f"候選人目標角色：{', '.join(profile.target_roles)}\n"
                        f"履歷摘要：{profile.summary[:240]}\n"
                        "職缺列表：\n"
                        + "\n".join(
                            (
                                f"- job_index={index}; "
                                f"title={job.title}; matched_role={job.matched_role}"
                            )
                            for index, job in batch
                        )
                    ),
                    text_format=TitleSimilarityBatch,
                )
                parsed = response.output_parsed
                if parsed is None:
                    raise RuntimeError("LLM 沒有回傳職稱相近度結果。")
                cached = {
                    "scores": [
                        {
                            "job_index": item.job_index,
                            "similarity": max(0.0, min(1.0, float(item.similarity))),
                            "reason": normalize_text(item.reason),
                        }
                        for item in parsed.scores
                    ]
                }
                self._write_cache(self.title_cache_dir, cache_key, cached)

            for item in cached.get("scores", []):
                results[int(item["job_index"])] = {
                    "similarity": max(0.0, min(1.0, float(item["similarity"]))),
                    "reason": normalize_text(str(item.get("reason", ""))),
                }
        return results

    def _score_semantics(
        self,
        profile: ResumeProfile,
        jobs: list[JobListing],
    ) -> dict[str, list[float]]:
        profile_skill_text = _prepare_embedding_text(
            "\n".join(profile.core_skills + profile.tool_skills + profile.target_roles)
        )
        profile_task_text = _prepare_embedding_text(
            "\n".join(profile.preferred_tasks + profile.generated_prompts)
        )
        profile_keyword_text = _prepare_embedding_text(
            "\n".join([profile.summary] + profile.match_keywords + profile.domain_keywords)
        )

        job_skill_texts = [
            _prepare_embedding_text(
                "\n".join(
                    [job.requirement_text(), " ".join(job.extracted_skills), job.title]
                )
            )
            for job in jobs
        ]
        job_task_texts = [
            _prepare_embedding_text("\n".join(job.work_content_items + [job.summary]))
            for job in jobs
        ]
        job_keyword_texts = [
            _prepare_embedding_text(job.combined_text())
            for job in jobs
        ]

        all_texts = unique_preserving_order(
            [
                profile_skill_text,
                profile_task_text,
                profile_keyword_text,
                *job_skill_texts,
                *job_task_texts,
                *job_keyword_texts,
            ]
        )
        embeddings = self._embed_texts([text for text in all_texts if text])

        def cosine(left: str, right: str) -> float:
            if not left or not right:
                return 0.0
            return _cosine_similarity(embeddings.get(left, []), embeddings.get(right, []))

        return {
            "skill": [cosine(profile_skill_text, text) for text in job_skill_texts],
            "task": [cosine(profile_task_text, text) for text in job_task_texts],
            "keyword": [cosine(profile_keyword_text, text) for text in job_keyword_texts],
        }

    def _embed_texts(self, texts: list[str]) -> dict[str, list[float]]:
        vectors: dict[str, list[float]] = {}
        missing: list[str] = []

        for text in texts:
            cache_key = _stable_hash({"model": self.embedding_model, "text": text})
            cached = self._read_cache(self.embedding_cache_dir, cache_key)
            if cached is not None:
                vectors[text] = [float(value) for value in cached.get("embedding", [])]
            else:
                missing.append(text)

        if missing:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=missing,
            )
            for text, item in zip(missing, response.data):
                embedding = [float(value) for value in item.embedding]
                vectors[text] = embedding
                cache_key = _stable_hash({"model": self.embedding_model, "text": text})
                self._write_cache(
                    self.embedding_cache_dir,
                    cache_key,
                    {"embedding": embedding},
                )

        return vectors

    def _read_cache(self, directory: Path | None, key: str) -> dict[str, Any] | None:
        if directory is None:
            return None
        path = directory / f"{key}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_cache(self, directory: Path | None, key: str, payload: dict[str, Any]) -> None:
        if directory is None:
            return
        path = directory / f"{key}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class ResumeMatcher:
    def __init__(self, role_targets: list[TargetRole]) -> None:
        self.role_targets = role_targets
        self.analyzer = JobAnalyzer(role_targets)
        self.compiled_tasks = self.analyzer._compiled_tasks

    def match_jobs(
        self,
        profile: ResumeProfile,
        jobs: list[JobListing],
    ) -> list[ResumeJobMatch]:
        matches: list[ResumeJobMatch] = []
        resume_skills = set(profile.core_skills + profile.tool_skills)
        resume_tasks = set(profile.preferred_tasks)
        resume_keywords = unique_preserving_order(
            profile.match_keywords + profile.domain_keywords + profile.target_roles
        )[:20]

        for job in jobs:
            job_skill_set = self._job_skills(job)
            job_task_set = self._job_tasks(job)
            matched_skills = sorted(resume_skills & job_skill_set)
            matched_tasks = sorted(resume_tasks & job_task_set)
            matched_keywords = self._matched_keywords(job, resume_keywords)
            missing_skills = sorted(job_skill_set - resume_skills)
            missing_tasks = sorted(job_task_set - resume_tasks)
            missing_keywords = [
                keyword for keyword in self._job_keywords(job) if keyword not in resume_keywords
            ]

            role_score = self._role_score(profile, job)
            skill_score = SKILL_SEMANTIC_WEIGHT * _dice_coefficient(resume_skills, job_skill_set)
            task_score = TASK_SEMANTIC_WEIGHT * _dice_coefficient(resume_tasks, job_task_set)
            keyword_score = min(
                KEYWORD_WEIGHT,
                KEYWORD_WEIGHT
                * (len(matched_keywords) / max(4, len(resume_keywords) or 1))
                * 2.2,
            )
            exact_skill_score = EXACT_SKILL_WEIGHT * _saturating_hit_ratio(
                len(matched_skills), saturation=3
            )
            exact_task_score = EXACT_TASK_WEIGHT * _saturating_hit_ratio(
                len(matched_tasks), saturation=2
            )
            exact_match_score = exact_skill_score + exact_task_score
            market_base_score = role_score + skill_score + task_score + keyword_score
            market_fit_score = _normalize_score(market_base_score, MARKET_FIT_TOTAL)
            overall_score = round(market_base_score + exact_match_score, 2)

            reasons: list[str] = []
            role_similarity = self._role_similarity(profile, job)
            if role_similarity >= 0.75:
                reasons.append(f"職稱相近：{job.matched_role or job.title}")
            if matched_skills:
                reasons.append(f"精確技能命中：{'、'.join(matched_skills[:5])}")
            if matched_tasks:
                reasons.append(f"精確工作內容命中：{'、'.join(matched_tasks[:4])}")
            if matched_keywords:
                reasons.append(f"關鍵字 / 領域命中：{'、'.join(matched_keywords[:4])}")
            fit_summary = _build_fit_summary(
                title_reason="",
                matched_skills=matched_skills,
                matched_tasks=matched_tasks,
                missing_skills=missing_skills,
                missing_tasks=missing_tasks,
            )

            matches.append(
                ResumeJobMatch(
                    job_url=job.url,
                    title=job.title,
                    company=job.company,
                    source=job.source,
                    matched_role=job.matched_role,
                    overall_score=overall_score,
                    role_score=round(role_score, 2),
                    skill_score=round(skill_score, 2),
                    task_score=round(task_score, 2),
                    keyword_score=round(keyword_score, 2),
                    market_fit_score=round(market_fit_score, 2),
                    exact_match_score=round(exact_match_score, 2),
                    exact_skill_score=round(exact_skill_score, 2),
                    exact_task_score=round(exact_task_score, 2),
                    title_similarity=round(role_similarity * 100, 2),
                    semantic_similarity=round(
                        _normalize_score(skill_score + task_score + keyword_score, SEMANTIC_TOTAL),
                        2,
                    ),
                    matched_skills=matched_skills,
                    matched_tasks=matched_tasks,
                    matched_keywords=matched_keywords,
                    missing_skills=missing_skills[:6],
                    missing_tasks=missing_tasks[:4],
                    missing_keywords=missing_keywords[:5],
                    fit_summary=fit_summary,
                    reasons=reasons[:3],
                )
            )

        matches.sort(key=lambda item: item.overall_score, reverse=True)
        return matches

    def _role_similarity(self, profile: ResumeProfile, job: JobListing) -> float:
        if not profile.target_roles:
            return 0.0
        title_lower = normalize_text(job.title).lower()
        matched_role_lower = normalize_text(job.matched_role).lower()

        best = 0.0
        for role in profile.target_roles:
            role_lower = normalize_text(role).lower()
            if role_lower == matched_role_lower:
                best = max(best, 1.0)
            elif role_lower and (role_lower in title_lower or title_lower in role_lower):
                best = max(best, 0.78)
            elif matched_role_lower and (
                role_lower in matched_role_lower or matched_role_lower in role_lower
            ):
                best = max(best, 0.72)
        return best

    def _role_score(self, profile: ResumeProfile, job: JobListing) -> float:
        return ROLE_WEIGHT * self._role_similarity(profile, job)

    def _job_skills(self, job: JobListing) -> set[str]:
        skills = list(job.extracted_skills)
        requirement_skills = self.analyzer.extract_skills(
            job.requirement_text() or job.combined_text()
        )
        if not skills:
            skills = requirement_skills
        else:
            skills = unique_preserving_order(skills + requirement_skills)
        return set(skills)

    def _job_tasks(self, job: JobListing) -> set[str]:
        matched: list[str] = []
        for item in job.work_content_items:
            lowered = f" {normalize_text(item).lower()} "
            found = False
            for task, patterns in self.compiled_tasks.items():
                if any(pattern.search(lowered) for pattern in patterns):
                    matched.append(task)
                    found = True
            if not found and len(item) <= 36:
                matched.append(item)
        return set(unique_preserving_order(matched))

    def _matched_keywords(self, job: JobListing, keywords: list[str]) -> list[str]:
        job_text = normalize_text(job.combined_text()).lower()
        matched: list[str] = []
        for keyword in keywords:
            lowered = normalize_text(keyword).lower()
            if lowered and lowered in job_text:
                matched.append(keyword)
        return unique_preserving_order(matched)[:8]

    def _job_keywords(self, job: JobListing) -> list[str]:
        candidates = (
            list(job.extracted_skills)
            + list(job.required_skill_items)
            + list(job.work_content_items)
            + [job.matched_role, job.title]
        )
        cleaned = [normalize_text(item) for item in candidates if normalize_text(item)]
        return unique_preserving_order(cleaned)[:18]

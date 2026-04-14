"""Resume-analysis helpers for matchers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..analysis import JobAnalyzer
from ..models import JobListing, ResumeJobMatch, ResumeProfile, TargetRole
from ..openai_usage import extract_openai_usage, merge_openai_usage
from ..prompt_versions import TITLE_SIMILARITY_PROMPT_VERSION
from ..utils import chunked, ensure_directory, normalize_text, unique_preserving_order
from .scoring import (
    EXACT_SKILL_WEIGHT,
    EXACT_TASK_WEIGHT,
    EXACT_TITLE_WEIGHT,
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
    _stabilize_title_similarity,
    _title_exact_match_bonus,
)
from .schemas import OpenAI, TitleSimilarityBatch

LLM_CANDIDATE_MIN = 5
LLM_CANDIDATE_MAX = 8
LLM_CANDIDATE_RATIO = 0.3
TITLE_LLM_MAX = 4
SEMANTIC_EMBED_MAX = 6
TITLE_LLM_SKIP_ROLE_SIMILARITY = 0.82
LLM_SCORE_FLOOR_RATIO = 0.68
LLM_SCORE_FLOOR_DELTA = 18.0
RESUME_MATCH_MEMORY_CACHE_MAX = 1024


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
        self.llm_candidate_limit = LLM_CANDIDATE_MAX
        self.last_usage = merge_openai_usage()
        self.last_metrics: dict[str, Any] = {}
        self._embedding_memory_cache: dict[str, list[float]] = {}
        self._title_memory_cache: dict[str, dict[str, Any]] = {}

    def match_jobs(
        self,
        profile: ResumeProfile,
        jobs: list[JobListing],
    ) -> list[ResumeJobMatch]:
        self.last_usage = merge_openai_usage()
        self.last_metrics = {
            "title_prompt_version": TITLE_SIMILARITY_PROMPT_VERSION,
            "llm_candidate_limit": self.llm_candidate_limit,
            "candidate_jobs": 0,
            "title_llm_jobs": 0,
            "semantic_jobs": 0,
            "embedding_memory_hits": 0,
            "embedding_disk_hits": 0,
            "embedding_remote_texts": 0,
            "title_cache_memory_hits": 0,
            "title_cache_disk_hits": 0,
            "title_llm_requests": 0,
        }
        if not jobs:
            return []

        fallback_matches = self.fallback_matcher.match_jobs(profile, jobs)
        candidate_jobs = self._select_candidate_jobs(profile, jobs, fallback_matches)
        if len(candidate_jobs) == len(jobs):
            candidate_jobs = jobs
        self.last_metrics["candidate_jobs"] = len(candidate_jobs)

        fallback_match_by_url = {
            match.job_url: match
            for match in fallback_matches
        }
        indexed_candidate_jobs = list(enumerate(candidate_jobs))
        title_candidate_jobs = [
            (index, job)
            for index, job in indexed_candidate_jobs[:TITLE_LLM_MAX]
            if not self._should_skip_title_llm(
                profile,
                job,
                fallback_match_by_url.get(job.url),
            )
        ]
        semantic_candidate_jobs = indexed_candidate_jobs[:SEMANTIC_EMBED_MAX]
        self.last_metrics["title_llm_jobs"] = len(title_candidate_jobs)
        self.last_metrics["semantic_jobs"] = len(semantic_candidate_jobs)

        title_scores = self._score_titles(profile, title_candidate_jobs)
        semantic_scores = self._score_semantics(profile, semantic_candidate_jobs)
        resume_skills = set(profile.core_skills + profile.tool_skills)
        resume_tasks = set(profile.preferred_tasks)
        resume_keywords = unique_preserving_order(
            profile.match_keywords + profile.domain_keywords + profile.target_roles
        )[:20]

        llm_matches: list[ResumeJobMatch] = []
        for index, job in enumerate(candidate_jobs):
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

            fallback_role_similarity = self.fallback_matcher._role_similarity(profile, job)
            raw_title_similarity = title_scores.get(index, {}).get(
                "similarity", fallback_role_similarity
            )
            title_similarity = _stabilize_title_similarity(
                raw_title_similarity, fallback_role_similarity
            )
            title_reason = title_scores.get(index, {}).get("reason", "")

            skill_similarity = max(
                semantic_scores["skill"].get(index, 0.0),
                _dice_coefficient(resume_skills, job_skill_set),
            )
            task_similarity = max(
                semantic_scores["task"].get(index, 0.0),
                _dice_coefficient(resume_tasks, job_task_set),
            )
            keyword_similarity = max(
                semantic_scores["keyword"].get(index, 0.0),
                _saturating_hit_ratio(len(matched_keywords), saturation=4),
            )
            semantic_similarity = (
                (skill_similarity * SKILL_SEMANTIC_WEIGHT)
                + (task_similarity * TASK_SEMANTIC_WEIGHT)
                + (keyword_similarity * KEYWORD_WEIGHT)
            ) / SEMANTIC_TOTAL

            role_score = round(ROLE_WEIGHT * title_similarity, 2)
            skill_score = round(SKILL_SEMANTIC_WEIGHT * skill_similarity, 2)
            task_score = round(TASK_SEMANTIC_WEIGHT * task_similarity, 2)
            keyword_score = round(KEYWORD_WEIGHT * keyword_similarity, 2)
            exact_title_score = round(
                _title_exact_match_bonus(profile.target_roles, job.title),
                2,
            )
            exact_skill_score = round(
                EXACT_SKILL_WEIGHT * _saturating_hit_ratio(len(matched_skills), saturation=3),
                2,
            )
            exact_task_score = round(
                EXACT_TASK_WEIGHT * _saturating_hit_ratio(len(matched_tasks), saturation=2),
                2,
            )
            exact_match_score = round(
                exact_title_score + exact_skill_score + exact_task_score,
                2,
            )
            market_base_score = role_score + skill_score + task_score + keyword_score
            market_fit_score = round(_normalize_score(market_base_score, MARKET_FIT_TOTAL), 2)
            overall_score = round(market_base_score + exact_match_score, 2)

            reasons: list[str] = []
            if exact_title_score >= EXACT_TITLE_WEIGHT:
                reasons.append("精確職稱命中")
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

            llm_matches.append(
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

        llm_match_by_url = {match.job_url: match for match in llm_matches}
        merged_matches = [
            llm_match_by_url.get(match.job_url, match)
            for match in fallback_matches
        ]
        merged_matches.sort(key=lambda item: item.overall_score, reverse=True)
        return merged_matches

    def _select_candidate_jobs(
        self,
        profile: ResumeProfile,
        jobs: list[JobListing],
        fallback_matches: list[ResumeJobMatch],
    ) -> list[JobListing]:
        if len(jobs) <= LLM_CANDIDATE_MIN:
            return jobs

        candidate_limit = min(
            len(jobs),
            max(
                LLM_CANDIDATE_MIN,
                min(
                    self.llm_candidate_limit,
                    int(round(len(jobs) * LLM_CANDIDATE_RATIO)),
                ),
            ),
        )
        score_floor = 0.0
        if fallback_matches:
            top_score = fallback_matches[0].overall_score
            score_floor = max(top_score * LLM_SCORE_FLOOR_RATIO, top_score - LLM_SCORE_FLOOR_DELTA)
        job_by_url = {job.url: job for job in jobs}
        selected_urls: list[str] = []

        def add(url: str) -> None:
            if url and url not in selected_urls and url in job_by_url:
                selected_urls.append(url)

        for match in fallback_matches:
            add(match.job_url)
            if len(selected_urls) >= candidate_limit:
                break
            if len(selected_urls) >= LLM_CANDIDATE_MIN and match.overall_score < score_floor:
                break

        for job in jobs:
            if _title_exact_match_bonus(profile.target_roles, job.title) >= EXACT_TITLE_WEIGHT:
                add(job.url)
                continue
            if self.fallback_matcher._role_similarity(profile, job) >= 0.9:
                add(job.url)

        return [job_by_url[url] for url in selected_urls]

    def _score_titles(
        self,
        profile: ResumeProfile,
        indexed_jobs: list[tuple[int, JobListing]],
    ) -> dict[int, dict[str, Any]]:
        if not profile.target_roles or not indexed_jobs:
            return {}

        results: dict[int, dict[str, Any]] = {}
        for batch in chunked(indexed_jobs, 12):
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
                self.last_metrics["title_llm_requests"] = int(self.last_metrics.get("title_llm_requests", 0)) + 1
                response = self.client.responses.parse(
                    model=self.title_model,
                    temperature=0,
                    max_output_tokens=520,
                    input=(
                        "你是求職職稱比對器。請只根據候選人的目標角色與職缺職稱相近度評分。\n"
                        "similarity 請輸出 0 到 1 之間的小數：\n"
                        "1.0 = 幾乎同職稱；0.8 = 很接近；0.5 = 有關聯但不同；0.2 = 差異很大；0 = 無關。\n"
                        "reason 請用 18 字內繁中短句。\n"
                        f"候選人目標角色：{', '.join(profile.target_roles)}\n"
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
                self.last_usage = merge_openai_usage(
                    self.last_usage,
                    extract_openai_usage(response),
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
            else:
                if bool(cached.get("_memory_hit")):
                    self.last_metrics["title_cache_memory_hits"] = int(
                        self.last_metrics.get("title_cache_memory_hits", 0)
                    ) + 1
                else:
                    self.last_metrics["title_cache_disk_hits"] = int(
                        self.last_metrics.get("title_cache_disk_hits", 0)
                    ) + 1

            for item in cached.get("scores", []):
                results[int(item["job_index"])] = {
                    "similarity": max(0.0, min(1.0, float(item["similarity"]))),
                    "reason": normalize_text(str(item.get("reason", ""))),
                }
        return results

    def _score_semantics(
        self,
        profile: ResumeProfile,
        indexed_jobs: list[tuple[int, JobListing]],
    ) -> dict[str, dict[int, float]]:
        if not indexed_jobs:
            return {"skill": {}, "task": {}, "keyword": {}}

        profile_skill_text = _prepare_embedding_text(
            "\n".join(profile.core_skills + profile.tool_skills + profile.target_roles)
        )
        profile_task_text = _prepare_embedding_text(
            "\n".join(profile.preferred_tasks + profile.generated_prompts)
        )
        profile_keyword_text = _prepare_embedding_text(
            "\n".join([profile.summary] + profile.match_keywords + profile.domain_keywords)
        )

        job_skill_texts = {
            index: _prepare_embedding_text(
                "\n".join(
                    [job.requirement_text(), " ".join(job.extracted_skills), job.title]
                )
            )
            for index, job in indexed_jobs
        }
        job_task_texts = {
            index: _prepare_embedding_text("\n".join(job.work_content_items + [job.summary]))
            for index, job in indexed_jobs
        }
        job_keyword_texts = {
            index: _prepare_embedding_text(job.combined_text())
            for index, job in indexed_jobs
        }

        all_texts = unique_preserving_order(
            [
                profile_skill_text,
                profile_task_text,
                profile_keyword_text,
                *job_skill_texts.values(),
                *job_task_texts.values(),
                *job_keyword_texts.values(),
            ]
        )
        embeddings = self._embed_texts([text for text in all_texts if text])

        def cosine(left: str, right: str) -> float:
            if not left or not right:
                return 0.0
            return _cosine_similarity(embeddings.get(left, []), embeddings.get(right, []))

        return {
            "skill": {
                index: cosine(profile_skill_text, text)
                for index, text in job_skill_texts.items()
            },
            "task": {
                index: cosine(profile_task_text, text)
                for index, text in job_task_texts.items()
            },
            "keyword": {
                index: cosine(profile_keyword_text, text)
                for index, text in job_keyword_texts.items()
            },
        }

    def _should_skip_title_llm(
        self,
        profile: ResumeProfile,
        job: JobListing,
        fallback_match: ResumeJobMatch | None,
    ) -> bool:
        if _title_exact_match_bonus(profile.target_roles, job.title) >= EXACT_TITLE_WEIGHT:
            return True
        if fallback_match is None:
            return False
        return fallback_match.title_similarity >= (TITLE_LLM_SKIP_ROLE_SIMILARITY * 100.0)

    def _embed_texts(self, texts: list[str]) -> dict[str, list[float]]:
        vectors: dict[str, list[float]] = {}
        missing: list[str] = []

        for text in texts:
            cache_key = _stable_hash({"model": self.embedding_model, "text": text})
            memory_cached = self._embedding_memory_cache.get(cache_key)
            if memory_cached is not None:
                vectors[text] = list(memory_cached)
                self.last_metrics["embedding_memory_hits"] = int(
                    self.last_metrics.get("embedding_memory_hits", 0)
                ) + 1
                continue
            cached = self._read_cache(self.embedding_cache_dir, cache_key)
            if cached is not None:
                embedding = [float(value) for value in cached.get("embedding", [])]
                vectors[text] = embedding
                self._remember_embedding_cache(cache_key, embedding)
                self.last_metrics["embedding_disk_hits"] = int(
                    self.last_metrics.get("embedding_disk_hits", 0)
                ) + 1
                continue
            missing.append(text)

        if missing:
            self.last_metrics["embedding_remote_texts"] = int(
                self.last_metrics.get("embedding_remote_texts", 0)
            ) + len(missing)
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=missing,
            )
            self.last_usage = merge_openai_usage(
                self.last_usage,
                extract_openai_usage(response),
            )
            for text, item in zip(missing, response.data):
                embedding = [float(value) for value in item.embedding]
                vectors[text] = embedding
                cache_key = _stable_hash({"model": self.embedding_model, "text": text})
                self._remember_embedding_cache(cache_key, embedding)
                self._write_cache(
                    self.embedding_cache_dir,
                    cache_key,
                    {"embedding": embedding},
                )

        return vectors

    def _read_cache(self, directory: Path | None, key: str) -> dict[str, Any] | None:
        memory_cache = (
            self._title_memory_cache
            if directory == self.title_cache_dir
            else None
        )
        memory_cached = memory_cache.get(key) if memory_cache is not None else None
        if memory_cached is not None:
            payload = dict(memory_cached)
            payload["_memory_hit"] = True
            return payload
        if directory is None:
            return None
        path = directory / f"{key}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if directory == self.title_cache_dir:
            self._remember_title_cache(key, payload)
        payload["_memory_hit"] = False
        return payload

    def _write_cache(self, directory: Path | None, key: str, payload: dict[str, Any]) -> None:
        if directory == self.title_cache_dir:
            self._remember_title_cache(key, payload)
        if directory is None:
            return
        path = directory / f"{key}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def _remember_embedding_cache(self, key: str, embedding: list[float]) -> None:
        self._embedding_memory_cache[key] = list(embedding)
        while len(self._embedding_memory_cache) > RESUME_MATCH_MEMORY_CACHE_MAX:
            oldest_key = next(iter(self._embedding_memory_cache))
            self._embedding_memory_cache.pop(oldest_key, None)

    def _remember_title_cache(self, key: str, payload: dict[str, Any]) -> None:
        self._title_memory_cache[key] = dict(payload)
        while len(self._title_memory_cache) > RESUME_MATCH_MEMORY_CACHE_MAX:
            oldest_key = next(iter(self._title_memory_cache))
            self._title_memory_cache.pop(oldest_key, None)


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
            if role_lower == title_lower:
                best = max(best, 1.0)
            elif role_lower == matched_role_lower:
                best = max(best, 0.9)
            elif role_lower and (role_lower in title_lower or title_lower in role_lower):
                best = max(best, 0.82)
            elif matched_role_lower and (
                role_lower in matched_role_lower or matched_role_lower in role_lower
            ):
                best = max(best, 0.74)
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

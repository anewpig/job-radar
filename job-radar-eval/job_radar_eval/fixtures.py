"""固定評估資料，避免 baseline 被即時資料波動影響。"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from .config import EvalConfig


def load_json_fixture(path: Path):
    """讀取 JSON fixture。"""
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl_fixture(path: Path) -> list[dict]:
    """讀取 JSONL fixture。"""
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def load_assistant_questions(config: EvalConfig) -> list[dict]:
    """載入 AI 助理固定測題。"""
    return load_json_fixture(config.fixtures_dir / "assistant_questions.json")


def load_resume_cases(config: EvalConfig) -> list[dict]:
    """載入履歷分析固定測例。"""
    return load_json_fixture(config.fixtures_dir / "resume_cases.json")


def load_resume_match_labels(config: EvalConfig) -> list[dict]:
    """載入履歷匹配標註資料。"""
    return load_jsonl_fixture(config.fixtures_dir / "resume_match_labels.jsonl")


def load_retrieval_cases(config: EvalConfig) -> list[dict]:
    """載入 retrieval 固定測題。"""
    return load_json_fixture(config.fixtures_dir / "retrieval_cases.json")


def load_real_snapshot(config: EvalConfig, snapshot_path: Path | None = None):
    """用正式 loader 讀取真實 jobs_latest.json。"""
    from job_spy_tw.storage import load_snapshot

    path = (snapshot_path or config.snapshot_path).resolve()
    snapshot = load_snapshot(path)
    if snapshot is None:
        raise FileNotFoundError(f"找不到或無法解析快照：{path}")
    return snapshot


def top_counter_values(values: list[str], limit: int = 5) -> list[tuple[str, int]]:
    """回傳去空值後的常見值統計。"""
    counter = Counter(value for value in values if value)
    return counter.most_common(limit)


def build_retrieval_chunks_fixture():
    """建立固定知識片段，供 retrieval.py baseline 使用。"""
    from job_spy_tw.assistant.models import KnowledgeChunk

    return [
        KnowledgeChunk(
            chunk_id="ai-summary",
            source_type="job",
            label="AI 應用工程師摘要",
            text="職稱：AI應用工程師\n薪資：月薪 60,000 - 80,000\n技能：Python、LLM、RAG、Docker\n工作內容：需求分析、API 串接、流程自動化",
            url="https://example.com/jobs/1",
        ),
        KnowledgeChunk(
            chunk_id="ai-skills",
            source_type="job-skill",
            label="AI 技能需求",
            text="Python；LLM；RAG；Docker；AWS",
            url="https://example.com/jobs/1",
        ),
        KnowledgeChunk(
            chunk_id="market-skill-llm",
            source_type="market-skill",
            label="市場技能：LLM",
            text="LLM\n重要度：高\n出現次數：2\n範例職缺：AI應用工程師；Senior AI Platform Engineer",
        ),
        KnowledgeChunk(
            chunk_id="salary-overview",
            source_type="job",
            label="AI 薪資概覽",
            text="AI 類職缺多落在月薪 60,000 到 80,000，資深職缺可到 90,000 以上。",
        ),
        KnowledgeChunk(
            chunk_id="pm-summary",
            source_type="job",
            label="Product Manager 摘要",
            text="職稱：Product Manager\n技能：Figma、Jira、PRD\n工作內容：產品路線圖規劃、需求訪談、跨部門協作",
            url="https://example.com/jobs/3",
        ),
        KnowledgeChunk(
            chunk_id="pm-work",
            source_type="job-work",
            label="PM 工作內容",
            text="產品路線圖規劃；需求訪談；跨部門協作；進度管理",
            url="https://example.com/jobs/3",
        ),
        KnowledgeChunk(
            chunk_id="pm-skills",
            source_type="job-skill",
            label="PM 技能需求",
            text="Figma；Jira；PRD；SQL",
            url="https://example.com/jobs/3",
        ),
        KnowledgeChunk(
            chunk_id="firmware-summary",
            source_type="job",
            label="韌體工程師摘要",
            text="職稱：藍牙韌體設計工程師\n技能：C/C++、RTOS、ARM、Bluetooth\n工作內容：Bluetooth SoC 韌體開發、FPGA/ASIC 驗證、客戶支援",
            url="https://example.com/jobs/6",
        ),
        KnowledgeChunk(
            chunk_id="firmware-skills",
            source_type="job-skill",
            label="韌體技能需求",
            text="C/C++；RTOS；ARM；MIPS；Linux",
            url="https://example.com/jobs/6",
        ),
        KnowledgeChunk(
            chunk_id="rag-summary",
            source_type="job",
            label="RAG AI Engineer 摘要",
            text="職稱：RAG AI Engineer\n技能：Python、RAG、向量資料庫、API\n工作內容：Knowledge Base 維護、檢索優化、API 整合",
            url="https://example.com/jobs/5",
        ),
        KnowledgeChunk(
            chunk_id="rag-work",
            source_type="job-work",
            label="RAG 工作內容",
            text="Knowledge Base 維護；向量資料庫檢索優化；RAG workflow；API 整合",
            url="https://example.com/jobs/5",
        ),
    ]


def build_market_snapshot_fixture():
    """建立固定的市場快照，供 baseline 重複使用。"""
    from job_spy_tw.models import ItemInsight, JobListing, MarketSnapshot, SkillInsight, TargetRole

    return MarketSnapshot(
        generated_at="2026-04-05T10:00:00",
        queries=["AI工程師", "韌體工程師", "Product Manager"],
        role_targets=[
            TargetRole(name="AI應用工程師", priority=1, keywords=["LLM", "RAG", "Python"]),
            TargetRole(name="韌體工程師", priority=2, keywords=["C/C++", "RTOS", "ARM"]),
            TargetRole(name="PM", priority=3, keywords=["Figma", "Jira", "PRD"]),
        ],
        jobs=[
            JobListing(
                source="104",
                title="AI應用工程師",
                company="Example 104 AI Agent",
                location="新北市",
                url="https://example.com/jobs/1",
                summary="月薪 60,000 - 80,000，負責 AI Agent 應用開發、RAG workflow 與 API 串接。",
                salary="月薪 60,000 - 80,000",
                matched_role="AI應用工程師",
                extracted_skills=["Python", "LLM", "RAG", "LangChain", "API"],
                work_content_items=["AI Agent 系統設計", "API 串接", "流程自動化"],
                required_skill_items=["Python", "LLM", "RAG", "Docker"],
                requirement_items=["熟悉 AWS"],
            ),
            JobListing(
                source="LinkedIn",
                title="Senior AI Platform Engineer",
                company="Example Platform",
                location="台北市",
                url="https://example.com/jobs/2",
                summary="建置 AI 平台與 RAG workflow。",
                salary="月薪 90,000 - 120,000",
                matched_role="AI應用工程師",
                extracted_skills=["Python", "LLM", "RAG", "Kubernetes"],
                work_content_items=["RAG 平台建置", "推理服務部署"],
                required_skill_items=["Python", "RAG", "Kubernetes"],
                requirement_items=["熟悉雲端架構"],
            ),
            JobListing(
                source="1111",
                title="Product Manager",
                company="Example PM",
                location="新北市",
                url="https://example.com/jobs/3",
                summary="規劃 AI 產品 roadmap、撰寫 PRD，並與跨部門協作推進。",
                salary="月薪 55,000 - 75,000",
                matched_role="PM",
                extracted_skills=["Figma", "Jira", "PRD"],
                work_content_items=["產品路線圖規劃", "需求訪談", "跨部門協作"],
                required_skill_items=["Figma", "Jira", "PRD"],
                requirement_items=["具 SQL 基礎"],
            ),
            JobListing(
                source="Cake",
                title="藍牙韌體設計工程師C1",
                company="Example Firmware",
                location="新竹市",
                url="https://example.com/jobs/4",
                summary="Bluetooth SoC 韌體開發，重視 C/C++、RTOS 與 ARM/MIPS。",
                salary="月薪 50,000 以上或面議",
                matched_role="韌體工程師",
                extracted_skills=["C++", "RTOS", "ARM", "Bluetooth"],
                work_content_items=["Bluetooth SoC 韌體開發", "FPGA/ASIC 驗證", "客戶支援"],
                required_skill_items=["C++", "RTOS", "ARM"],
                requirement_items=["熟悉 MIPS 架構"],
            ),
            JobListing(
                source="Cake",
                title="RAG AI Engineer",
                company="Example RAG",
                location="新北市",
                url="https://example.com/jobs/5",
                summary="年薪 1.2M - 2.0M，負責 Knowledge Base、RAG workflow 與向量資料庫整合。",
                salary="年薪 1,200,000 - 2,000,000",
                matched_role="AI應用工程師",
                extracted_skills=["Python", "RAG", "向量資料庫", "API", "LLM"],
                work_content_items=["Knowledge Base 維護", "向量資料庫檢索優化", "API 整合"],
                required_skill_items=["Python", "RAG", "向量資料庫"],
                requirement_items=["熟悉 Prompt Engineering"],
            ),
            JobListing(
                source="LinkedIn",
                title="Embedded Linux Firmware Engineer",
                company="Example Embedded",
                location="新竹市",
                url="https://example.com/jobs/6",
                summary="嵌入式 Linux 韌體開發，重視 C/C++、Linux、RTOS、ARM。",
                salary="面議",
                matched_role="韌體工程師",
                extracted_skills=["C++", "Linux", "RTOS", "ARM", "Python"],
                work_content_items=["Bootloader 與 Driver 開發", "系統 bring-up", "軟硬體整合"],
                required_skill_items=["C++", "Linux", "RTOS", "ARM"],
                requirement_items=["Python 為加分"],
            ),
            JobListing(
                source="104",
                title="Machine Learning Engineer",
                company="Example ML Team",
                location="台北市",
                url="https://example.com/jobs/7",
                summary="負責模型訓練、特徵工程與部署，重視 Python、PyTorch、TensorFlow、AWS、Docker。",
                salary="月薪 70,000 - 100,000",
                matched_role="AI工程師",
                extracted_skills=["Python", "PyTorch", "TensorFlow", "AWS", "Docker"],
                work_content_items=["模型訓練", "特徵工程", "模型部署"],
                required_skill_items=["Python", "PyTorch", "TensorFlow", "AWS", "Docker"],
                requirement_items=["具模型部署經驗"],
            ),
            JobListing(
                source="Cake",
                title="Backend Engineer (AI Platform)",
                company="Example Backend Platform",
                location="台北市",
                url="https://example.com/jobs/8",
                summary="負責後端服務與 AI 平台 API，重視 Python、API Design、System Design、Docker、AWS。",
                salary="月薪 65,000 - 95,000",
                matched_role="軟體工程師",
                extracted_skills=["Python", "API Design", "System Design", "Docker", "AWS"],
                work_content_items=["後端服務開發", "REST API 設計", "系統整合"],
                required_skill_items=["Python", "API Design", "System Design", "Docker", "AWS"],
                requirement_items=["熟悉微服務架構"],
            ),
            JobListing(
                source="1111",
                title="AI Solution Engineer",
                company="Example Solution Team",
                location="新北市",
                url="https://example.com/jobs/9",
                summary="負責客戶需求訪談、解決方案設計與技術導入，重視 Requirement Analysis、Technical Support、Customer Communication、Solution Design、API。",
                salary="月薪 58,000 - 85,000",
                matched_role="應用工程師",
                extracted_skills=["Requirement Analysis", "Technical Support", "Customer Communication", "Solution Design", "API Design"],
                work_content_items=["客戶需求訪談", "解決方案設計", "技術導入"],
                required_skill_items=["Requirement Analysis", "Technical Support", "Customer Communication", "Solution Design", "API Design"],
                requirement_items=["具售前支援與導入經驗"],
            ),
            JobListing(
                source="LinkedIn",
                title="Project Manager / AI Delivery",
                company="Example Delivery Office",
                location="新北市",
                url="https://example.com/jobs/10",
                summary="負責 AI 專案規劃與交付，重視 Project Management、Jira、Roadmap、Stakeholder Management、PRD。",
                salary="月薪 60,000 - 90,000",
                matched_role="PM",
                extracted_skills=["Project Management", "Jira", "Roadmap", "Stakeholder Management", "PRD"],
                work_content_items=["專案規劃", "跨部門協調", "需求控管"],
                required_skill_items=["Project Management", "Jira", "Roadmap", "Stakeholder Management", "PRD"],
                requirement_items=["熟悉 AI 專案交付流程"],
            ),
        ],
        skills=[
            SkillInsight(skill="Python", category="程式語言", score=0.95, importance="高", occurrences=3),
            SkillInsight(skill="LLM", category="AI", score=0.92, importance="高", occurrences=2),
            SkillInsight(skill="RTOS", category="韌體", score=0.82, importance="高", occurrences=2),
            SkillInsight(skill="Figma", category="產品", score=0.65, importance="中", occurrences=1),
        ],
        task_insights=[
            ItemInsight(item="API 串接", score=0.88, importance="高", occurrences=1),
            ItemInsight(item="流程自動化", score=0.84, importance="高", occurrences=1),
            ItemInsight(item="向量資料庫檢索優化", score=0.8, importance="高", occurrences=1),
            ItemInsight(item="Bluetooth SoC 韌體開發", score=0.79, importance="高", occurrences=1),
            ItemInsight(item="產品路線圖規劃", score=0.73, importance="中", occurrences=1),
        ],
        errors=[],
    )


def build_resume_profile_fixture():
    """建立固定履歷摘要，供 AI 助理個人化問答測試使用。"""
    from job_spy_tw.models import ResumeProfile

    return ResumeProfile(
        summary="具備 Python 與 AI 專案經驗，曾開發企業知識搜尋與 RAG workflow。",
        target_roles=["AI應用工程師"],
        core_skills=["LLM", "RAG"],
        tool_skills=["Python"],
        preferred_tasks=["API 串接", "流程自動化"],
    )

from __future__ import annotations

from .models import TargetRole


DEFAULT_TARGET_ROLES: list[TargetRole] = [
    TargetRole(
        name="AI應用工程師",
        priority=1,
        keywords=[
            "AI應用工程師",
            "Applied AI Engineer",
            "生成式AI工程師",
            "LLM Engineer",
            "RAG",
            "AI Agent",
        ],
    ),
    TargetRole(
        name="AI工程師",
        priority=2,
        keywords=[
            "AI工程師",
            "AI Engineer",
            "Machine Learning Engineer",
            "ML Engineer",
            "Deep Learning",
            "Artificial Intelligence",
        ],
    ),
    TargetRole(
        name="軟體工程師",
        priority=3,
        keywords=[
            "軟體工程師",
            "Software Engineer",
            "Backend Engineer",
            "Full Stack Engineer",
            "API",
            "System Design",
        ],
    ),
    TargetRole(
        name="PM",
        priority=4,
        keywords=[
            "PM",
            "Product Manager",
            "Project Manager",
            "產品經理",
            "專案經理",
            "Roadmap",
        ],
    ),
    TargetRole(
        name="應用工程師",
        priority=5,
        keywords=[
            "應用工程師",
            "Application Engineer",
            "Field Application Engineer",
            "FAE",
            "Solution Engineer",
            "客戶導入",
        ],
    ),
]


def build_default_queries(
    roles: list[TargetRole] | None = None,
    keywords_per_role: int = 2,
) -> list[str]:
    active_roles = DEFAULT_TARGET_ROLES if roles is None else roles
    queries: list[str] = []
    for role in active_roles:
        queries.append(role.name)
        queries.extend(role.keywords[: max(0, keywords_per_role)])
    return list(dict.fromkeys(query.strip() for query in queries if query.strip()))

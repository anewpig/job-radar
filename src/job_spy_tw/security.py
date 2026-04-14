"""Role and authorization helpers."""

from __future__ import annotations

from typing import Iterable


USER_ROLE_GUEST = "guest"
USER_ROLE_USER = "user"
USER_ROLE_OPERATOR = "operator"
USER_ROLE_ADMIN = "admin"
ALLOWED_USER_ROLES = (
    USER_ROLE_GUEST,
    USER_ROLE_USER,
    USER_ROLE_OPERATOR,
    USER_ROLE_ADMIN,
)


def normalize_user_role(role: str) -> str:
    cleaned = str(role or "").strip().lower()
    if cleaned in ALLOWED_USER_ROLES:
        return cleaned
    return USER_ROLE_USER


def parse_allowed_roles(roles: Iterable[str]) -> tuple[str, ...]:
    normalized = tuple(
        normalize_user_role(role)
        for role in roles
        if normalize_user_role(role) != USER_ROLE_GUEST
    )
    return normalized or (USER_ROLE_OPERATOR, USER_ROLE_ADMIN)


def can_access_backend_console(
    enabled: bool = True,
    user_role: str = "",
    allowed_roles: Iterable[str] = (),
) -> bool:
    if not bool(enabled):
        return False
    normalized_role = normalize_user_role(user_role)
    return normalized_role in set(parse_allowed_roles(allowed_roles))

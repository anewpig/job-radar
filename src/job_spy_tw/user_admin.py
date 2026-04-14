"""Administrative CLI helpers for user role management."""

from __future__ import annotations

import argparse

from .config import load_settings
from .product_store import ProductStore
from .security import ALLOWED_USER_ROLES, normalize_user_role


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect users and assign Job Radar roles.")
    parser.add_argument("--base-dir", default=".", help="Project base directory.")
    parser.add_argument("--list-users", action="store_true", help="List current users.")
    parser.add_argument("--user-id", type=int, default=0, help="Target user id for role assignment.")
    parser.add_argument(
        "--set-role",
        default="",
        help=f"Assign role to a user. Allowed: {', '.join(ALLOWED_USER_ROLES)}",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    settings = load_settings(args.base_dir)
    product_store = ProductStore(settings.product_state_db_path)

    if bool(args.list_users):
        for user in product_store.list_users(include_guest=True):
            print(
                f"id={user.id} email={user.email} role={user.role} "
                f"guest={int(user.is_guest)} last_login_at={user.last_login_at or '-'}"
            )
        return 0

    if args.user_id and str(args.set_role or "").strip():
        user = product_store.set_user_role(
            user_id=int(args.user_id),
            role=normalize_user_role(args.set_role),
        )
        product_store.record_audit_event(
            event_type="auth.role_assignment",
            status="success",
            target_type="user",
            target_id=str(user.id),
            details={"assigned_role": user.role, "email": user.email},
            user_id=int(user.id),
            actor_role=user.role,
            trace_id=f"admin-{user.id}",
        )
        print(f"updated user #{user.id} -> role={user.role}")
        return 0

    raise SystemExit("請提供 --list-users，或使用 --user-id 搭配 --set-role。")

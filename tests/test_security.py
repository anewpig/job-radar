"""Tests for role normalization and backend-console access gating."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.security import (  # noqa: E402
    USER_ROLE_ADMIN,
    USER_ROLE_GUEST,
    USER_ROLE_OPERATOR,
    USER_ROLE_USER,
    can_access_backend_console,
    normalize_user_role,
)


class SecurityTests(unittest.TestCase):
    def test_normalize_user_role_falls_back_to_user(self) -> None:
        self.assertEqual(normalize_user_role(""), USER_ROLE_USER)
        self.assertEqual(normalize_user_role("weird-role"), USER_ROLE_USER)

    def test_can_access_backend_console_respects_allowed_roles(self) -> None:
        self.assertFalse(can_access_backend_console(False, USER_ROLE_ADMIN, ("admin",)))
        self.assertFalse(can_access_backend_console(True, USER_ROLE_USER, ("admin", "operator")))
        self.assertFalse(can_access_backend_console(True, USER_ROLE_GUEST, ("admin", "operator")))
        self.assertTrue(can_access_backend_console(True, USER_ROLE_OPERATOR, ("admin", "operator")))
        self.assertTrue(can_access_backend_console(True, USER_ROLE_ADMIN, ("admin", "operator")))

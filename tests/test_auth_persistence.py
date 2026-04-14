"""Tests for auth persistence token encoding/decoding."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.ui.auth_persistence import TokenPayload, _decode_token, _encode_token  # noqa: E402


class AuthPersistenceTests(unittest.TestCase):
    def test_encode_decode_round_trip(self) -> None:
        payload = TokenPayload(user_id=42, issued_at=100, expires_at=200)
        token = _encode_token(payload, secret="secret-key")
        decoded = _decode_token(token, secret="secret-key")
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.user_id, 42)
        self.assertEqual(decoded.issued_at, 100)
        self.assertEqual(decoded.expires_at, 200)

    def test_decode_rejects_tampered_token(self) -> None:
        payload = TokenPayload(user_id=7, issued_at=10, expires_at=20)
        token = _encode_token(payload, secret="secret-key")
        body, sig = token.split(".", 1)
        tampered = body[:-2] + "ab" + "." + sig
        self.assertIsNone(_decode_token(tampered, secret="secret-key"))

    def test_decode_rejects_wrong_secret(self) -> None:
        payload = TokenPayload(user_id=3, issued_at=10, expires_at=20)
        token = _encode_token(payload, secret="secret-key")
        self.assertIsNone(_decode_token(token, secret="other-secret"))


if __name__ == "__main__":
    unittest.main()

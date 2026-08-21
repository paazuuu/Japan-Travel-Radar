"""Auth security primitives: password hashing + JWT (no DB, stdlib only)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql://x:x@127.0.0.1:1/none")

from app import security  # noqa: E402


def test_password_hash_roundtrip():
    h = security.hash_password("s3cret-pw")
    assert h.startswith("pbkdf2_sha256$")
    assert security.verify_password("s3cret-pw", h)
    assert not security.verify_password("wrong", h)


def test_password_hash_is_salted():
    assert security.hash_password("x") != security.hash_password("x")


def test_jwt_roundtrip_and_tamper():
    tok = security.create_token("user-123", "a@b.com")
    payload = security.decode_token(tok)
    assert payload["sub"] == "user-123" and payload["email"] == "a@b.com"
    # tampering with the payload invalidates the signature
    head, _, sig = tok.split(".")
    assert security.decode_token(f"{head}.{security._b64url(b'{}')}.{sig}") is None
    assert security.decode_token("not.a.jwt") is None


def test_expired_token_rejected(monkeypatch):
    monkeypatch.setattr(security, "TOKEN_TTL_SECONDS", -1)
    tok = security.create_token("u", "e@x.com")
    assert security.decode_token(tok) is None

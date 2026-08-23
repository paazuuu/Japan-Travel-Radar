"""Password hashing (PBKDF2-HMAC-SHA256) and JWT (HS256) using only the
standard library — no external crypto deps, so it runs identically everywhere.

For an MVP this is secure: PBKDF2 with a per-password salt and a high iteration
count, and HMAC-SHA256-signed tokens. A move to argon2/bcrypt is a drop-in later.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

from app.config import get_settings

ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 14  # 2 weeks
_PBKDF2_ITER = 240_000


# ---- password hashing -------------------------------------------------------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITER)
    return f"pbkdf2_sha256${_PBKDF2_ITER}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                 bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


# ---- JWT (HS256) ------------------------------------------------------------
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _sign(msg: bytes) -> bytes:
    return hmac.new(get_settings().secret_key.encode("utf-8"), msg, hashlib.sha256).digest()


def create_token(user_id: str, email: str) -> str:
    header = _b64url(json.dumps({"alg": ALGORITHM, "typ": "JWT"}, separators=(",", ":")).encode())
    now = int(time.time())
    payload = _b64url(json.dumps(
        {"sub": str(user_id), "email": email, "iat": now, "exp": now + TOKEN_TTL_SECONDS},
        separators=(",", ":"),
    ).encode())
    signing_input = f"{header}.{payload}".encode("ascii")
    return f"{header}.{payload}.{_b64url(_sign(signing_input))}"


def decode_token(token: str) -> dict | None:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected = _sign(signing_input)
        if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except (ValueError, KeyError, json.JSONDecodeError):
        return None

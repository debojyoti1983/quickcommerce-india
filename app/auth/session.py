"""Signed session cookies (stateless, HMAC-signed).

Token = base64(payload).signature, where payload is "user_id:expiry". The
signature is HMAC-SHA256 over the payload with the server secret, verified in
constant time. No server-side session table needed for this demo.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from functools import lru_cache

from app.config import get_settings

COOKIE_NAME = "qc_session"


@lru_cache
def _secret() -> bytes:
    configured = get_settings().session_secret
    # Random per-process fallback (sessions reset on restart) when unset.
    return (configured or secrets.token_hex(32)).encode()


def _sign(payload: str) -> str:
    return hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()


def issue(user_id: int) -> str:
    expiry = int(time.time()) + get_settings().session_ttl_seconds
    payload = f"{user_id}:{expiry}"
    b64 = base64.urlsafe_b64encode(payload.encode()).decode()
    return f"{b64}.{_sign(payload)}"


def read(token: str | None) -> int | None:
    """Return the user_id if the token is validly signed and unexpired."""
    if not token or "." not in token:
        return None
    b64, sig = token.rsplit(".", 1)
    try:
        payload = base64.urlsafe_b64decode(b64.encode()).decode()
    except (ValueError, UnicodeDecodeError):
        return None
    if not hmac.compare_digest(sig, _sign(payload)):
        return None
    try:
        user_id_str, expiry_str = payload.split(":")
        if int(expiry_str) < time.time():
            return None
        return int(user_id_str)
    except (ValueError, TypeError):
        return None

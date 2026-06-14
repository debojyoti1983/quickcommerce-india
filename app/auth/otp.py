"""One-time-password generation and verification.

In-process store (demo). OTP is hashed at rest, expires, and is attempt-limited.
There is no SMS/email provider wired, so `request_otp` returns the code only when
``expose_demo_otp`` is set — that flag MUST be off in production, where the code
would instead be sent via a provider and never returned to the client.
"""

from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass

_TTL_SECONDS = 300  # 5 minutes
_MAX_ATTEMPTS = 5


@dataclass
class _Entry:
    otp_hash: str
    expires_at: float
    attempts: int = 0


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


class OtpStore:
    def __init__(self) -> None:
        self._store: dict[str, _Entry] = {}

    def request(self, identifier: str) -> str:
        """Generate a 6-digit OTP for the identifier and return it (caller decides
        whether to expose it). Overwrites any previous unexpired code."""
        code = f"{secrets.randbelow(1_000_000):06d}"
        self._store[identifier] = _Entry(otp_hash=_hash(code), expires_at=time.time() + _TTL_SECONDS)
        return code

    def verify(self, identifier: str, code: str) -> bool:
        entry = self._store.get(identifier)
        if entry is None:
            return False
        if time.time() > entry.expires_at:
            self._store.pop(identifier, None)
            return False
        entry.attempts += 1
        if entry.attempts > _MAX_ATTEMPTS:
            self._store.pop(identifier, None)
            return False
        import hmac

        if hmac.compare_digest(entry.otp_hash, _hash(code)):
            self._store.pop(identifier, None)  # single-use
            return True
        return False


# Single shared instance for the process.
otp_store = OtpStore()

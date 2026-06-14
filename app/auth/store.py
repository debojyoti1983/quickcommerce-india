"""User store + password hashing + identifier validation.

SQLite-backed (one connection per call — fine for this app's concurrency). A new
sqlite3 connection per operation keeps it thread-safe under uvicorn without locks.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
import time
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel

from app.config import get_settings

_PBKDF2_ITERATIONS = 200_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?\d{10,13}$")


class User(BaseModel):
    id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    sso_provider: Optional[str] = None
    created_at: float


def normalize_identifier(identifier: str) -> tuple[str, str]:
    """Return (kind, normalized) where kind is 'email' or 'phone'.

    Raises ValueError if it's neither a valid email nor phone number.
    """
    raw = (identifier or "").strip()
    if _EMAIL_RE.match(raw):
        return "email", raw.lower()
    phone = re.sub(r"[\s\-()]", "", raw)
    if _PHONE_RE.match(phone):
        return "phone", phone
    raise ValueError("Enter a valid email address or phone number.")


# --- password hashing (PBKDF2-HMAC-SHA256, per-user salt) --------------------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: Optional[str]) -> bool:
    if not stored:
        return False
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)  # constant-time compare
    except (ValueError, TypeError):
        return False


class UserStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    phone TEXT UNIQUE,
                    password_hash TEXT,
                    sso_provider TEXT,
                    created_at REAL NOT NULL
                )
                """
            )

    @staticmethod
    def _to_user(row: sqlite3.Row) -> User:
        return User(
            id=row["id"], email=row["email"], phone=row["phone"],
            sso_provider=row["sso_provider"], created_at=row["created_at"],
        )

    def get_by_identifier(self, identifier: str) -> Optional[User]:
        kind, value = normalize_identifier(identifier)
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM users WHERE {kind} = ?", (value,)
            ).fetchone()
        return self._to_user(row) if row else None

    def _password_hash(self, identifier: str) -> Optional[str]:
        kind, value = normalize_identifier(identifier)
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT password_hash FROM users WHERE {kind} = ?", (value,)
            ).fetchone()
        return row["password_hash"] if row else None

    def create_user(
        self,
        *,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        sso_provider: Optional[str] = None,
    ) -> User:
        pw_hash = hash_password(password) if password else None
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO users (email, phone, password_hash, sso_provider, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (email, phone, pw_hash, sso_provider, time.time()),
            )
            uid = cur.lastrowid
            row = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
        return self._to_user(row)

    def get_or_create(self, identifier: str, *, sso_provider: Optional[str] = None) -> User:
        """Used by OTP / SSO login — passwordless account provisioning."""
        existing = self.get_by_identifier(identifier)
        if existing:
            return existing
        kind, value = normalize_identifier(identifier)
        return self.create_user(**{kind: value}, sso_provider=sso_provider)

    def check_password(self, identifier: str, password: str) -> Optional[User]:
        if not verify_password(password, self._password_hash(identifier)):
            return None
        return self.get_by_identifier(identifier)


def _seed_demo_user(store: UserStore) -> None:
    """Seed a known account so password login works out of the box (demo only)."""
    if store.get_by_identifier("demo@quickcommerce.in") is None:
        store.create_user(
            email="demo@quickcommerce.in", phone="+919999999999", password="demo1234"
        )


@lru_cache
def get_user_store() -> UserStore:
    store = UserStore(get_settings().auth_db_path)
    _seed_demo_user(store)
    return store

"""Module `auth` — demo-grade but architecturally-correct user authentication.

Email/phone identity with either password or OTP, plus stubbed social SSO.
Passwords are PBKDF2-hashed (never stored or logged in plaintext); sessions are
signed HttpOnly cookies. OTP delivery and SSO are simulated (no SMS/OAuth
provider) — the real providers slot in behind the same service functions, with
credentials sourced from env/secrets, never hardcoded.
"""

from app.auth.store import UserStore, get_user_store, normalize_identifier

__all__ = ["UserStore", "get_user_store", "normalize_identifier"]

"""Module `accounts` — simulated connected-account / membership detection.

IMPORTANT: this NEVER collects, transmits, or stores a real password. It stands
in for an official OAuth "connect account" flow (the real apps expose no public
membership API). It returns a simulated session + the membership-programme status
for a demo profile, so the UX of "detect my memberships" can be shown safely.
"""

from app.accounts.mock_accounts import AccountStatus, active_memberships, detect_accounts

__all__ = ["AccountStatus", "active_memberships", "detect_accounts"]

"""Mock account directory — simulated membership detection for the demo user.

No credentials of any kind are accepted or stored here. The "connect" is a
stand-in for OAuth: it reports, per platform, whether the simulated user holds
that platform's paid membership programme. `_DEMO_ACTIVE` is the demo profile —
deliberately a realistic *mix* (holds some, not others) so detection is meaningful.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.bootstrap.registry import CONNECTORS


class AccountStatus(BaseModel):
    platform: str  # internal connector name
    display_name: str
    connected: bool
    membership: str | None  # programme name, e.g. "Swiggy One"; None = no programme
    membership_active: bool
    detail: str


# Demo profile: programmes the simulated user actually holds. (Not BB Star — so
# the user can see a "not a member" result too.) Swap this for real OAuth later.
_DEMO_ACTIVE: set[str] = {"Swiggy One", "Zomato Gold", "Prime"}


def detect_accounts() -> list[AccountStatus]:
    """Simulate connecting each platform and report membership status."""
    statuses: list[AccountStatus] = []
    for spec in CONNECTORS:
        if spec.membership is None:
            statuses.append(
                AccountStatus(
                    platform=spec.name,
                    display_name=spec.display_name,
                    connected=True,
                    membership=None,
                    membership_active=False,
                    detail="No membership programme",
                )
            )
            continue
        active = spec.membership in _DEMO_ACTIVE
        statuses.append(
            AccountStatus(
                platform=spec.name,
                display_name=spec.display_name,
                connected=True,
                membership=spec.membership,
                membership_active=active,
                detail="Active member" if active else "Not a member",
            )
        )
    return statuses


def active_memberships() -> list[str]:
    """Distinct membership programmes the demo user holds (e.g. for auto-fill)."""
    seen: list[str] = []
    for s in detect_accounts():
        if s.membership_active and s.membership and s.membership not in seen:
            seen.append(s.membership)
    return seen

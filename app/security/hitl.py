"""Human-in-the-loop gate for irreversible / high-stakes actions.

No order is ever placed autonomously. ``prepare_action`` returns a decision that
either requires explicit approval (with the full context the human needs) or, for
low-stakes actions, is auto-approved. Approvals are returned with an idempotency
key so a retry can never double-act.
"""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import BaseModel

from app.bootstrap.domain_profile import DomainProfile


class HITLDecision(BaseModel):
    action: str
    requires_approval: bool
    reason: str
    idempotency_key: str
    summary: dict[str, Any]


def _idempotency_key(action: str, summary: dict[str, Any]) -> str:
    # Stable across retries of the *same* logical action (no Date/random used).
    basis = action + "|" + "|".join(f"{k}={summary[k]}" for k in sorted(summary))
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def prepare_action(action: str, summary: dict[str, Any], profile: DomainProfile) -> HITLDecision:
    requires = profile.requires_hitl(action)
    reason = (
        "High-stakes action — requires explicit human approval before execution."
        if requires
        else "Low-stakes action — safe to proceed."
    )
    return HITLDecision(
        action=action,
        requires_approval=requires,
        reason=reason,
        idempotency_key=_idempotency_key(action, summary),
        summary=summary,
    )

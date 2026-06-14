"""Module `security` — guardrails + human-in-the-loop.

This slice ships the HITL gate: high-stakes actions (place order, apply paid
coupon, modify subscription, change payment) are NEVER autonomous. The assistant
prepares the action and returns it for explicit human approval.
"""

from app.security.hitl import HITLDecision, prepare_action

__all__ = ["HITLDecision", "prepare_action"]

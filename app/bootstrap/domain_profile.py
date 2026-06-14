"""The domain profile: authority tiers, recency decay, abstention, HITL triggers.

These are the India quick-commerce policy knobs the rest of the app reads. Half-
lives are in SECONDS and reflect how fast each datum goes stale.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.models import HITLTrigger


class DomainProfile(BaseModel):
    domain: str = "qcommerce_india"
    currency: str = "INR"

    # How fast each kind of datum decays (seconds = one half-life).
    recency_decay_half_lives: dict[str, int] = Field(
        default_factory=lambda: {
            "eta": 300,  # 5 min  — surge + rider availability shift fast
            "availability": 600,  # 10 min — stock depletes fast
            "serviceability": 1800,  # 30 min — store open/closed
            "offers": 3600,  # 1 hr  — coupon validity windows
            "price": 7200,  # 2 hr  — dynamic pricing
        }
    )

    # Below this composite confidence -> abstain instead of guessing.
    abstention_confidence_threshold: float = 0.55

    # Actions that ALWAYS require explicit human approval.
    hitl_triggers: list[HITLTrigger] = Field(
        default_factory=lambda: [
            HITLTrigger.PLACE_ORDER,
            HITLTrigger.APPLY_PAID_COUPON,
            HITLTrigger.MODIFY_SUBSCRIPTION,
            HITLTrigger.PAYMENT_METHOD_CHANGE,
        ]
    )

    # India-specific defaults.
    default_veg_filter: bool = False
    max_acceptable_eta_minutes: int = 45

    def requires_hitl(self, action: str) -> bool:
        return any(t.value == action for t in self.hitl_triggers)

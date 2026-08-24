"""Normalization — raw offers -> comparable NormalizedOffers.

Computes the all-in TRUE price and a composite confidence (authority tier x
recency decay). Money stays Decimal throughout; we quantize to paise only at the
end. Confidence drives later abstention.
"""

from __future__ import annotations

import time
from decimal import ROUND_HALF_UP, Decimal

from app.bootstrap.domain_profile import DomainProfile
from app.models import AuthorityTier, NormalizedOffer, RawOffer

_PAISE = Decimal("0.01")
_TIER_SCORE = {AuthorityTier.TIER_1: 1.0, AuthorityTier.TIER_2: 0.8, AuthorityTier.TIER_3: 0.5}


def compute_true_price(offer: RawOffer) -> Decimal:
    """All-in price the user actually pays: item + tax + delivery + surge - membership."""
    total = (
        offer.base_price
        + offer.tax
        + offer.delivery_fee
        + offer.surge
        - offer.membership_discount
    )
    if total < 0:
        total = Decimal("0")
    return total.quantize(_PAISE, rounding=ROUND_HALF_UP)


def _recency_factor(captured_at: float, half_life_s: int, now: float) -> float:
    age = max(0.0, now - captured_at)
    return 0.5 ** (age / half_life_s) if half_life_s > 0 else 1.0


def compute_confidence(offer: RawOffer, profile: DomainProfile, now: float) -> float:
    """Composite confidence = tier score x price-recency x availability."""
    tier = _TIER_SCORE.get(offer.source_tier, 0.5)
    recency = _recency_factor(
        offer.captured_at, profile.recency_decay_half_lives["price"], now
    )
    avail = 1.0 if offer.available else 0.2
    return round(tier * recency * avail, 3)


def normalize_offers(
    offers: list[RawOffer], profile: DomainProfile, now: float | None = None
) -> list[NormalizedOffer]:
    now = now if now is not None else time.time()
    stale_after = profile.recency_decay_half_lives["price"]
    normalized: list[NormalizedOffer] = []
    for o in offers:
        true_price = compute_true_price(o)
        normalized.append(
            NormalizedOffer(
                platform=o.platform,
                kind=o.kind,
                item_name=o.item_name,
                unit=o.unit,
                veg=o.veg,
                restaurant=o.restaurant,
                restaurant_distance_km=o.restaurant_distance_km,
                available=o.available,
                eta_minutes=o.eta_minutes,
                rating=o.rating,
                offer_text=o.offer_text,
                base_price=o.base_price,
                tax=o.tax,
                delivery_fee=o.delivery_fee,
                surge=o.surge,
                membership_discount=o.membership_discount,
                true_price=true_price,
                confidence=compute_confidence(o, profile, now),
                stale=(now - o.captured_at) > stale_after,
                source_tier=o.source_tier,
                captured_at=o.captured_at,
            )
        )
    return normalized

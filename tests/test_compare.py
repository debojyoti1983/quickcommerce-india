"""Unit tests for ranking and the cheapest/fastest/best-rated picks."""

import time
from decimal import Decimal

from app.engine.compare import build_comparison
from app.models import AuthorityTier, ConnectorKind, NormalizedOffer


def _n(platform, price, eta, rating, available=True, conf=1.0) -> NormalizedOffer:
    p = Decimal(str(price))
    return NormalizedOffer(
        platform=platform, kind=ConnectorKind.GROCERY, item_name="Amul Milk 500ml",
        available=available, eta_minutes=eta, rating=rating,
        base_price=p, tax=Decimal("0"), delivery_fee=Decimal("0"),
        surge=Decimal("0"), membership_discount=Decimal("0"), true_price=p,
        confidence=conf, stale=False, source_tier=AuthorityTier.TIER_1,
        captured_at=time.time(),
    )


def test_cheapest_fastest_best_rated():
    offers = [
        _n("BigBasket", 47, 120, 4.5),
        _n("Zepto", 52, 9, 4.5),
        _n("Blinkit", 49, 11, 4.6),
    ]
    c = build_comparison("milk", offers)
    assert c.cheapest.platform == "BigBasket"
    assert c.fastest.platform == "Zepto"
    assert c.best_rated.platform == "Blinkit"


def test_unavailable_excluded_from_ranking():
    offers = [_n("Blinkit", 49, 11, 4.6), _n("FlipkartMinutes", 30, 18, 4.2, available=False)]
    c = build_comparison("milk", offers)
    assert len(c.available) == 1
    assert len(c.unavailable) == 1
    assert c.cheapest.platform == "Blinkit"  # the ₹30 one is out of stock


def test_confidence_penalises_overall_score():
    # Confidence is a multiplicative penalty on the ranking score: a low-trust
    # offer's overall score is scaled down by its confidence. (The hard guardrail
    # against acting on low-trust data is abstention — see test_recommend.py.)
    offers = [_n("Sketchy", 20, 5, 4.9, conf=0.2), _n("Blinkit", 49, 11, 4.6, conf=1.0)]
    c = build_comparison("milk", offers)
    sketchy = next(s for s in c.available if s.offer.platform == "Sketchy")
    # Sketchy is best on every raw axis (raw ~1.0) but scaled by its 0.2 confidence.
    assert sketchy.overall_score == 0.2

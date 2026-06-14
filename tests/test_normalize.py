"""Unit tests for true-price computation and confidence."""

import time
from decimal import Decimal

from app.bootstrap.domain_profile import DomainProfile
from app.engine.normalize import compute_confidence, compute_true_price, normalize_offers
from app.models import AuthorityTier, ConnectorKind, RawOffer


def _offer(**kw) -> RawOffer:
    base = dict(
        platform="Blinkit", kind=ConnectorKind.GROCERY, item_name="Amul Milk 500ml",
        base_price=Decimal("34"), tax=Decimal("0"), delivery_fee=Decimal("15"),
        surge=Decimal("0"), membership_discount=Decimal("0"), available=True,
        eta_minutes=11, rating=4.6, source_tier=AuthorityTier.TIER_1,
        captured_at=time.time(),
    )
    base.update(kw)
    return RawOffer(**base)


def test_true_price_is_all_in():
    o = _offer(base_price=Decimal("249"), tax=Decimal("12.45"),
               delivery_fee=Decimal("35"), surge=Decimal("20"),
               membership_discount=Decimal("35"))
    # 249 + 12.45 + 35 + 20 - 35 = 281.45
    assert compute_true_price(o) == Decimal("281.45")


def test_true_price_never_negative():
    o = _offer(base_price=Decimal("10"), membership_discount=Decimal("999"))
    assert compute_true_price(o) == Decimal("0.00")


def test_confidence_tier1_fresh_is_high():
    profile = DomainProfile()
    now = time.time()
    c = compute_confidence(_offer(source_tier=AuthorityTier.TIER_1, captured_at=now), profile, now)
    assert c == 1.0


def test_confidence_unavailable_is_penalised():
    profile = DomainProfile()
    now = time.time()
    c = compute_confidence(_offer(available=False, captured_at=now), profile, now)
    assert c < 0.55  # would trigger abstention


def test_normalize_sets_true_price_and_confidence():
    profile = DomainProfile()
    out = normalize_offers([_offer()], profile)
    assert out[0].true_price == Decimal("49.00")  # 34 + 15
    assert 0.0 <= out[0].confidence <= 1.0

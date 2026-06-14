"""Tests for the recommendation + abstention guardrail."""

import time
from decimal import Decimal

from app.bootstrap.domain_profile import DomainProfile
from app.engine.compare import build_comparison
from app.engine.recommend import recommend
from app.memory.claim_graph import ClaimGraph
from app.models import AuthorityTier, ConnectorKind, NormalizedOffer


def _n(platform, price, conf, available=True) -> NormalizedOffer:
    p = Decimal(str(price))
    return NormalizedOffer(
        platform=platform, kind=ConnectorKind.GROCERY, item_name="Amul Milk 500ml",
        available=available, eta_minutes=11, rating=4.5,
        base_price=p, tax=Decimal("0"), delivery_fee=Decimal("0"),
        surge=Decimal("0"), membership_discount=Decimal("0"), true_price=p,
        confidence=conf, stale=False, source_tier=AuthorityTier.TIER_1,
        captured_at=time.time(),
    )


def test_abstains_when_top_option_below_threshold():
    profile = DomainProfile()  # threshold 0.55
    comparison = build_comparison("milk", [_n("Sketchy", 20, conf=0.2)])
    rec = recommend(comparison, profile, ClaimGraph())
    assert rec.abstained is True
    assert "threshold" in (rec.abstain_reason or "")


def test_abstains_when_nothing_available():
    profile = DomainProfile()
    comparison = build_comparison("milk", [_n("Blinkit", 49, conf=1.0, available=False)])
    rec = recommend(comparison, profile, ClaimGraph())
    assert rec.abstained is True


def test_recommends_with_evidence_when_confident():
    profile = DomainProfile()
    comparison = build_comparison("milk", [_n("Blinkit", 49, conf=1.0), _n("Zepto", 52, conf=1.0)])
    rec = recommend(comparison, profile, ClaimGraph())
    assert rec.abstained is False
    assert rec.best is not None
    assert rec.because  # has [BECAUSE] reasoning
    assert rec.evidence  # has cited [EVIDENCE] claims
    assert rec.confidence_label in {"high", "medium"}

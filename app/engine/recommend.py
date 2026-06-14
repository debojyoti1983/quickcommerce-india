"""Recommendation — choose a best option + alternatives, explanation-first.

Emits the auditable [BECAUSE] / [EVIDENCE] / [CONFIDENCE] structure mandated by
the domain rules, records every cited fact in the Claim Graph, and ABSTAINS
rather than guessing when confidence is below the profile threshold.
"""

from __future__ import annotations

import time
from typing import Optional

from pydantic import BaseModel

from app.bootstrap.domain_profile import DomainProfile
from app.engine.compare import Comparison, ScoredOffer
from app.memory.claim_graph import ClaimGraph
from app.models import AuthorityTier, NormalizedOffer


class EvidenceSource(BaseModel):
    """Human-readable provenance for the figures behind a recommendation."""

    platform: str
    source_label: str  # plain-English source type (from the authority tier)
    freshness: str  # plain-English "how fresh" (from the capture timestamp)
    tier: int  # 1..3, for the curious / for styling
    facts: list[str]  # ["Price ₹295.95", "41 min delivery", "4.4★ rating", "In stock"]


class Recommendation(BaseModel):
    query: str
    abstained: bool = False
    abstain_reason: Optional[str] = None

    best: Optional[ScoredOffer] = None
    alternatives: list[ScoredOffer] = []

    because: list[str] = []
    evidence: list[EvidenceSource] = []  # friendly provenance, shown by default
    audit_claims: list[str] = []  # raw Claim Graph lines, tucked behind "audit trail"
    confidence_value: float = 0.0
    confidence_label: str = "low"
    assumptions: list[str] = []
    missing_data: list[str] = []


_SOURCE_LABEL = {
    AuthorityTier.TIER_1: "Live price",
    AuthorityTier.TIER_2: "Catalog listing",
    AuthorityTier.TIER_3: "Cached estimate",
}


def _label(value: float) -> str:
    if value >= 0.75:
        return "high"
    if value >= 0.55:
        return "medium"
    return "low"


def _money(o: NormalizedOffer) -> str:
    return f"₹{o.true_price}"


def _freshness(captured_at: float, now: float) -> str:
    age = max(0.0, now - captured_at)
    if age < 90:
        return "just now"
    if age < 3600:
        return f"{int(age // 60)} min ago"
    if age < 86400:
        return f"{int(age // 3600)} hr ago"
    return f"{int(age // 86400)} days ago"


def _evidence_source(o: NormalizedOffer, now: float) -> EvidenceSource:
    facts = [f"Price ₹{o.true_price}"]
    if o.eta_minutes is not None:
        facts.append(f"{o.eta_minutes} min delivery")
    if o.rating is not None:
        facts.append(f"{o.rating}★ rating")
    facts.append("In stock" if o.available else "Out of stock")
    return EvidenceSource(
        platform=o.platform,
        source_label=_SOURCE_LABEL.get(o.source_tier, "Unverified"),
        freshness=_freshness(o.captured_at, now),
        tier=int(o.source_tier),
        facts=facts,
    )


def recommend(
    comparison: Comparison,
    profile: DomainProfile,
    claim_graph: ClaimGraph,
    *,
    assumptions: Optional[list[str]] = None,
    missing_data: Optional[list[str]] = None,
) -> Recommendation:
    assumptions = list(assumptions or [])
    missing = list(missing_data or [])

    # Record every offer (available + unavailable) as auditable claims.
    cited: dict[str, list[str]] = {}
    for so in comparison.available:
        cited[so.offer.platform] = claim_graph.record_offer(
            _to_raw_like(so.offer), str(so.offer.true_price)
        )
    for o in comparison.unavailable:
        claim_graph.record_offer(_to_raw_like(o), str(o.true_price))

    if comparison.unavailable:
        missing.append(
            "Out of stock: "
            + ", ".join(f"{o.platform} ({o.item_name})" for o in comparison.unavailable)
        )

    # Abstain if nothing is available at all.
    if not comparison.available:
        return Recommendation(
            query=comparison.query,
            abstained=True,
            abstain_reason="No available options across the live platforms for this query.",
            missing_data=missing,
            assumptions=assumptions,
            confidence_label="low",
        )

    best = comparison.available[0]
    conf = best.offer.confidence

    # Abstain if even the best option is below the confidence threshold.
    if conf < profile.abstention_confidence_threshold:
        return Recommendation(
            query=comparison.query,
            abstained=True,
            abstain_reason=(
                f"Top option confidence {conf:.2f} is below the {profile.abstention_confidence_threshold:.2f} "
                "threshold (stale or low-authority data). I can't confirm this reliably."
            ),
            best=best,
            missing_data=missing,
            assumptions=assumptions,
            confidence_value=conf,
            confidence_label=_label(conf),
        )

    # Build the [BECAUSE] reasoning.
    b = best.offer
    because = [
        f"Best overall on {b.platform}: {b.item_name} at {_money(b)} all-in"
        + (f", ETA {b.eta_minutes} min" if b.eta_minutes is not None else "")
        + (f", rated {b.rating}★" if b.rating is not None else "")
        + " — best balance of price, speed, and rating."
    ]
    if comparison.cheapest and comparison.cheapest.platform != b.platform:
        because.append(
            f"Cheapest is {comparison.cheapest.platform} at {_money(comparison.cheapest)}, "
            f"but it trades off speed/rating."
        )
    if comparison.fastest and comparison.fastest.platform != b.platform:
        because.append(
            f"Fastest is {comparison.fastest.platform} at {comparison.fastest.eta_minutes} min."
        )
    if b.offer_text:
        because.append(f"Active offer applied: {b.offer_text}.")

    # Alternatives = the distinct cheapest / fastest / best-rated picks.
    alt_platforms = set()
    alternatives: list[ScoredOffer] = []
    for so in comparison.available[1:]:
        if so.offer.platform not in alt_platforms:
            alternatives.append(so)
            alt_platforms.add(so.offer.platform)
        if len(alternatives) >= 3:
            break

    # [EVIDENCE] — friendly provenance for the chosen option, plus the raw
    # Claim Graph lines kept behind an "audit trail" for anyone who wants them.
    now = time.time()
    evidence = [_evidence_source(b, now)]
    audit_claims = [
        claim_graph.by_id(cid).as_evidence()
        for cid in cited.get(b.platform, [])
        if claim_graph.by_id(cid)
    ]

    return Recommendation(
        query=comparison.query,
        best=best,
        alternatives=alternatives,
        because=because,
        evidence=evidence,
        audit_claims=audit_claims,
        confidence_value=conf,
        confidence_label=_label(conf),
        assumptions=assumptions,
        missing_data=missing,
    )


def _to_raw_like(o: NormalizedOffer):
    """Adapter so ClaimGraph.record_offer can read a NormalizedOffer uniformly."""
    from app.models import RawOffer

    return RawOffer(
        platform=o.platform,
        kind=o.kind,
        item_name=o.item_name,
        unit=o.unit,
        veg=o.veg,
        base_price=o.base_price,
        tax=o.tax,
        delivery_fee=o.delivery_fee,
        surge=o.surge,
        membership_discount=o.membership_discount,
        available=o.available,
        eta_minutes=o.eta_minutes,
        rating=o.rating,
        offer_text=o.offer_text,
        source_tier=o.source_tier,
        captured_at=o.captured_at,
    )

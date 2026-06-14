"""Comparison — rank normalized offers along the axes that matter.

Produces the unified view: cheapest, fastest, best-rated, and a weighted
"best overall" score. Only AVAILABLE offers are ranked; unavailable ones are
surfaced separately so the assistant can be transparent about them.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.models import NormalizedOffer


class ScoredOffer(BaseModel):
    offer: NormalizedOffer
    overall_score: float  # 0..1, higher is better


class Comparison(BaseModel):
    query: str
    available: list[ScoredOffer]  # ranked best-overall first
    unavailable: list[NormalizedOffer]
    cheapest: Optional[NormalizedOffer] = None
    fastest: Optional[NormalizedOffer] = None
    best_rated: Optional[NormalizedOffer] = None


def _norm(value: float, lo: float, hi: float, *, invert: bool) -> float:
    if hi == lo:
        return 1.0
    pos = (value - lo) / (hi - lo)
    return 1.0 - pos if invert else pos


def build_comparison(
    query: str,
    offers: list[NormalizedOffer],
    *,
    weights: tuple[float, float, float] = (0.5, 0.3, 0.2),  # price, eta, rating
) -> Comparison:
    available = [o for o in offers if o.available]
    unavailable = [o for o in offers if not o.available]

    if not available:
        return Comparison(query=query, available=[], unavailable=unavailable)

    prices = [float(o.true_price) for o in available]
    etas = [float(o.eta_minutes) for o in available if o.eta_minutes is not None]
    ratings = [o.rating for o in available if o.rating is not None]

    p_lo, p_hi = min(prices), max(prices)
    e_lo, e_hi = (min(etas), max(etas)) if etas else (0.0, 0.0)
    r_lo, r_hi = (min(ratings), max(ratings)) if ratings else (0.0, 0.0)
    w_price, w_eta, w_rating = weights

    scored: list[ScoredOffer] = []
    for o in available:
        s_price = _norm(float(o.true_price), p_lo, p_hi, invert=True)
        s_eta = _norm(float(o.eta_minutes), e_lo, e_hi, invert=True) if o.eta_minutes is not None else 0.5
        s_rating = _norm(o.rating, r_lo, r_hi, invert=False) if o.rating is not None else 0.5
        raw = w_price * s_price + w_eta * s_eta + w_rating * s_rating
        # Down-weight low-confidence offers so stale/Tier-3 data can't "win".
        scored.append(ScoredOffer(offer=o, overall_score=round(raw * o.confidence, 4)))

    scored.sort(key=lambda s: s.overall_score, reverse=True)

    cheapest = min(available, key=lambda o: o.true_price)
    rated = [o for o in available if o.rating is not None]
    timed = [o for o in available if o.eta_minutes is not None]
    return Comparison(
        query=query,
        available=scored,
        unavailable=unavailable,
        cheapest=cheapest,
        fastest=min(timed, key=lambda o: o.eta_minutes) if timed else None,
        best_rated=max(rated, key=lambda o: o.rating) if rated else None,
    )

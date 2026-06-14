"""Claim Graph — every datum recorded with source, value, tier, and timestamp.

The recommender cites claim ids in its [EVIDENCE] block so a human can audit
exactly where each price/ETA came from.
"""

from __future__ import annotations

import time

from pydantic import BaseModel, Field

from app.models import AuthorityTier, RawOffer


class Claim(BaseModel):
    id: str
    platform: str
    subject: str  # e.g. "Amul Taaza Toned Milk 500ml"
    predicate: str  # e.g. "true_price_inr" | "eta_minutes" | "rating"
    value: str
    tier: AuthorityTier
    captured_at: float

    def as_evidence(self) -> str:
        from datetime import datetime, timezone

        ts = datetime.fromtimestamp(self.captured_at, tz=timezone.utc).strftime("%H:%M UTC")
        return (
            f"[{self.id}] {self.platform}: {self.subject} {self.predicate}={self.value} "
            f"(T{int(self.tier)}, captured {ts})"
        )


class ClaimGraph(BaseModel):
    claims: list[Claim] = Field(default_factory=list)
    _seq: int = 0

    def record_offer(self, offer: RawOffer, true_price: str) -> list[str]:
        """Record the comparison-relevant facts for an offer. Returns claim ids."""
        facts = {
            "true_price_inr": true_price,
            "eta_minutes": str(offer.eta_minutes) if offer.eta_minutes is not None else "unknown",
            "rating": str(offer.rating) if offer.rating is not None else "unknown",
            "available": str(offer.available),
        }
        ids: list[str] = []
        for predicate, value in facts.items():
            self._seq += 1
            cid = f"C{self._seq}"
            self.claims.append(
                Claim(
                    id=cid,
                    platform=offer.platform,
                    subject=offer.item_name,
                    predicate=predicate,
                    value=value,
                    tier=offer.source_tier,
                    captured_at=offer.captured_at or time.time(),
                )
            )
            ids.append(cid)
        return ids

    def by_id(self, cid: str) -> Claim | None:
        return next((c for c in self.claims if c.id == cid), None)

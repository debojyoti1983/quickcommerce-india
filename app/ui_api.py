"""UI-facing search endpoint.

Returns the comparison in the exact shape the React UI consumes (platform *ids*,
numeric prices, an `item` object per result). It reuses the real orchestrator —
single source of truth — and just reshapes the output. Kept separate from
/api/compare so the internal contract and the UI contract can evolve apart.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.bootstrap.geo import LocationMatch, list_known_cities, resolve_from_latlng
from app.bootstrap.registry import CONNECTORS
from app.coordination.orchestrator import run_query
from app.models import NormalizedOffer, UserContext

router = APIRouter()

# Display name (what the engine stores on offers) -> platform id (what the UI keys on).
_DISPLAY_TO_ID = {c.display_name: c.name for c in CONNECTORS}


class LocationResolveRequest(BaseModel):
    # Bounds match what navigator.geolocation can ever report — reject anything
    # else at the boundary rather than trust client-supplied floats blindly.
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


@router.post("/api/location/resolve", response_model=LocationMatch)
async def location_resolve(req: LocationResolveRequest) -> LocationMatch:
    """Cold-start bootstrap step: browser geolocation coords -> nearest known
    metro's pincode/city. No third-party geocoder call (see app/bootstrap/geo.py)."""
    return resolve_from_latlng(req.lat, req.lng)


@router.get("/api/location/cities")
async def location_cities() -> dict:
    """Manual-entry fallback list, shown when geolocation is denied/unsupported."""
    return {"cities": list_known_cities()}


class UISearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=120)
    memberships: list[str] = Field(default_factory=list, max_length=10)
    platforms: list[str] = Field(default_factory=list, max_length=20)
    veg_only: bool = False
    pincode: str = Field(default="560001", pattern=r"^\d{6}$")
    city: str = Field(default="Bengaluru", max_length=60)


def _offer(o: NormalizedOffer) -> dict:
    return {
        "platform": _DISPLAY_TO_ID.get(o.platform, o.platform),
        "item_name": o.item_name,
        "unit": o.unit,
        "kind": o.kind.value,
        "veg": o.veg,
        "restaurant": o.restaurant,
        "available": o.available,
        "eta_minutes": o.eta_minutes,
        "rating": o.rating,
        "offer_text": o.offer_text,
        "true_price": float(o.true_price),  # UI does math/formatting on a number
        "membership_applied": o.membership_discount > 0,
    }


@router.post("/api/ui/search")
async def ui_search(req: UISearchRequest) -> dict:
    # The UI always sends its selected platform ids; an empty list means the user
    # deselected every app -> no results (matches the UI's "none" affordance).
    if not req.platforms:
        return {"results": []}

    user = UserContext(
        pincode=req.pincode, city=req.city, veg_only=req.veg_only, memberships=req.memberships
    )
    resp = await run_query(req.query, user, platforms=req.platforms)

    results = []
    for res in resp.results:
        comp = res.comparison
        first = (
            comp.available[0].offer if comp.available
            else (comp.unavailable[0] if comp.unavailable else None)
        )
        rec = res.recommendation
        results.append({
            "key": res.item_name,
            "item": {
                "name": res.item_name,
                "unit": first.unit if first else None,
                "kind": res.kind,
                "veg": first.veg if first else None,
            },
            "comparison": {
                "available": [
                    {"offer": _offer(s.offer), "overall_score": s.overall_score}
                    for s in comp.available
                ],
                "unavailable": [_offer(o) for o in comp.unavailable],
                "cheapest": _offer(comp.cheapest) if comp.cheapest else None,
                "fastest": _offer(comp.fastest) if comp.fastest else None,
                "best_rated": _offer(comp.best_rated) if comp.best_rated else None,
            },
            "recommendation": {
                "abstained": rec.abstained,
                "abstain_reason": rec.abstain_reason,
                "best": {"offer": _offer(rec.best.offer)} if rec.best else None,
                "alternatives": [{"offer": _offer(s.offer)} for s in rec.alternatives],
                "because": rec.because,
                "evidence": [
                    {
                        "platform": _DISPLAY_TO_ID.get(ev.platform, ev.platform),
                        "source_label": ev.source_label,
                        "freshness": ev.freshness,
                        "tier": ev.tier,
                        "facts": ev.facts,
                    }
                    for ev in rec.evidence
                ],
                "confidence_value": rec.confidence_value,
                "confidence_label": rec.confidence_label,
            },
        })
    return {"results": results, "note": resp.note}

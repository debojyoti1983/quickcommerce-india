"""The query orchestrator — wires every module into one async pipeline."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from pydantic import BaseModel

from app.bootstrap.registry import CONNECTORS
from app.bootstrap.snapshot import ContextSnapshot, bootstrap_context
from app.config import get_settings
from app.connectors.mock_connector import MockConnector
from app.connectors.mock_data import match_score
from app.engine.compare import Comparison, build_comparison
from app.engine.normalize import normalize_offers
from app.engine.recommend import Recommendation, recommend
from app.llm.client import narrate_recommendation
from app.memory.claim_graph import ClaimGraph
from app.models import RawOffer, UserContext

logger = logging.getLogger("qcommerce.orchestrator")


class QueryResult(BaseModel):
    item_name: str
    kind: str
    comparison: Comparison
    recommendation: Recommendation
    narration: str
    narration_source: str  # "claude" | "deterministic"


class QueryResponse(BaseModel):
    query: str
    user: UserContext
    snapshot: ContextSnapshot
    results: list[QueryResult]
    note: str | None = None


async def _search_one(spec, query: str, user: UserContext, timeout_s: float) -> list[RawOffer]:
    try:
        return await asyncio.wait_for(MockConnector(spec).search(query, user), timeout_s)
    except (asyncio.TimeoutError, Exception) as exc:  # noqa: BLE001 — drop this platform, keep going
        logger.warning("search failed on %s (%s)", spec.name, type(exc).__name__)
        return []


async def run_query(
    query: str, user: UserContext, platforms: list[str] | None = None
) -> QueryResponse:
    settings = get_settings()
    snapshot = await bootstrap_context(user)
    claim_graph = ClaimGraph()

    # Restrict to the user-selected platforms (empty/None = all). Filtering by
    # connector `name` keeps the food/grocery routing intact.
    selected = [c for c in CONNECTORS if not platforms or c.name in platforms]

    # Parallel fan-out across the selected connectors (food connectors simply
    # return [] for grocery queries and vice versa — natural routing).
    offer_lists = await asyncio.gather(
        *(_search_one(spec, query, user, settings.request_timeout_s) for spec in selected)
    )
    all_offers: list[RawOffer] = [o for lst in offer_lists for o in lst]

    if not all_offers:
        from app.connectors.mock_data import catalog_item_names

        return QueryResponse(
            query=query,
            user=user,
            snapshot=snapshot,
            results=[],
            note=(
                f"No match for “{query}” in the demo catalog. This build uses "
                "simulated data — the real Swiggy/Zomato/Blinkit apps have no public "
                "search API — so only a fixed set of items is searchable: "
                + ", ".join(catalog_item_names())
                + "."
            ),
        )

    # Group like-for-like by canonical item name, then run the pipeline per item.
    grouped: dict[str, list[RawOffer]] = defaultdict(list)
    for o in all_offers:
        grouped[o.item_name].append(o)

    assumptions = _assumptions(user)
    results: list[QueryResult] = []
    for item_name, raw in grouped.items():
        normalized = normalize_offers(raw, snapshot.profile)
        comparison = build_comparison(item_name, normalized)
        rec = recommend(
            comparison,
            snapshot.profile,
            claim_graph,
            assumptions=assumptions,
            missing_data=list(snapshot.missing_data),
        )
        narration = narrate_recommendation(rec, user)
        results.append(
            QueryResult(
                item_name=item_name,
                kind=raw[0].kind.value,
                comparison=comparison,
                recommendation=rec,
                narration=narration["text"],
                narration_source=narration["source"],
            )
        )

    # Most-relevant item first: how specific a match it is for the query
    # (so "chicken momos" outranks "Chicken Curry", which only shares the
    # generic word "chicken") — platform count is just the tiebreaker.
    results.sort(
        key=lambda r: (
            match_score(query, r.item_name),
            len(r.comparison.available) + len(r.comparison.unavailable),
        ),
        reverse=True,
    )
    return QueryResponse(query=query, user=user, snapshot=snapshot, results=results)


def _assumptions(user: UserContext) -> list[str]:
    out = [
        "Prices/ETAs are simulated demo data, not live platform values.",
        f"Coverage, ETAs, and delivery fees for {user.city} ({user.pincode}) follow this "
        "demo's per-city model, not live platform coverage.",
    ]
    if user.veg_only:
        out.append("Veg-only filter applied — non-veg items excluded.")
    if user.memberships:
        out.append("Membership benefits applied for: " + ", ".join(user.memberships) + ".")
    else:
        out.append("No memberships assumed (no Swiggy One / Zomato Gold / BB Star discounts).")
    return out

"""MockConnector — serves one platform's data from the seed catalog.

Async like a real adapter (simulated sub-second latency). Never raises on
'not found' / 'out of stock'; returns empty/unavailable so the orchestrator can
degrade gracefully. Swap this for a real adapter behind app/connectors/base.py.
"""

from __future__ import annotations

import asyncio
import time

from app.bootstrap.registry import ConnectorSpec
from app.connectors.base import Serviceability
from app.connectors.mock_data import CATALOG, PLATFORM_OFFERS, match_catalog_keys
from app.models import RawOffer, UserContext

# Deterministic, tiny simulated network latency per platform (seconds).
_LATENCY = {
    "swiggy": 0.04, "zomato": 0.05, "blinkit": 0.03, "zepto": 0.03,
    "instamart": 0.04, "bigbasket": 0.06, "flipkart_minutes": 0.05,
    "amazon_fresh": 0.06,
}


class MockConnector:
    def __init__(self, spec: ConnectorSpec) -> None:
        self.spec = spec
        self.name = spec.name

    async def serviceability(self, user: UserContext) -> Serviceability:
        await asyncio.sleep(_LATENCY.get(self.name, 0.04))
        offers = PLATFORM_OFFERS.get(self.name, {})
        etas = [o.get("eta_minutes") for o in offers.values() if o.get("eta_minutes")]
        return Serviceability(
            serviceable=bool(offers),
            baseline_eta_minutes=min(etas) if etas else None,
            store_id=f"{self.name}-{user.pincode}",
        )

    async def search(self, query: str, user: UserContext) -> list[RawOffer]:
        await asyncio.sleep(_LATENCY.get(self.name, 0.04))
        platform_offers = PLATFORM_OFFERS.get(self.name, {})
        membership_active = bool(self.spec.membership and self.spec.membership in user.memberships)
        captured = time.time()

        results: list[RawOffer] = []
        for key in match_catalog_keys(query):
            params = platform_offers.get(key)
            if params is None:
                continue
            item = CATALOG[key]

            # Respect veg-only for food items.
            if user.veg_only and item["veg"] is False:
                continue

            # Membership discount only applies if the user actually holds it.
            discount = params.get("membership_discount", 0) if membership_active else 0

            results.append(
                RawOffer(
                    platform=self.spec.display_name,
                    kind=item["kind"],
                    item_name=item["name"],
                    unit=item["unit"],
                    veg=item["veg"],
                    base_price=params["base_price"],
                    tax=params.get("tax", 0),
                    delivery_fee=params.get("delivery_fee", 0),
                    surge=params.get("surge", 0),
                    membership_discount=discount,
                    available=params.get("available", True),
                    eta_minutes=params.get("eta_minutes"),
                    rating=params.get("rating"),
                    offer_text=params.get("offer_text"),
                    store_id=f"{self.name}-{user.pincode}",
                    source_tier=params["tier"],
                    captured_at=captured,
                )
            )
        return results

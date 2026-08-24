"""Per-city platform coverage for the simulated catalog.

Real quick-commerce coverage is famously uneven: dark-store networks (Blinkit,
Zepto, Instamart, BigBasket) cluster hard in a handful of metros, while the two
food-delivery apps (Swiggy, Zomato) have much broader reach, and Amazon Fresh /
Flipkart Minutes lean hardest on existing metro warehouses. This module encodes
that *shape* for the demo catalog — it is a modelled assumption for a fixed list
of cities, not scraped or live coverage data (see app/connectors/mock_data.py's
own "simulated, not live" note). Unknown/unlisted cities fall back to full
metro-style coverage so a typo or an unmapped town never silently zeroes out
every result.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

# Platform `name`s — must match app/bootstrap/registry.py.
_ALL_PLATFORMS = frozenset({
    "swiggy", "zomato", "blinkit", "zepto", "instamart",
    "bigbasket", "flipkart_minutes", "amazon_fresh",
})
# Amazon Fresh and Flipkart Minutes are the first to drop off outside the
# biggest metro warehouse footprints.
_MINUS_LONG_TAIL = _ALL_PLATFORMS - {"amazon_fresh", "flipkart_minutes"}
# Only the fastest-scaling dark-store networks plus both food-delivery apps
# reach smaller cities in this simulated model.
_SMALL_CITY_PLATFORMS = frozenset({"swiggy", "zomato", "blinkit", "zepto"})


class CityProfile(BaseModel):
    # Platform names that actually deliver to this city.
    platforms: frozenset[str]
    # Every ETA minute figure is multiplied by this — smaller markets run
    # thinner delivery networks and slower dark stores.
    eta_multiplier: float = 1.0
    # Every delivery fee is multiplied by this — a rough proxy for lower
    # delivery density outside the biggest metros.
    fee_multiplier: Decimal = Decimal("1.0")


_METRO = CityProfile(platforms=_ALL_PLATFORMS, eta_multiplier=1.0, fee_multiplier=Decimal("1.0"))
_TIER2 = CityProfile(platforms=_MINUS_LONG_TAIL, eta_multiplier=1.25, fee_multiplier=Decimal("1.15"))
_TIER3 = CityProfile(platforms=_SMALL_CITY_PLATFORMS, eta_multiplier=1.6, fee_multiplier=Decimal("1.3"))

# Keyed on the same city names app/bootstrap/geo.py resolves to, so the
# location picker and this coverage model always agree.
CITY_PROFILES: dict[str, CityProfile] = {
    # Tier-1 metros — full 8-platform coverage, no ETA/fee penalty.
    "Bengaluru": _METRO, "Mumbai": _METRO, "Delhi": _METRO, "Hyderabad": _METRO,
    "Chennai": _METRO, "Kolkata": _METRO, "Pune": _METRO,
    # Tier-2 — everything except the two platforms leaning hardest on metro warehouses.
    "Ahmedabad": _TIER2, "Jaipur": _TIER2, "Lucknow": _TIER2, "Chandigarh": _TIER2,
    "Kochi": _TIER2, "Indore": _TIER2, "Nagpur": _TIER2, "Coimbatore": _TIER2,
    "Visakhapatnam": _TIER2,
    # Tier-3 — only the fastest-scaling dark-store + food-delivery networks.
    "Bhopal": _TIER3, "Surat": _TIER3, "Patna": _TIER3, "Guwahati": _TIER3,
}

# Unknown/unlisted city -> don't silently zero out every result.
DEFAULT_PROFILE = _METRO


def profile_for(city: str) -> CityProfile:
    return CITY_PROFILES.get(city, DEFAULT_PROFILE)

"""Which restaurant is serving a dish, within range of the selected location.

The catalog (mock_data.py) models dishes at the platform level only — there's
no real per-restaurant menu data behind this demo. To answer "which restaurant,
how far away" without fabricating a fact we can't back up, each dish+platform
combo gets a handful of deterministic, simulated outlet locations scattered a
few km around the selected city's centroid (or the user's precise coordinates,
when browser geolocation supplied them). We then genuinely filter to outlets
within ``DEFAULT_RADIUS_KM`` of the reference point using the same great-circle
math as the rest of the app (see app/bootstrap/geo.py) and surface the nearest
match with its real distance — if nothing modeled falls within range, we say
so (return None) rather than showing a restaurant that isn't actually nearby.
This is a modelled/simulated pairing, same as the rest of the app's demo data,
not a live restaurant listing.
"""

from __future__ import annotations

import hashlib
import math

from pydantic import BaseModel

from app.bootstrap.geo import centroid_for, haversine_km

DEFAULT_RADIUS_KM = 10.0

# One representative, genuinely multi-city Indian restaurant chain per food
# dish in the catalog (see app/connectors/mock_data.py CATALOG). Food-only —
# grocery items have no `restaurant` (the platform itself is the seller).
_CHAIN_FOR_DISH: dict[str, str] = {
    "paneer_butter_masala": "Punjab Grill",
    "chicken_biryani": "Paradise Biryani",
    "masala_dosa": "Sagar Ratna",
    "chicken_curry": "Barbeque Nation",
    "butter_chicken": "Punjab Grill",
    "veg_biryani": "Behrouz Biryani",
    "dal_makhani": "Punjab Grill",
    "chole_bhature": "Haldiram's",
    "mutton_biryani": "Paradise Biryani",
    "egg_biryani": "Paradise Biryani",
    "veg_fried_rice": "Mainland China",
    "pav_bhaji": "Bikanervala",
    "rajma_chawal": "Sagar Ratna",
    "palak_paneer": "Punjab Grill",
    "chicken_65": "Barbeque Nation",
    "gulab_jamun": "Haldiram's",
}

# Real, well-known neighbourhoods for the original 20 cities — used when we
# have one, so those cities keep a specific place name rather than a
# generic compass direction.
_LOCALITIES: dict[str, list[str]] = {
    "Bengaluru": ["Indiranagar", "Koramangala", "HSR Layout", "Whitefield"],
    "Mumbai": ["Andheri", "Bandra", "Powai", "Malad"],
    "Delhi": ["Connaught Place", "Saket", "Rajouri Garden", "Dwarka"],
    "Hyderabad": ["Gachibowli", "Banjara Hills", "Kukatpally"],
    "Chennai": ["Anna Nagar", "T Nagar", "Velachery"],
    "Kolkata": ["Salt Lake", "Park Street", "Gariahat"],
    "Pune": ["Kothrud", "Viman Nagar", "Hinjewadi"],
    "Ahmedabad": ["Navrangpura", "Satellite", "Bopal"],
    "Jaipur": ["Malviya Nagar", "Vaishali Nagar", "C-Scheme"],
    "Lucknow": ["Hazratganj", "Gomti Nagar", "Aliganj"],
    "Chandigarh": ["Sector 17", "Sector 22", "Sector 35"],
    "Kochi": ["Kakkanad", "MG Road", "Edappally"],
    "Indore": ["Vijay Nagar", "Palasia", "Rajwada"],
    "Nagpur": ["Sadar", "Dharampeth", "Sitabuldi"],
    "Bhopal": ["MP Nagar", "New Market", "Arera Colony"],
    "Surat": ["Adajan", "Vesu", "Citylight"],
    "Patna": ["Boring Road", "Kankarbagh", "Rajendra Nagar"],
    "Guwahati": ["Fancy Bazar", "Zoo Road", "GS Road"],
    "Coimbatore": ["RS Puram", "Gandhipuram", "Peelamedu"],
    "Visakhapatnam": ["MVP Colony", "Dwaraka Nagar", "Siripuram"],
}

_COMPASS = ["North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West"]
_FALLBACK_CENTROID = (12.9716, 77.5946)  # Bengaluru — only used if a city name isn't in geo.py at all


class RestaurantMatch(BaseModel):
    name: str  # "<chain> - <locality>"
    distance_km: float


def _pick(options: list[str], *parts: str) -> str:
    """Deterministic pick — stable across requests, varies with each part."""
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return options[int(digest, 16) % len(options)]


def _destination_point(lat: float, lng: float, bearing_deg: float, distance_km: float) -> tuple[float, float]:
    """Standard spherical "destination point given distance and bearing"."""
    r = 6371.0
    brng = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lng1 = math.radians(lng)
    d_r = distance_km / r
    lat2 = math.asin(math.sin(lat1) * math.cos(d_r) + math.cos(lat1) * math.sin(d_r) * math.cos(brng))
    lng2 = lng1 + math.atan2(
        math.sin(brng) * math.sin(d_r) * math.cos(lat1), math.cos(d_r) - math.sin(lat1) * math.sin(lat2)
    )
    return math.degrees(lat2), math.degrees(lng2)


def _synthetic_outlets(base_lat: float, base_lng: float, seed: str, count: int = 4) -> list[tuple[float, float, float]]:
    """Deterministic candidate outlet points 1-9 km from the city centroid, in
    varied directions — same seed always yields the same outlets, so results
    don't flicker between identical searches."""
    outlets = []
    for i in range(count):
        digest = hashlib.sha256(f"{seed}|{i}".encode()).hexdigest()
        bearing = int(digest[:8], 16) % 360
        distance = 1.0 + (int(digest[8:16], 16) % 800) / 100.0  # 1.00 .. 8.99 km
        lat, lng = _destination_point(base_lat, base_lng, bearing, distance)
        outlets.append((lat, lng, bearing))
    return outlets


def restaurant_for(
    catalog_key: str, platform: str, city: str, *, lat: float | None = None, lng: float | None = None,
    radius_km: float = DEFAULT_RADIUS_KM,
) -> RestaurantMatch | None:
    """The nearest simulated outlet of this dish's chain within ``radius_km``
    of the reference point, or None if nothing modelled falls in range —
    abstaining rather than claiming a restaurant is nearby when it isn't.

    Reference point: the caller's precise lat/lng when browser geolocation
    supplied one, otherwise the selected city's centroid (so a manually-picked
    city still reliably finds outlets generated around that same centroid).
    """
    chain = _CHAIN_FOR_DISH.get(catalog_key)
    if chain is None:
        return None  # grocery — the platform itself is the seller

    base = centroid_for(city) or _FALLBACK_CENTROID
    ref_lat = lat if lat is not None else base[0]
    ref_lng = lng if lng is not None else base[1]

    best: tuple[float, float] | None = None  # (distance_km, bearing)
    for outlet_lat, outlet_lng, bearing in _synthetic_outlets(base[0], base[1], f"{catalog_key}|{platform}|{city}"):
        distance = haversine_km(ref_lat, ref_lng, outlet_lat, outlet_lng)
        if distance <= radius_km and (best is None or distance < best[0]):
            best = (distance, bearing)

    if best is None:
        return None

    distance, bearing = best
    localities = _LOCALITIES.get(city)
    if localities:
        # Keep continuity with the previously curated pairing for these cities.
        locality = _pick(localities, catalog_key, platform, city)
    else:
        locality = f"{_COMPASS[round(bearing / 45) % 8]} {city}"
    return RestaurantMatch(name=f"{chain} - {locality}", distance_km=round(distance, 1))

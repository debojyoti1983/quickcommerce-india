"""Which restaurant is serving a dish, in the selected city.

The catalog (mock_data.py) models dishes at the platform level only — there's
no real per-restaurant menu data behind this demo. To answer "which restaurant
is this coming from" without fabricating a fact we can't back up, we pair a
well-known, multi-city restaurant chain per dish with a real neighbourhood in
the selected city, picked deterministically (same dish+platform+city always
resolves to the same restaurant — no flicker between searches). This is a
modelled/simulated pairing, same as the rest of the app's demo data, not a
live restaurant listing.
"""

from __future__ import annotations

import hashlib

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
}

# A handful of real, well-known neighbourhoods per city the location picker
# resolves to (see app/bootstrap/geo.py) — enough to make "restaurant near you"
# feel local without claiming block-level accuracy.
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
_DEFAULT_LOCALITIES = _LOCALITIES["Bengaluru"]  # unknown city -> still show *something*


def _pick(options: list[str], *parts: str) -> str:
    """Deterministic pick — stable across requests, varies with each part."""
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return options[int(digest, 16) % len(options)]


def restaurant_for(catalog_key: str, platform: str, city: str) -> str | None:
    """The restaurant serving this dish in the selected city, or None for
    anything not in the food chain table (i.e. every grocery item)."""
    chain = _CHAIN_FOR_DISH.get(catalog_key)
    if chain is None:
        return None
    localities = _LOCALITIES.get(city, _DEFAULT_LOCALITIES)
    locality = _pick(localities, catalog_key, platform, city)
    return f"{chain} - {locality}"

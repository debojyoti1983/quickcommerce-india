"""Lat/lng -> pincode + city resolution (the "bootstrap" cold-start step).

No external geocoding API is called: this is a demo aggregator (see README —
all connector data is simulated), and reaching out to a third-party geocoder
would mean a new outbound dependency, a new SSRF surface, and possibly a paid
API key for a feature that only needs city-level precision. Instead we resolve
against an allowlisted table of Indian city centroids (at least one per state/
union territory, plus the major commercial hubs) and pick the nearest by
great-circle distance. Good enough to seed pincode/city for the comparison
engine; the user can always override manually from a searchable list of the
same cities (see app.web.static.location.jsx).
"""

from __future__ import annotations

import math
import re
from typing import NamedTuple

from pydantic import BaseModel

# Rough bounding box for India (mainland + islands) — used only to flag
# out-of-area detections; we still return the nearest known city either way
# so the UI always has *something* sensible to show.
_INDIA_LAT_RANGE = (6.0, 37.5)
_INDIA_LNG_RANGE = (68.0, 97.5)

# A representative pincode per city — not exhaustive (India has ~19,000
# pincodes), just broad enough for a demo: at least one city per state/union
# territory, plus the major commercial hubs within the bigger states. lat/lng
# are approximate city centroids.
KNOWN_LOCATIONS: list[dict] = [
    # Original 7 metros + first-wave coverage.
    {"city": "Bengaluru", "pincode": "560001", "lat": 12.9716, "lng": 77.5946},
    {"city": "Mumbai", "pincode": "400001", "lat": 19.0760, "lng": 72.8777},
    {"city": "Delhi", "pincode": "110001", "lat": 28.6139, "lng": 77.2090},
    {"city": "Hyderabad", "pincode": "500001", "lat": 17.3850, "lng": 78.4867},
    {"city": "Chennai", "pincode": "600001", "lat": 13.0827, "lng": 80.2707},
    {"city": "Kolkata", "pincode": "700001", "lat": 22.5726, "lng": 88.3639},
    {"city": "Pune", "pincode": "411001", "lat": 18.5204, "lng": 73.8567},
    {"city": "Ahmedabad", "pincode": "380001", "lat": 23.0225, "lng": 72.5714},
    {"city": "Jaipur", "pincode": "302001", "lat": 26.9124, "lng": 75.7873},
    {"city": "Lucknow", "pincode": "226001", "lat": 26.8467, "lng": 80.9462},
    {"city": "Chandigarh", "pincode": "160001", "lat": 30.7333, "lng": 76.7794},
    {"city": "Kochi", "pincode": "682001", "lat": 9.9312, "lng": 76.2673},
    {"city": "Indore", "pincode": "452001", "lat": 22.7196, "lng": 75.8577},
    {"city": "Nagpur", "pincode": "440001", "lat": 21.1458, "lng": 79.0882},
    {"city": "Bhopal", "pincode": "462001", "lat": 23.2599, "lng": 77.4126},
    {"city": "Surat", "pincode": "395001", "lat": 21.1702, "lng": 72.8311},
    {"city": "Patna", "pincode": "800001", "lat": 25.5941, "lng": 85.1376},
    {"city": "Guwahati", "pincode": "781001", "lat": 26.1445, "lng": 91.7362},
    {"city": "Coimbatore", "pincode": "641001", "lat": 11.0168, "lng": 76.9558},
    {"city": "Visakhapatnam", "pincode": "530001", "lat": 17.6868, "lng": 83.2185},
    # State/UT capitals not yet covered above.
    {"city": "Thiruvananthapuram", "pincode": "695001", "lat": 8.5241, "lng": 76.9366},
    {"city": "Bhubaneswar", "pincode": "751001", "lat": 20.2961, "lng": 85.8245},
    {"city": "Raipur", "pincode": "492001", "lat": 21.2514, "lng": 81.6296},
    {"city": "Ranchi", "pincode": "834001", "lat": 23.3441, "lng": 85.3096},
    {"city": "Dehradun", "pincode": "248001", "lat": 30.3165, "lng": 78.0322},
    {"city": "Shimla", "pincode": "171001", "lat": 31.1048, "lng": 77.1734},
    {"city": "Srinagar", "pincode": "190001", "lat": 34.0837, "lng": 74.7973},
    {"city": "Jammu", "pincode": "180001", "lat": 32.7266, "lng": 74.8570},
    {"city": "Panaji", "pincode": "403001", "lat": 15.4909, "lng": 73.8278},
    {"city": "Agartala", "pincode": "799001", "lat": 23.8315, "lng": 91.2868},
    {"city": "Imphal", "pincode": "795001", "lat": 24.8170, "lng": 93.9368},
    {"city": "Shillong", "pincode": "793001", "lat": 25.5788, "lng": 91.8933},
    {"city": "Aizawl", "pincode": "796001", "lat": 23.7271, "lng": 92.7176},
    {"city": "Kohima", "pincode": "797001", "lat": 25.6751, "lng": 94.1086},
    {"city": "Itanagar", "pincode": "791111", "lat": 27.0844, "lng": 93.6053},
    {"city": "Gangtok", "pincode": "737101", "lat": 27.3389, "lng": 88.6065},
    {"city": "Puducherry", "pincode": "605001", "lat": 11.9416, "lng": 79.8083},
    {"city": "Port Blair", "pincode": "744101", "lat": 11.6234, "lng": 92.7265},
    # Major commercial cities within already-covered states.
    {"city": "Amritsar", "pincode": "143001", "lat": 31.6340, "lng": 74.8723},
    {"city": "Ludhiana", "pincode": "141001", "lat": 30.9010, "lng": 75.8573},
    {"city": "Gurugram", "pincode": "122001", "lat": 28.4595, "lng": 77.0266},
    {"city": "Faridabad", "pincode": "121001", "lat": 28.4089, "lng": 77.3178},
    {"city": "Varanasi", "pincode": "221001", "lat": 25.3176, "lng": 82.9739},
    {"city": "Kanpur", "pincode": "208001", "lat": 26.4499, "lng": 80.3319},
    {"city": "Agra", "pincode": "282001", "lat": 27.1767, "lng": 78.0081},
    {"city": "Noida", "pincode": "201301", "lat": 28.5355, "lng": 77.3910},
    {"city": "Prayagraj", "pincode": "211001", "lat": 25.4358, "lng": 81.8463},
    {"city": "Jamshedpur", "pincode": "831001", "lat": 22.8046, "lng": 86.2029},
    {"city": "Vadodara", "pincode": "390001", "lat": 22.3072, "lng": 73.1812},
    {"city": "Rajkot", "pincode": "360001", "lat": 22.3039, "lng": 70.8022},
    {"city": "Vijayawada", "pincode": "520001", "lat": 16.5062, "lng": 80.6480},
    {"city": "Tirupati", "pincode": "517501", "lat": 13.6288, "lng": 79.4192},
    {"city": "Warangal", "pincode": "506002", "lat": 17.9689, "lng": 79.5941},
    {"city": "Mysuru", "pincode": "570001", "lat": 12.2958, "lng": 76.6394},
    {"city": "Mangaluru", "pincode": "575001", "lat": 12.9141, "lng": 74.8560},
    {"city": "Hubballi", "pincode": "580020", "lat": 15.3647, "lng": 75.1240},
    {"city": "Madurai", "pincode": "625001", "lat": 9.9252, "lng": 78.1198},
    {"city": "Tiruchirappalli", "pincode": "620001", "lat": 10.7905, "lng": 78.7047},
    {"city": "Salem", "pincode": "636001", "lat": 11.6643, "lng": 78.1460},
    {"city": "Thane", "pincode": "400601", "lat": 19.2183, "lng": 72.9781},
    {"city": "Nashik", "pincode": "422001", "lat": 19.9975, "lng": 73.7898},
    {"city": "Aurangabad", "pincode": "431001", "lat": 19.8762, "lng": 75.3433},
    {"city": "Jabalpur", "pincode": "482001", "lat": 23.1815, "lng": 79.9864},
    {"city": "Gwalior", "pincode": "474001", "lat": 26.2183, "lng": 78.1828},
    {"city": "Cuttack", "pincode": "753001", "lat": 20.4625, "lng": 85.8828},
    {"city": "Siliguri", "pincode": "734001", "lat": 26.7271, "lng": 88.3953},
    {"city": "Durgapur", "pincode": "713201", "lat": 23.5204, "lng": 87.3119},
    {"city": "Muzaffarpur", "pincode": "842001", "lat": 26.1225, "lng": 85.3906},
    {"city": "Gaya", "pincode": "823001", "lat": 24.7955, "lng": 84.9994},
    {"city": "Jodhpur", "pincode": "342001", "lat": 26.2389, "lng": 73.0243},
    {"city": "Udaipur", "pincode": "313001", "lat": 24.5854, "lng": 73.7125},
    {"city": "Dibrugarh", "pincode": "786001", "lat": 27.4728, "lng": 94.9120},
]

# Beyond this radius the "nearest known city" is too far away to call
# serviceable — it's a demo signal to the UI ("we don't cover this area yet"),
# not a hard block.
_SERVICEABLE_RADIUS_KM = 300.0
_EARTH_RADIUS_KM = 6371.0


class LocationMatch(BaseModel):
    city: str
    pincode: str
    matched_label: str
    distance_km: float
    serviceable: bool
    in_india: bool


class _City(NamedTuple):
    city: str
    pincode: str
    lat: float
    lng: float


_CITIES = [_City(m["city"], m["pincode"], m["lat"], m["lng"]) for m in KNOWN_LOCATIONS]
_BY_NAME = {c.city: c for c in _CITIES}


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km. Shared by geo resolution and the
    restaurant-radius filter (app/connectors/restaurants.py) — one formula,
    one place to get it right."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def centroid_for(city: str) -> tuple[float, float] | None:
    """This city's approximate lat/lng centroid, or None if it's not in our
    coverage table (see app/connectors/restaurants.py for the fallback)."""
    c = _BY_NAME.get(city)
    return (c.lat, c.lng) if c else None


# A real Indian PIN code is exactly 6 digits and never starts with 0.
_PINCODE_RE = re.compile(r"^[1-9]\d{5}$")

# Shared-prefix length with a known city's representative PIN -> an honest
# confidence-proportional distance. India's PIN structure genuinely encodes
# geography this way, but each level covers a lot more ground than it might
# sound like: digit 1 (zone) spans several states; digits 1-2 (postal
# circle/sub-zone) is typically a whole state or a large chunk of one; only
# digits 1-3 (sorting district) narrows to a real city/district (tens of km).
# Verified against real pincodes far from any of our 72 known cities (e.g.
# Solapur, Jalandhar, Nainital) — a 1-2 digit match alone was landing on a
# plausible-*sounding* but potentially 100s of km wrong city while still
# being marked "serviceable". Only a 3+ digit match gets a confident,
# serviceable distance; 1-2 digit matches deliberately exceed
# _SERVICEABLE_RADIUS_KM below so they surface as an explicit low-confidence
# guess (see the UI's "results may be approximate" warning) rather than a
# silently wrong "sure thing".
_PREFIX_MATCH_DISTANCE_KM = {6: 0.0, 5: 2.0, 4: 8.0, 3: 20.0, 2: 320.0, 1: 500.0}


def resolve_from_pincode(pincode: str) -> LocationMatch | None:
    """Approximate city resolution from a PIN code's own structure — matched
    against the longest shared prefix with one of our known cities' PINs.
    Returns None only for a malformed code (not 6 digits, or starting with 0,
    which no real Indian PIN does); a syntactically valid but unrecognized
    code still resolves, just with low confidence (serviceable=False)."""
    if not _PINCODE_RE.match(pincode):
        return None

    best_city, best_prefix = _CITIES[0], -1
    for c in _CITIES:
        shared = 0
        for a, b in zip(pincode, c.pincode):
            if a != b:
                break
            shared += 1
        if shared > best_prefix:
            best_city, best_prefix = c, shared

    distance = _PREFIX_MATCH_DISTANCE_KM.get(best_prefix, 800.0)
    return LocationMatch(
        city=best_city.city,
        pincode=pincode,
        matched_label=best_city.city,
        distance_km=distance,
        serviceable=distance <= _SERVICEABLE_RADIUS_KM,
        in_india=True,  # syntactically valid Indian PIN code
    )


def resolve_from_latlng(lat: float, lng: float) -> LocationMatch:
    """Nearest known city by great-circle distance. Never raises — worst case
    is a distant match flagged ``serviceable=False``; the caller/UI decides
    whether to fall back to manual entry."""
    nearest = min(_CITIES, key=lambda c: haversine_km(lat, lng, c.lat, c.lng))
    distance = haversine_km(lat, lng, nearest.lat, nearest.lng)
    in_india = _INDIA_LAT_RANGE[0] <= lat <= _INDIA_LAT_RANGE[1] and _INDIA_LNG_RANGE[0] <= lng <= _INDIA_LNG_RANGE[1]
    return LocationMatch(
        city=nearest.city,
        pincode=nearest.pincode,
        matched_label=nearest.city,
        distance_km=round(distance, 1),
        serviceable=distance <= _SERVICEABLE_RADIUS_KM,
        in_india=in_india,
    )


def list_known_cities() -> list[dict]:
    """Sorted city list for the manual location picker — every city here is
    serviceable by at least the fast-scaling platform set (see
    app/connectors/city_profiles.py), so any of them is a valid pick."""
    return sorted(({"city": c.city, "pincode": c.pincode} for c in _CITIES), key=lambda c: c["city"])

"""Tests for geo-aware, radius-filtered restaurant assignment on food offers."""

import asyncio

from app.bootstrap.geo import centroid_for, haversine_km
from app.bootstrap.registry import CONNECTORS
from app.connectors.mock_connector import MockConnector
from app.connectors.restaurants import restaurant_for
from app.models import UserContext


def _spec(name: str):
    return next(c for c in CONNECTORS if c.name == name)


def _search(platform: str, query: str, city: str, **kwargs):
    return asyncio.run(MockConnector(_spec(platform)).search(query, UserContext(city=city, **kwargs)))


def test_grocery_offers_have_no_restaurant():
    assert restaurant_for("amul_milk_500ml", "blinkit", "Bengaluru") is None
    offers = _search("blinkit", "Amul milk", "Bengaluru")
    assert offers and all(o.restaurant is None for o in offers)


def test_food_offers_get_a_restaurant_with_a_real_distance():
    match = restaurant_for("chicken_biryani", "swiggy", "Bengaluru")
    assert match is not None
    assert match.distance_km <= 10.0
    offers = _search("swiggy", "chicken biryani", "Bengaluru")
    assert offers and all(o.restaurant and o.restaurant_distance_km is not None for o in offers)
    assert all(o.restaurant_distance_km <= 10.0 for o in offers)


def test_restaurant_locality_varies_by_city_but_stable_for_same_inputs():
    bengaluru = restaurant_for("chicken_biryani", "swiggy", "Bengaluru")
    mumbai = restaurant_for("chicken_biryani", "swiggy", "Mumbai")
    again = restaurant_for("chicken_biryani", "swiggy", "Bengaluru")
    assert bengaluru == again  # deterministic, not random per call
    assert bengaluru.name != mumbai.name  # but does depend on the selected city
    # Same chain (brand), different neighbourhood.
    chain = bengaluru.name.split(" - ")[0]
    assert mumbai.name.startswith(chain + " - ")


def test_a_city_without_curated_localities_gets_a_directional_label():
    # Jodhpur has no entry in restaurants.py's curated _LOCALITIES table —
    # it should still resolve, just with a compass-direction label.
    match = restaurant_for("chicken_biryani", "swiggy", "Jodhpur")
    assert match is not None
    assert " Jodhpur" in match.name


def test_precise_coordinates_narrow_to_a_real_10km_radius():
    # Standing right on the city centroid: every outlet (generated 1-9 km from
    # that same centroid) must report a real distance <= 10 km.
    lat, lng = centroid_for("Bengaluru")
    near = restaurant_for("chicken_biryani", "swiggy", "Bengaluru", lat=lat, lng=lng)
    assert near is not None
    assert near.distance_km <= 10.0

    # Standing 50 km away from the city centroid in a fixed direction: no
    # simulated outlet (all within ~9 km of the centroid) can be within a
    # 10 km radius of us -> honestly abstain instead of showing a "nearby"
    # restaurant that isn't.
    far_lat, far_lng = lat + 0.5, lng  # ~55 km north
    far = restaurant_for("chicken_biryani", "swiggy", "Bengaluru", lat=far_lat, lng=far_lng)
    assert far is None


def test_unknown_city_still_resolves_via_fallback_centroid():
    assert restaurant_for("chicken_biryani", "swiggy", "Neverland") is not None


def test_haversine_matches_known_distance_scale():
    # Sanity check the shared distance helper against a known-ish pair
    # (Bengaluru <-> Mumbai is roughly 840 km as the crow flies).
    b = centroid_for("Bengaluru")
    m = centroid_for("Mumbai")
    d = haversine_km(*b, *m)
    assert 800 <= d <= 900

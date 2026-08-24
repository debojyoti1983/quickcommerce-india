"""Tests for per-city restaurant assignment on food offers."""

import asyncio

from app.bootstrap.registry import CONNECTORS
from app.connectors.mock_connector import MockConnector
from app.connectors.restaurants import restaurant_for
from app.models import UserContext


def _spec(name: str):
    return next(c for c in CONNECTORS if c.name == name)


def _search(platform: str, query: str, city: str):
    return asyncio.run(MockConnector(_spec(platform)).search(query, UserContext(city=city)))


def test_grocery_offers_have_no_restaurant():
    assert restaurant_for("amul_milk_500ml", "blinkit", "Bengaluru") is None
    offers = _search("blinkit", "Amul milk", "Bengaluru")
    assert offers and all(o.restaurant is None for o in offers)


def test_food_offers_get_a_restaurant():
    assert restaurant_for("chicken_biryani", "swiggy", "Bengaluru") is not None
    offers = _search("swiggy", "chicken biryani", "Bengaluru")
    assert offers and all(o.restaurant for o in offers)


def test_restaurant_locality_varies_by_city_but_stable_for_same_inputs():
    bengaluru = restaurant_for("chicken_biryani", "swiggy", "Bengaluru")
    mumbai = restaurant_for("chicken_biryani", "swiggy", "Mumbai")
    again = restaurant_for("chicken_biryani", "swiggy", "Bengaluru")
    assert bengaluru == again  # deterministic, not random per call
    assert bengaluru != mumbai  # but does depend on the selected city
    # Same chain (brand), different neighbourhood.
    chain = bengaluru.split(" - ")[0]
    assert mumbai.startswith(chain + " - ")


def test_unknown_city_still_returns_a_restaurant():
    assert restaurant_for("chicken_biryani", "swiggy", "Neverland") is not None

"""Tests for per-city platform coverage / ETA-fee scaling in the mock connectors."""

import asyncio
from decimal import Decimal

from app.bootstrap.registry import CONNECTORS
from app.connectors.city_profiles import profile_for
from app.connectors.mock_connector import MockConnector
from app.models import UserContext


def _spec(name: str):
    return next(c for c in CONNECTORS if c.name == name)


def _search(platform: str, query: str, city: str):
    user = UserContext(city=city, pincode="000000")
    return asyncio.run(MockConnector(_spec(platform)).search(query, user))


def test_unknown_city_falls_back_to_full_metro_coverage():
    profile = profile_for("Some Town Nobody Mapped")
    assert profile.platforms == profile_for("Bengaluru").platforms
    assert profile.eta_multiplier == 1.0


def test_metro_city_gets_every_platform():
    offers = _search("amazon_fresh", "Amul milk", "Bengaluru")
    assert offers, "Amazon Fresh should serve a metro like Bengaluru"


def test_small_city_drops_the_long_tail_platforms():
    # Patna is Tier-3 in the coverage model: only swiggy/zomato/blinkit/zepto.
    assert _search("amazon_fresh", "Amul milk", "Patna") == []
    assert _search("flipkart_minutes", "Amul milk", "Patna") == []
    assert _search("bigbasket", "Amul milk", "Patna") == []
    assert _search("instamart", "Amul milk", "Patna") == []
    # But the fast dark-store networks and food apps still do.
    assert _search("blinkit", "Amul milk", "Patna")
    assert _search("zepto", "Amul milk", "Patna")


def test_eta_and_delivery_fee_scale_up_outside_metros():
    metro = _search("blinkit", "Amul milk", "Bengaluru")[0]
    small = _search("blinkit", "Amul milk", "Patna")[0]
    assert small.eta_minutes > metro.eta_minutes
    assert small.delivery_fee > metro.delivery_fee
    # Exact scaling per city_profiles.py: Patna is 1.6x ETA, 1.3x fee.
    assert small.eta_minutes == round(metro.eta_minutes * 1.6)
    assert small.delivery_fee == (metro.delivery_fee * Decimal("1.3")).quantize(Decimal("0.01"))


def test_serviceability_reflects_city_coverage():
    reachable = asyncio.run(
        MockConnector(_spec("amazon_fresh")).serviceability(UserContext(city="Bengaluru"))
    )
    out_of_area = asyncio.run(
        MockConnector(_spec("amazon_fresh")).serviceability(UserContext(city="Patna"))
    )
    assert reachable.serviceable is True
    assert out_of_area.serviceable is False

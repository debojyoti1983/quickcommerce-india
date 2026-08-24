"""Tests for lat/lng -> pincode/city resolution (no external geocoder)."""

from app.bootstrap.geo import list_known_cities, resolve_from_latlng


def test_resolves_to_nearest_known_metro():
    # Right in the middle of Bengaluru.
    match = resolve_from_latlng(12.9716, 77.5946)
    assert match.city == "Bengaluru"
    assert match.pincode == "560001"
    assert match.serviceable is True
    assert match.in_india is True
    assert match.distance_km < 1


def test_nearby_point_still_resolves_within_service_radius():
    # A few km off Mumbai's centroid should still land on Mumbai.
    match = resolve_from_latlng(19.10, 72.90)
    assert match.city == "Mumbai"
    assert match.serviceable is True


def test_far_outside_india_is_flagged_unserviceable_but_never_raises():
    # London — nearest metro is very far away and outside the India bbox.
    match = resolve_from_latlng(51.5074, -0.1278)
    assert match.serviceable is False
    assert match.in_india is False
    assert match.pincode  # still returns *some* usable fallback


def test_known_cities_cover_every_metro_with_valid_pincodes():
    cities = list_known_cities()
    assert len(cities) >= 15
    assert all(len(c["pincode"]) == 6 and c["pincode"].isdigit() for c in cities)
    assert cities == sorted(cities, key=lambda c: c["city"])

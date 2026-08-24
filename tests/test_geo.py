"""Tests for lat/lng and pincode -> pincode/city resolution (no external geocoder)."""

from app.bootstrap.geo import list_known_cities, resolve_from_latlng, resolve_from_pincode


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


def test_exact_known_pincode_resolves_with_full_confidence():
    match = resolve_from_pincode("560001")
    assert match.city == "Bengaluru"
    assert match.distance_km == 0.0
    assert match.serviceable is True


def test_nearby_unknown_pincode_still_resolves_via_shared_prefix():
    # 560034 isn't one of our exact known codes, but shares Bengaluru's
    # 3-digit sorting-district prefix ("560") — should still land there,
    # confidently, rather than falling back to a distant "nearest" guess.
    match = resolve_from_pincode("560034")
    assert match.city == "Bengaluru"
    assert match.serviceable is True


def test_pincode_with_no_shared_prefix_is_low_confidence_but_never_raises():
    # A syntactically valid PIN that shares nothing meaningful with any known
    # city's prefix should still resolve to *something*, just unserviceable.
    match = resolve_from_pincode("999999")
    assert match is not None
    assert match.in_india is True


def test_malformed_pincodes_are_rejected():
    assert resolve_from_pincode("12345") is None  # too short
    assert resolve_from_pincode("1234567") is None  # too long
    assert resolve_from_pincode("012345") is None  # no real Indian PIN starts with 0
    assert resolve_from_pincode("abcdef") is None  # not digits


def test_weak_prefix_match_is_flagged_low_confidence_not_claimed_confident():
    # Real pincodes nowhere near any of our 72 known cities (Solapur is
    # ~250km from Pune; Jalandhar sits between Amritsar and Ludhiana) only
    # share 1-2 digits with their nearest known-city guess. That guess should
    # still come back (so restaurant suggestions have *something* to anchor
    # on), but must never be reported as a confident, serviceable match —
    # regression coverage for a real bug: these used to come back
    # serviceable=True despite being a coin-flip guess 100s of km off.
    solapur = resolve_from_pincode("413001")
    assert solapur.serviceable is False

    jalandhar = resolve_from_pincode("144001")
    assert jalandhar.serviceable is False


def test_known_metro_satellite_district_overrides_the_raw_prefix_guess():
    # Regression for a real reported bug: 712xxx (Hooghly district towns —
    # Chandannagar, Serampore, Bandel) is genuinely part of the Kolkata
    # Metropolitan Area, but shares more raw digits with Durgapur's PIN
    # (713xxx) than with Kolkata's (700xxx) — the generic longest-shared-
    # prefix heuristic picked Durgapur, confidently, which is wrong.
    match = resolve_from_pincode("712233")
    assert match.city == "Kolkata"
    assert match.serviceable is True


def test_district_level_match_still_stays_confident():
    # A genuine 3+ digit shared prefix (same sorting district) should still
    # resolve confidently — only 1-2 digit matches get downgraded.
    match = resolve_from_pincode("560103")  # Bengaluru area, not the exact known 560001
    assert match.city == "Bengaluru"
    assert match.serviceable is True

"""Tests for the simulated account / membership detection (no credentials)."""

from app.accounts.mock_accounts import active_memberships, detect_accounts


def test_detect_returns_status_for_every_platform():
    statuses = detect_accounts()
    assert len(statuses) == 8
    assert all(s.connected for s in statuses)


def test_platforms_without_a_programme_report_no_membership():
    by_name = {s.platform: s for s in detect_accounts()}
    for name in ("blinkit", "zepto", "flipkart_minutes"):
        assert by_name[name].membership is None
        assert by_name[name].membership_active is False


def test_demo_profile_holds_a_realistic_mix():
    active = set(active_memberships())
    assert "Swiggy One" in active and "Zomato Gold" in active and "Prime" in active
    assert "BB Star" not in active  # demo user is deliberately NOT a BB Star member


def test_instamart_inherits_swiggy_one():
    by_name = {s.platform: s for s in detect_accounts()}
    # Instamart's programme is Swiggy One, which the demo user holds.
    assert by_name["instamart"].membership == "Swiggy One"
    assert by_name["instamart"].membership_active is True

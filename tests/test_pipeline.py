"""Integration tests for the end-to-end orchestrator (mock connectors, no LLM)."""

import asyncio

from app.coordination.orchestrator import run_query
from app.models import UserContext


def _run(query: str, user: UserContext):
    return asyncio.run(run_query(query, user))


def test_grocery_query_aggregates_multiple_platforms():
    resp = _run("Amul milk", UserContext())
    assert resp.results, "expected at least one item result"
    res = resp.results[0]
    platforms = {s.offer.platform for s in res.comparison.available}
    # Amul milk is carried by several grocery platforms.
    assert len(platforms) >= 4
    assert res.recommendation.best is not None
    assert res.recommendation.because


def test_veg_only_excludes_non_veg():
    resp = _run("chicken biryani", UserContext(veg_only=True))
    # veg_only must exclude every non-veg offer (e.g. Chicken Biryani), even if a
    # veg match like "Veg Biryani" surfaces from the shared "biryani" term.
    for r in resp.results:
        assert "Chicken" not in r.item_name
        for s in r.comparison.available:
            assert s.offer.veg is not False


def test_membership_lowers_effective_price():
    base = _run("paneer butter masala", UserContext())
    member = _run("paneer butter masala", UserContext(memberships=["Swiggy One"]))

    def swiggy_price(resp):
        for r in resp.results:
            for s in r.comparison.available:
                if s.offer.platform == "Swiggy":
                    return s.offer.true_price
        return None

    assert swiggy_price(member) < swiggy_price(base)


def test_platform_filter_restricts_comparison():
    resp = _run("Amul milk", UserContext())  # available on many platforms
    full = {s.offer.platform for s in resp.results[0].comparison.available}
    assert len(full) >= 4

    # Restrict to just Blinkit + Zepto.
    import asyncio
    from app.coordination.orchestrator import run_query
    limited = asyncio.run(run_query("Amul milk", UserContext(), platforms=["blinkit", "zepto"]))
    plats = {s.offer.platform for s in limited.results[0].comparison.available}
    assert plats == {"Blinkit", "Zepto"}


def test_bb_star_membership_lowers_bigbasket_price():
    import asyncio
    from app.coordination.orchestrator import run_query

    def bb_price(resp):
        for s in resp.results[0].comparison.available:
            if s.offer.platform == "BigBasket":
                return s.offer.true_price
        return None

    base = asyncio.run(run_query("Aashirvaad atta", UserContext()))
    member = asyncio.run(run_query("Aashirvaad atta", UserContext(memberships=["BB Star"])))
    assert bb_price(member) < bb_price(base)


def test_chicken_curry_now_resolves_on_food_apps():
    resp = _run("chicken curry", UserContext())
    assert resp.results, "chicken curry should now match the expanded catalog"
    platforms = {s.offer.platform for r in resp.results for s in r.comparison.available}
    assert {"Swiggy", "Zomato"} & platforms


def test_token_fallback_matches_near_miss():
    # 'chicken gravy' isn't a catalog item, but token overlap on 'chicken' rescues it.
    resp = _run("chicken gravy", UserContext())
    assert resp.results


def test_unknown_query_returns_helpful_note():
    resp = _run("unobtanium 9000", UserContext())
    assert resp.results == []
    assert resp.note and "demo catalog" in resp.note


def test_specific_dish_ranks_above_a_generically_shared_word_match():
    # Regression: as the catalog grew, several dishes share a generic word
    # ("chicken") without being related dishes at all. "chicken momos" used
    # to rank "Chicken Curry" first (it shares only "chicken") ahead of the
    # actual "Chicken Momos" match — results must lead with the specific,
    # near-exact match; the weaker generic-word match can still trail behind.
    resp = _run("chicken momos", UserContext())
    assert resp.results
    assert resp.results[0].item_name == "Chicken Momos (6 pcs)"


def test_related_variant_still_surfaces_as_a_secondary_match():
    # The existing "shared dish-type term" cross-match (biryani variants)
    # must still work — just not rank ahead of the exact match.
    resp = _run("chicken biryani", UserContext())
    names = [r.item_name for r in resp.results]
    assert names[0] == "Chicken Biryani"
    assert "Veg Biryani" in names


def test_out_of_stock_surfaced():
    # Flipkart Minutes lists Aashirvaad atta as out of stock in the seed data.
    resp = _run("Aashirvaad atta", UserContext())
    res = resp.results[0]
    assert any(o.platform == "Flipkart Minutes" for o in res.comparison.unavailable)

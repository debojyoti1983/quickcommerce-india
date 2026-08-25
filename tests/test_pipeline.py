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
    # "chicken biryani" now names exactly Chicken Biryani (see
    # test_exact_dish_name_matches_only_that_dish) - veg_only correctly
    # filters that dish's offers out entirely rather than substituting an
    # unrelated veg dish the user didn't ask for, so this resolves to no
    # results at all.
    resp = _run("chicken biryani", UserContext(veg_only=True))
    assert resp.results == []
    for r in resp.results:
        assert "Chicken" not in r.item_name
        for s in r.comparison.available:
            assert s.offer.veg is not False

    # veg_only still must exclude non-veg offers on a query that resolves to
    # more than one item (a bare category word, not a specific dish name).
    resp2 = _run("biryani", UserContext(veg_only=True))
    for r in resp2.results:
        assert "Chicken" not in r.item_name and "Mutton" not in r.item_name and "Egg" not in r.item_name
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


def test_exact_dish_name_matches_only_that_dish():
    # A full, specific dish name must resolve to exactly that dish - not
    # "Chicken Curry" (shares only "chicken") or "Veg Biryani" (shares only
    # "biryani"). Naming a specific dish should never pull in unrelated ones
    # that merely share a single word.
    resp = _run("chicken biryani", UserContext())
    names = [r.item_name for r in resp.results]
    assert names == ["Chicken Biryani"]

    resp2 = _run("kadai paneer", UserContext())
    assert [r.item_name for r in resp2.results] == ["Kadai Paneer"]

    resp3 = _run("chicken momos", UserContext())
    assert [r.item_name for r in resp3.results] == ["Chicken Momos (6 pcs)"]


def test_bare_category_word_still_browses_every_variant():
    # A single generic word (not a specific dish name) should still surface
    # every dish in that category - this is category browsing, not naming
    # one specific dish, so the broader match is still the right behavior.
    resp = _run("biryani", UserContext())
    names = {r.item_name for r in resp.results}
    assert {"Chicken Biryani", "Veg Biryani", "Mutton Biryani", "Egg Biryani"} <= names


def test_typo_still_falls_back_to_a_reasonable_match():
    # A multi-word query with a typo doesn't cover any single dish's full
    # name, so it must fall through to the broader substring/token matching
    # instead of returning nothing.
    resp = _run("chiken curry", UserContext())
    assert resp.results
    assert any(r.item_name == "Chicken Curry" for r in resp.results)


def test_out_of_stock_surfaced():
    # Flipkart Minutes lists Aashirvaad atta as out of stock in the seed data.
    resp = _run("Aashirvaad atta", UserContext())
    res = resp.results[0]
    assert any(o.platform == "Flipkart Minutes" for o in res.comparison.unavailable)

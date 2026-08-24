"""Data-integrity checks for the demo catalog + a broader-menu search smoke test.

Not "any dish on earth" (see mock_data.py's own docstring — no live platform
search API exists to back that), but the catalog should be broad enough that
typing a common dish doesn't dead-end, and every offer must reference a real
catalog item.
"""

from app.connectors.mock_data import CATALOG, PLATFORM_OFFERS, catalog_item_names, match_catalog_keys
from app.connectors.restaurants import _CHAIN_FOR_DISH
from app.models import ConnectorKind


def test_every_platform_offer_references_a_real_catalog_item():
    orphans = [
        (platform, key)
        for platform, offers in PLATFORM_OFFERS.items()
        for key in offers
        if key not in CATALOG
    ]
    assert orphans == []


def test_every_food_item_has_a_restaurant_chain_assigned():
    # Otherwise a food search would silently show no restaurant at all.
    food_keys = [k for k, item in CATALOG.items() if item["kind"] == ConnectorKind.FOOD]
    missing = [k for k in food_keys if k not in _CHAIN_FOR_DISH]
    assert missing == []


def test_catalog_is_broad_not_a_handful_of_fixed_dishes():
    assert len(CATALOG) >= 30
    food = sum(1 for i in CATALOG.values() if i["kind"] == ConnectorKind.FOOD)
    grocery = sum(1 for i in CATALOG.values() if i["kind"] == ConnectorKind.GROCERY)
    assert food >= 10 and grocery >= 10


def test_newly_added_dishes_are_searchable_by_plain_text():
    cases = {
        "mutton biryani": "mutton_biryani",
        "pav bhaji": "pav_bhaji",
        "chicken 65": "chicken_65",
        "gulab jamun": "gulab_jamun",
        "toor dal": "toor_dal_1kg",
        "sunflower oil": "sunflower_oil_1l",
        "curd": "curd_400g",
        "tata tea": "tata_tea_250g",
    }
    for query, expected_key in cases.items():
        assert expected_key in match_catalog_keys(query), query


def test_catalog_item_names_lists_every_item_for_the_no_match_note():
    names = catalog_item_names()
    assert len(names) == len(CATALOG)
    assert CATALOG["mutton_biryani"]["name"] in names

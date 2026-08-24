"""Realistic seed data for the mock connectors.

Hand-authored so cross-platform comparisons are meaningful (genuine price/ETA/
rating trade-offs, surge on one app, a stock-out on another, membership perks).
All money is in INR. This is simulated data — NOT live platform pricing.

To refresh: edit CATALOG (canonical items) and PLATFORM_OFFERS (per-platform
pricing). Keep keys in sync between the two.
"""

from __future__ import annotations

import re
from decimal import Decimal

from app.models import AuthorityTier, ConnectorKind

# --- canonical catalog ------------------------------------------------------
# key -> (display name, kind, unit, veg, search aliases)
CATALOG: dict[str, dict] = {
    "amul_milk_500ml": {
        "name": "Amul Taaza Toned Milk 500ml", "kind": ConnectorKind.GROCERY,
        "unit": "500 ml", "veg": None,
        "aliases": ["amul", "milk", "toned milk", "amul milk"],
    },
    "aashirvaad_atta_5kg": {
        "name": "Aashirvaad Whole Wheat Atta 5kg", "kind": ConnectorKind.GROCERY,
        "unit": "5 kg", "veg": None,
        "aliases": ["atta", "aashirvaad", "wheat", "flour"],
    },
    "tata_salt_1kg": {
        "name": "Tata Salt 1kg", "kind": ConnectorKind.GROCERY,
        "unit": "1 kg", "veg": None, "aliases": ["salt", "tata salt"],
    },
    "onion_1kg": {
        "name": "Onion 1kg", "kind": ConnectorKind.GROCERY,
        "unit": "1 kg", "veg": None, "aliases": ["onion", "pyaz", "kanda"],
    },
    "paneer_butter_masala": {
        "name": "Paneer Butter Masala", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True,
        "aliases": ["paneer", "paneer butter masala", "pbm", "paneer makhani"],
    },
    "chicken_biryani": {
        "name": "Chicken Biryani", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": False,
        "aliases": ["biryani", "chicken biryani", "biriyani"],
    },
    "masala_dosa": {
        "name": "Masala Dosa", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True, "aliases": ["dosa", "masala dosa"],
    },
    "chicken_curry": {
        "name": "Chicken Curry", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": False,
        "aliases": ["chicken curry", "curry", "chicken gravy", "murgh curry", "chicken"],
    },
    "butter_chicken": {
        "name": "Butter Chicken", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": False,
        "aliases": ["butter chicken", "murgh makhani", "chicken makhani", "chicken"],
    },
    "veg_biryani": {
        "name": "Veg Biryani", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True,
        "aliases": ["veg biryani", "vegetable biryani", "veg biriyani", "biryani"],
    },
    "dal_makhani": {
        "name": "Dal Makhani", "kind": ConnectorKind.FOOD,
        "unit": "1 bowl", "veg": True,
        "aliases": ["dal makhani", "dal", "daal", "dal makhni", "lentils"],
    },
    "chole_bhature": {
        "name": "Chole Bhature", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True,
        "aliases": ["chole bhature", "chole", "chhole", "bhature"],
    },
    "eggs_6": {
        "name": "Farm Eggs (6 pcs)", "kind": ConnectorKind.GROCERY,
        "unit": "6 pcs", "veg": False,
        "aliases": ["eggs", "egg", "anda", "ande"],
    },
    "bread": {
        "name": "Britannia Bread 400g", "kind": ConnectorKind.GROCERY,
        "unit": "400 g", "veg": True,
        "aliases": ["bread", "loaf", "sandwich bread"],
    },
    "basmati_rice_1kg": {
        "name": "India Gate Basmati Rice 1kg", "kind": ConnectorKind.GROCERY,
        "unit": "1 kg", "veg": None,
        "aliases": ["rice", "basmati", "basmati rice", "chawal"],
    },
    # -- broader food menu, so search isn't stuck on a handful of dishes --
    "mutton_biryani": {
        "name": "Mutton Biryani", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": False,
        "aliases": ["mutton biryani", "gosht biryani", "lamb biryani"],
    },
    "egg_biryani": {
        "name": "Egg Biryani", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": False,
        "aliases": ["egg biryani", "anda biryani"],
    },
    "veg_fried_rice": {
        "name": "Veg Fried Rice", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True,
        "aliases": ["veg fried rice", "vegetable fried rice", "fried rice"],
    },
    "pav_bhaji": {
        "name": "Pav Bhaji", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True,
        "aliases": ["pav bhaji", "pao bhaji"],
    },
    "rajma_chawal": {
        "name": "Rajma Chawal", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True,
        "aliases": ["rajma chawal", "rajma rice", "rajma"],
    },
    "palak_paneer": {
        "name": "Palak Paneer", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True,
        "aliases": ["palak paneer", "saag paneer", "spinach paneer"],
    },
    "chicken_65": {
        "name": "Chicken 65", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": False,
        "aliases": ["chicken 65", "chicken sixty five"],
    },
    "gulab_jamun": {
        "name": "Gulab Jamun (2 pcs)", "kind": ConnectorKind.FOOD,
        "unit": "2 pcs", "veg": True,
        "aliases": ["gulab jamun", "gulab jamoon", "dessert"],
    },
    # -- broader grocery aisle --
    "toor_dal_1kg": {
        "name": "Toor Dal 1kg", "kind": ConnectorKind.GROCERY,
        "unit": "1 kg", "veg": True,
        "aliases": ["toor dal", "arhar dal", "pigeon pea", "tuvar dal"],
    },
    "sugar_1kg": {
        "name": "Sugar 1kg", "kind": ConnectorKind.GROCERY,
        "unit": "1 kg", "veg": True, "aliases": ["sugar", "chini"],
    },
    "sunflower_oil_1l": {
        "name": "Sunflower Cooking Oil 1L", "kind": ConnectorKind.GROCERY,
        "unit": "1 L", "veg": True,
        "aliases": ["sunflower oil", "cooking oil", "edible oil", "oil"],
    },
    "curd_400g": {
        "name": "Curd 400g", "kind": ConnectorKind.GROCERY,
        "unit": "400 g", "veg": True, "aliases": ["curd", "yogurt", "dahi"],
    },
    "paneer_200g": {
        "name": "Paneer 200g", "kind": ConnectorKind.GROCERY,
        "unit": "200 g", "veg": True, "aliases": ["paneer", "cottage cheese"],
    },
    "potato_1kg": {
        "name": "Potato 1kg", "kind": ConnectorKind.GROCERY,
        "unit": "1 kg", "veg": True, "aliases": ["potato", "aloo", "batata"],
    },
    "tomato_1kg": {
        "name": "Tomato 1kg", "kind": ConnectorKind.GROCERY,
        "unit": "1 kg", "veg": True, "aliases": ["tomato", "tamatar"],
    },
    "tata_tea_250g": {
        "name": "Tata Tea Premium 250g", "kind": ConnectorKind.GROCERY,
        "unit": "250 g", "veg": True, "aliases": ["tea", "tata tea", "chai"],
    },
    # -- yet more of the food menu --
    "idli": {
        "name": "Idli (4 pcs)", "kind": ConnectorKind.FOOD,
        "unit": "4 pcs", "veg": True, "aliases": ["idli", "idly"],
    },
    "medu_vada": {
        "name": "Medu Vada (2 pcs)", "kind": ConnectorKind.FOOD,
        "unit": "2 pcs", "veg": True, "aliases": ["medu vada", "vada", "wada"],
    },
    "veg_manchurian": {
        "name": "Veg Manchurian", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True,
        "aliases": ["veg manchurian", "vegetable manchurian", "manchurian"],
    },
    "chilli_chicken": {
        "name": "Chilli Chicken", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": False, "aliases": ["chilli chicken", "chili chicken"],
    },
    "veg_momos": {
        "name": "Veg Momos (6 pcs)", "kind": ConnectorKind.FOOD,
        "unit": "6 pcs", "veg": True, "aliases": ["veg momos", "vegetable momos", "momos"],
    },
    "chicken_momos": {
        "name": "Chicken Momos (6 pcs)", "kind": ConnectorKind.FOOD,
        "unit": "6 pcs", "veg": False, "aliases": ["chicken momos", "momos"],
    },
    "kadai_paneer": {
        "name": "Kadai Paneer", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True, "aliases": ["kadai paneer", "kadhai paneer"],
    },
    "malai_kofta": {
        "name": "Malai Kofta", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True, "aliases": ["malai kofta", "kofta"],
    },
    "samosa_2pcs": {
        "name": "Samosa (2 pcs)", "kind": ConnectorKind.FOOD,
        "unit": "2 pcs", "veg": True, "aliases": ["samosa", "samosas"],
    },
    "hakka_noodles_veg": {
        "name": "Veg Hakka Noodles", "kind": ConnectorKind.FOOD,
        "unit": "1 plate", "veg": True,
        "aliases": ["hakka noodles", "veg noodles", "noodles"],
    },
    "fish_curry": {
        "name": "Fish Curry", "kind": ConnectorKind.FOOD,
        "unit": "1 bowl", "veg": False, "aliases": ["fish curry", "fish gravy"],
    },
    "dhokla": {
        "name": "Dhokla (4 pcs)", "kind": ConnectorKind.FOOD,
        "unit": "4 pcs", "veg": True, "aliases": ["dhokla"],
    },
    "kathi_roll_egg": {
        "name": "Egg Kathi Roll", "kind": ConnectorKind.FOOD,
        "unit": "1 roll", "veg": False, "aliases": ["kathi roll", "egg roll", "roll"],
    },
    "jalebi": {
        "name": "Jalebi (4 pcs)", "kind": ConnectorKind.FOOD,
        "unit": "4 pcs", "veg": True, "aliases": ["jalebi", "dessert"],
    },
    "rasgulla": {
        "name": "Rasgulla (4 pcs)", "kind": ConnectorKind.FOOD,
        "unit": "4 pcs", "veg": True, "aliases": ["rasgulla", "roshogolla", "dessert"],
    },
    # -- yet more of the grocery aisle --
    "moong_dal_1kg": {
        "name": "Moong Dal 1kg", "kind": ConnectorKind.GROCERY,
        "unit": "1 kg", "veg": True, "aliases": ["moong dal", "mung dal", "green gram"],
    },
    "ghee_500ml": {
        "name": "Ghee 500ml", "kind": ConnectorKind.GROCERY,
        "unit": "500 ml", "veg": True, "aliases": ["ghee", "clarified butter"],
    },
    "besan_1kg": {
        "name": "Besan 1kg", "kind": ConnectorKind.GROCERY,
        "unit": "1 kg", "veg": True, "aliases": ["besan", "gram flour", "chickpea flour"],
    },
    "maggi_noodles": {
        "name": "Maggi 2-Minute Noodles (pack of 4)", "kind": ConnectorKind.GROCERY,
        "unit": "pack of 4", "veg": True, "aliases": ["maggi", "maggi noodles", "instant noodles"],
    },
    "parle_g_biscuits": {
        "name": "Parle-G Biscuits 250g", "kind": ConnectorKind.GROCERY,
        "unit": "250 g", "veg": True, "aliases": ["parle g", "biscuits", "parle-g"],
    },
    "green_chilli_250g": {
        "name": "Green Chilli 250g", "kind": ConnectorKind.GROCERY,
        "unit": "250 g", "veg": True, "aliases": ["green chilli", "hari mirch", "chilli"],
    },
    "capsicum_1kg": {
        "name": "Capsicum 1kg", "kind": ConnectorKind.GROCERY,
        "unit": "1 kg", "veg": True, "aliases": ["capsicum", "bell pepper", "shimla mirch"],
    },
    "lemon_500g": {
        "name": "Lemon 500g", "kind": ConnectorKind.GROCERY,
        "unit": "500 g", "veg": True, "aliases": ["lemon", "nimbu"],
    },
    "frozen_peas_500g": {
        "name": "Frozen Green Peas 500g", "kind": ConnectorKind.GROCERY,
        "unit": "500 g", "veg": True, "aliases": ["frozen peas", "green peas", "matar"],
    },
    "coriander_bunch": {
        "name": "Coriander Leaves (1 bunch)", "kind": ConnectorKind.GROCERY,
        "unit": "1 bunch", "veg": True, "aliases": ["coriander", "dhaniya", "cilantro"],
    },
}

# --- per-platform offers ----------------------------------------------------
# platform -> { catalog_key: offer params }. Missing key = platform doesn't list
# it. available=False = listed but out of stock.
def _d(v: str) -> Decimal:
    return Decimal(v)


PLATFORM_OFFERS: dict[str, dict[str, dict]] = {
    # ---------------- FOOD ----------------
    "swiggy": {
        "paneer_butter_masala": dict(base_price=_d("249"), tax=_d("12.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=32, rating=4.3, offer_text="Free delivery with Swiggy One",
            tier=AuthorityTier.TIER_1),
        "chicken_biryani": dict(base_price=_d("279"), tax=_d("13.95"),
            delivery_fee=_d("35"), surge=_d("20"), membership_discount=_d("35"),
            eta_minutes=38, rating=4.1, offer_text="20% off up to ₹50",
            tier=AuthorityTier.TIER_1),
        "masala_dosa": dict(base_price=_d("129"), tax=_d("6.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=27, rating=4.5, offer_text=None, tier=AuthorityTier.TIER_1),
        "chicken_curry": dict(base_price=_d("219"), tax=_d("10.95"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=34, rating=4.2, offer_text=None, tier=AuthorityTier.TIER_1),
        "butter_chicken": dict(base_price=_d("289"), tax=_d("14.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=36, rating=4.4, offer_text="20% off up to ₹50", tier=AuthorityTier.TIER_1),
        "veg_biryani": dict(base_price=_d("169"), tax=_d("8.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=30, rating=4.1, offer_text=None, tier=AuthorityTier.TIER_1),
        "dal_makhani": dict(base_price=_d("179"), tax=_d("8.95"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=29, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_1),
        "chole_bhature": dict(base_price=_d("129"), tax=_d("6.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=26, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "mutton_biryani": dict(base_price=_d("349"), tax=_d("17.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=42, rating=4.4, offer_text="20% off up to ₹50", tier=AuthorityTier.TIER_1),
        "egg_biryani": dict(base_price=_d("189"), tax=_d("9.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=30, rating=4.1, offer_text=None, tier=AuthorityTier.TIER_1),
        "veg_fried_rice": dict(base_price=_d("159"), tax=_d("7.95"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=25, rating=4.0, offer_text=None, tier=AuthorityTier.TIER_1),
        "pav_bhaji": dict(base_price=_d("139"), tax=_d("6.95"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=24, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_1),
        "rajma_chawal": dict(base_price=_d("149"), tax=_d("7.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=28, rating=4.2, offer_text=None, tier=AuthorityTier.TIER_1),
        "palak_paneer": dict(base_price=_d("199"), tax=_d("9.95"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=31, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_1),
        "chicken_65": dict(base_price=_d("229"), tax=_d("11.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=27, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "gulab_jamun": dict(base_price=_d("79"), tax=_d("3.95"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=20, rating=4.5, offer_text=None, tier=AuthorityTier.TIER_1),
        "idli": dict(base_price=_d("89"), tax=_d("4.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=24, rating=4.5, offer_text=None, tier=AuthorityTier.TIER_1),
        "medu_vada": dict(base_price=_d("69"), tax=_d("3.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=23, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "veg_manchurian": dict(base_price=_d("179"), tax=_d("8.95"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=29, rating=4.1, offer_text=None, tier=AuthorityTier.TIER_1),
        "chilli_chicken": dict(base_price=_d("219"), tax=_d("10.95"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=30, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_1),
        "veg_momos": dict(base_price=_d("129"), tax=_d("6.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=22, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "chicken_momos": dict(base_price=_d("149"), tax=_d("7.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=22, rating=4.5, offer_text=None, tier=AuthorityTier.TIER_1),
        "kadai_paneer": dict(base_price=_d("219"), tax=_d("10.95"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=32, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_1),
        "malai_kofta": dict(base_price=_d("209"), tax=_d("10.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=33, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "samosa_2pcs": dict(base_price=_d("49"), tax=_d("2.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=18, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_1),
        "hakka_noodles_veg": dict(base_price=_d("169"), tax=_d("8.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=26, rating=4.1, offer_text=None, tier=AuthorityTier.TIER_1),
        "fish_curry": dict(base_price=_d("259"), tax=_d("12.95"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=35, rating=4.2, offer_text=None, tier=AuthorityTier.TIER_1),
        "dhokla": dict(base_price=_d("99"), tax=_d("4.95"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=21, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "kathi_roll_egg": dict(base_price=_d("109"), tax=_d("5.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=20, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_1),
        "jalebi": dict(base_price=_d("69"), tax=_d("3.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=19, rating=4.5, offer_text=None, tier=AuthorityTier.TIER_1),
        "rasgulla": dict(base_price=_d("89"), tax=_d("4.45"),
            delivery_fee=_d("35"), surge=_d("0"), membership_discount=_d("35"),
            eta_minutes=19, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
    },
    "zomato": {
        "paneer_butter_masala": dict(base_price=_d("239"), tax=_d("11.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=41, rating=4.4, offer_text="Free delivery with Gold",
            tier=AuthorityTier.TIER_1),
        "chicken_biryani": dict(base_price=_d("265"), tax=_d("13.25"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=35, rating=4.3, offer_text="Buy 1 Get 1",
            tier=AuthorityTier.TIER_1),
        "masala_dosa": dict(base_price=_d("119"), tax=_d("5.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=44, rating=4.2, offer_text=None, tier=AuthorityTier.TIER_2),
        "chicken_curry": dict(base_price=_d("229"), tax=_d("11.45"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=39, rating=4.3, offer_text="Buy 1 Get 1", tier=AuthorityTier.TIER_1),
        "butter_chicken": dict(base_price=_d("279"), tax=_d("13.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=40, rating=4.5, offer_text=None, tier=AuthorityTier.TIER_1),
        "veg_biryani": dict(base_price=_d("159"), tax=_d("7.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=37, rating=4.2, offer_text=None, tier=AuthorityTier.TIER_1),
        "dal_makhani": dict(base_price=_d("169"), tax=_d("8.45"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=35, rating=4.4, offer_text="Free delivery with Gold", tier=AuthorityTier.TIER_1),
        "chole_bhature": dict(base_price=_d("139"), tax=_d("6.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=33, rating=4.2, offer_text=None, tier=AuthorityTier.TIER_2),
        "mutton_biryani": dict(base_price=_d("339"), tax=_d("16.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=45, rating=4.5, offer_text="Buy 1 Get 1", tier=AuthorityTier.TIER_1),
        "egg_biryani": dict(base_price=_d("179"), tax=_d("8.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=33, rating=4.2, offer_text=None, tier=AuthorityTier.TIER_2),
        "veg_fried_rice": dict(base_price=_d("149"), tax=_d("7.45"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=28, rating=4.1, offer_text=None, tier=AuthorityTier.TIER_1),
        "pav_bhaji": dict(base_price=_d("129"), tax=_d("6.45"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=27, rating=4.2, offer_text=None, tier=AuthorityTier.TIER_1),
        "rajma_chawal": dict(base_price=_d("139"), tax=_d("6.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=31, rating=4.1, offer_text=None, tier=AuthorityTier.TIER_2),
        "palak_paneer": dict(base_price=_d("189"), tax=_d("9.45"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=34, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "chicken_65": dict(base_price=_d("219"), tax=_d("10.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=30, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_1),
        "gulab_jamun": dict(base_price=_d("75"), tax=_d("3.75"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=23, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "idli": dict(base_price=_d("85"), tax=_d("4.25"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=28, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_2),
        "medu_vada": dict(base_price=_d("65"), tax=_d("3.25"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=27, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_1),
        "veg_manchurian": dict(base_price=_d("169"), tax=_d("8.45"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=33, rating=4.2, offer_text="Buy 1 Get 1", tier=AuthorityTier.TIER_1),
        "chilli_chicken": dict(base_price=_d("209"), tax=_d("10.45"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=34, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "veg_momos": dict(base_price=_d("119"), tax=_d("5.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=26, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_2),
        "chicken_momos": dict(base_price=_d("139"), tax=_d("6.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=26, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "kadai_paneer": dict(base_price=_d("209"), tax=_d("10.45"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=36, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "malai_kofta": dict(base_price=_d("199"), tax=_d("9.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=37, rating=4.5, offer_text=None, tier=AuthorityTier.TIER_2),
        "samosa_2pcs": dict(base_price=_d("45"), tax=_d("2.25"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=21, rating=4.2, offer_text=None, tier=AuthorityTier.TIER_1),
        "hakka_noodles_veg": dict(base_price=_d("159"), tax=_d("7.95"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=29, rating=4.0, offer_text=None, tier=AuthorityTier.TIER_1),
        "fish_curry": dict(base_price=_d("249"), tax=_d("12.45"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=38, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_2),
        "dhokla": dict(base_price=_d("95"), tax=_d("4.75"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=24, rating=4.3, offer_text=None, tier=AuthorityTier.TIER_1),
        "kathi_roll_egg": dict(base_price=_d("105"), tax=_d("5.25"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=23, rating=4.4, offer_text="Buy 1 Get 1", tier=AuthorityTier.TIER_1),
        "jalebi": dict(base_price=_d("65"), tax=_d("3.25"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=22, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_2),
        "rasgulla": dict(base_price=_d("85"), tax=_d("4.25"),
            delivery_fee=_d("45"), surge=_d("0"), membership_discount=_d("45"),
            eta_minutes=22, rating=4.5, offer_text=None, tier=AuthorityTier.TIER_1),
    },
    # ---------------- GROCERY ----------------
    "blinkit": {
        "amul_milk_500ml": dict(base_price=_d("34"), tax=_d("0"),
            delivery_fee=_d("15"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=11, rating=4.6, offer_text=None, tier=AuthorityTier.TIER_1),
        "aashirvaad_atta_5kg": dict(base_price=_d("255"), tax=_d("0"),
            delivery_fee=_d("15"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=12, rating=4.5, offer_text="₹10 off", tier=AuthorityTier.TIER_1),
        "tata_salt_1kg": dict(base_price=_d("28"), tax=_d("0"),
            delivery_fee=_d("15"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=11, rating=4.6, offer_text=None, tier=AuthorityTier.TIER_1),
        "onion_1kg": dict(base_price=_d("39"), tax=_d("0"),
            delivery_fee=_d("15"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=12, rating=4.2, offer_text=None, tier=AuthorityTier.TIER_1),
        "eggs_6": dict(base_price=_d("47"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=11, rating=4.5,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "bread": dict(base_price=_d("40"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=11, rating=4.4,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "basmati_rice_1kg": dict(base_price=_d("99"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=12, rating=4.5,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "toor_dal_1kg": dict(base_price=_d("145"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=12, rating=4.4,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "sugar_1kg": dict(base_price=_d("44"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=11, rating=4.5,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "sunflower_oil_1l": dict(base_price=_d("155"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=12, rating=4.4,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "curd_400g": dict(base_price=_d("30"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=11, rating=4.5,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "paneer_200g": dict(base_price=_d("89"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=11, rating=4.6,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "potato_1kg": dict(base_price=_d("32"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=12, rating=4.2,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "tomato_1kg": dict(base_price=_d("38"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=12, rating=4.1,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "tata_tea_250g": dict(base_price=_d("148"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=11, rating=4.6,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "moong_dal_1kg": dict(base_price=_d("128"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=12, rating=4.4,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "ghee_500ml": dict(base_price=_d("299"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=12, rating=4.6,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "besan_1kg": dict(base_price=_d("89"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=11, rating=4.4,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "maggi_noodles": dict(base_price=_d("56"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=11, rating=4.7,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "parle_g_biscuits": dict(base_price=_d("30"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=11, rating=4.6,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "green_chilli_250g": dict(base_price=_d("18"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=12, rating=4.1,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "capsicum_1kg": dict(base_price=_d("59"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=12, rating=4.2,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "lemon_500g": dict(base_price=_d("29"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=11, rating=4.2,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "frozen_peas_500g": dict(base_price=_d("69"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=12, rating=4.3,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "coriander_bunch": dict(base_price=_d("12"), tax=_d("0"), delivery_fee=_d("15"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=11, rating=4.0,
            offer_text=None, tier=AuthorityTier.TIER_1),
    },
    "zepto": {
        "amul_milk_500ml": dict(base_price=_d("33"), tax=_d("0"),
            delivery_fee=_d("19"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=9, rating=4.5, offer_text="₹19 delivery", tier=AuthorityTier.TIER_1),
        "aashirvaad_atta_5kg": dict(base_price=_d("259"), tax=_d("0"),
            delivery_fee=_d("19"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=10, rating=4.4, offer_text=None, tier=AuthorityTier.TIER_1),
        "tata_salt_1kg": dict(base_price=_d("27"), tax=_d("0"),
            delivery_fee=_d("19"), surge=_d("0"), membership_discount=_d("0"),
            eta_minutes=9, rating=4.5, offer_text=None, tier=AuthorityTier.TIER_1),
        "onion_1kg": dict(base_price=_d("36"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=10, rating=4.1,
            offer_text="₹5 off", tier=AuthorityTier.TIER_1),
        "eggs_6": dict(base_price=_d("45"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=9, rating=4.4,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "bread": dict(base_price=_d("42"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=10, rating=4.3,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "basmati_rice_1kg": dict(base_price=_d("95"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=10, rating=4.4,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "toor_dal_1kg": dict(base_price=_d("142"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=10, rating=4.3,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "sugar_1kg": dict(base_price=_d("43"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=9, rating=4.4,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "sunflower_oil_1l": dict(base_price=_d("152"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=10, rating=4.3,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "curd_400g": dict(base_price=_d("29"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=9, rating=4.4,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "paneer_200g": dict(base_price=_d("87"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=9, rating=4.5,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "potato_1kg": dict(base_price=_d("30"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=10, rating=4.1,
            offer_text="₹4 off", tier=AuthorityTier.TIER_1),
        "tomato_1kg": dict(base_price=_d("36"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=10, rating=4.0,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "tata_tea_250g": dict(base_price=_d("145"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=9, rating=4.5,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "moong_dal_1kg": dict(base_price=_d("125"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=10, rating=4.3,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "ghee_500ml": dict(base_price=_d("295"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=10, rating=4.5,
            offer_text="₹19 delivery", tier=AuthorityTier.TIER_1),
        "maggi_noodles": dict(base_price=_d("55"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=9, rating=4.6,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "capsicum_1kg": dict(base_price=_d("57"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=10, rating=4.1,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "lemon_500g": dict(base_price=_d("27"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=9, rating=4.1,
            offer_text=None, tier=AuthorityTier.TIER_1),
        "coriander_bunch": dict(base_price=_d("11"), tax=_d("0"), delivery_fee=_d("19"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=9, rating=4.0,
            offer_text=None, tier=AuthorityTier.TIER_1),
    },
    "instamart": {
        "amul_milk_500ml": dict(base_price=_d("35"), tax=_d("0"), delivery_fee=_d("25"),
            surge=_d("0"), membership_discount=_d("25"), eta_minutes=14, rating=4.3,
            offer_text="Free delivery with Swiggy One", tier=AuthorityTier.TIER_1),
        "tata_salt_1kg": dict(base_price=_d("29"), tax=_d("0"), delivery_fee=_d("25"),
            surge=_d("0"), membership_discount=_d("25"), eta_minutes=15, rating=4.2,
            offer_text=None, tier=AuthorityTier.TIER_2),
        "onion_1kg": dict(base_price=_d("42"), tax=_d("0"), delivery_fee=_d("25"),
            surge=_d("0"), membership_discount=_d("25"), eta_minutes=14, rating=4.0,
            offer_text=None, tier=AuthorityTier.TIER_2),
        "eggs_6": dict(base_price=_d("49"), tax=_d("0"), delivery_fee=_d("25"),
            surge=_d("0"), membership_discount=_d("25"), eta_minutes=14, rating=4.3,
            offer_text="Free delivery with Swiggy One", tier=AuthorityTier.TIER_1),
        "bread": dict(base_price=_d("44"), tax=_d("0"), delivery_fee=_d("25"),
            surge=_d("0"), membership_discount=_d("25"), eta_minutes=15, rating=4.2,
            offer_text=None, tier=AuthorityTier.TIER_2),
        "sunflower_oil_1l": dict(base_price=_d("158"), tax=_d("0"), delivery_fee=_d("25"),
            surge=_d("0"), membership_discount=_d("25"), eta_minutes=14, rating=4.2,
            offer_text="Free delivery with Swiggy One", tier=AuthorityTier.TIER_1),
        "curd_400g": dict(base_price=_d("31"), tax=_d("0"), delivery_fee=_d("25"),
            surge=_d("0"), membership_discount=_d("25"), eta_minutes=14, rating=4.3,
            offer_text=None, tier=AuthorityTier.TIER_2),
        "paneer_200g": dict(base_price=_d("92"), tax=_d("0"), delivery_fee=_d("25"),
            surge=_d("0"), membership_discount=_d("25"), eta_minutes=14, rating=4.4,
            offer_text=None, tier=AuthorityTier.TIER_1),
    },
    "bigbasket": {
        "amul_milk_500ml": dict(base_price=_d("32"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("3"), eta_minutes=120, rating=4.4,
            offer_text="BB Star member price", tier=AuthorityTier.TIER_2),
        "aashirvaad_atta_5kg": dict(base_price=_d("245"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("15"), eta_minutes=120, rating=4.5,
            offer_text="Lowest price · ₹15 off with BB Star", tier=AuthorityTier.TIER_2),
        "tata_salt_1kg": dict(base_price=_d("26"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("2"), eta_minutes=120, rating=4.5,
            offer_text="BB Star member price", tier=AuthorityTier.TIER_2),
        "onion_1kg": dict(base_price=_d("33"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("3"), eta_minutes=150, rating=4.3,
            offer_text="Farm fresh", tier=AuthorityTier.TIER_2),
        "eggs_6": dict(base_price=_d("42"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("2"), eta_minutes=120, rating=4.5,
            offer_text="BB Star member price", tier=AuthorityTier.TIER_2),
        "bread": dict(base_price=_d("38"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("2"), eta_minutes=120, rating=4.5,
            offer_text=None, tier=AuthorityTier.TIER_2),
        "basmati_rice_1kg": dict(base_price=_d("89"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("5"), eta_minutes=120, rating=4.6,
            offer_text="Lowest price · ₹5 off with BB Star", tier=AuthorityTier.TIER_2),
        "toor_dal_1kg": dict(base_price=_d("138"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("5"), eta_minutes=120, rating=4.5,
            offer_text="Lowest price · ₹5 off with BB Star", tier=AuthorityTier.TIER_2),
        "sugar_1kg": dict(base_price=_d("41"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("2"), eta_minutes=120, rating=4.5,
            offer_text="BB Star member price", tier=AuthorityTier.TIER_2),
        "sunflower_oil_1l": dict(base_price=_d("149"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("8"), eta_minutes=120, rating=4.5,
            offer_text="₹8 off with BB Star", tier=AuthorityTier.TIER_2),
        "potato_1kg": dict(base_price=_d("28"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("2"), eta_minutes=150, rating=4.3,
            offer_text="Farm fresh", tier=AuthorityTier.TIER_2),
        "tomato_1kg": dict(base_price=_d("34"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("2"), eta_minutes=150, rating=4.2,
            offer_text="Farm fresh", tier=AuthorityTier.TIER_2),
        "tata_tea_250g": dict(base_price=_d("140"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("6"), eta_minutes=120, rating=4.6,
            offer_text="Lowest price · ₹6 off with BB Star", tier=AuthorityTier.TIER_2),
        "moong_dal_1kg": dict(base_price=_d("122"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("5"), eta_minutes=120, rating=4.5,
            offer_text="Lowest price · ₹5 off with BB Star", tier=AuthorityTier.TIER_2),
        "ghee_500ml": dict(base_price=_d("289"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("12"), eta_minutes=120, rating=4.6,
            offer_text="₹12 off with BB Star", tier=AuthorityTier.TIER_2),
        "besan_1kg": dict(base_price=_d("85"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("3"), eta_minutes=120, rating=4.5,
            offer_text="BB Star member price", tier=AuthorityTier.TIER_2),
        "parle_g_biscuits": dict(base_price=_d("28"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("1"), eta_minutes=120, rating=4.6,
            offer_text=None, tier=AuthorityTier.TIER_2),
        "capsicum_1kg": dict(base_price=_d("54"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("3"), eta_minutes=150, rating=4.2,
            offer_text="Farm fresh", tier=AuthorityTier.TIER_2),
        "frozen_peas_500g": dict(base_price=_d("64"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("2"), eta_minutes=120, rating=4.4,
            offer_text=None, tier=AuthorityTier.TIER_2),
    },
    "flipkart_minutes": {
        "amul_milk_500ml": dict(base_price=_d("34"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=16, rating=4.2,
            offer_text="Free delivery", tier=AuthorityTier.TIER_2),
        "tata_salt_1kg": dict(base_price=_d("28"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=18, rating=4.1,
            offer_text=None, tier=AuthorityTier.TIER_2),
        # listed but currently out of stock — exercises availability handling
        "aashirvaad_atta_5kg": dict(base_price=_d("249"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=18, rating=4.2,
            offer_text=None, available=False, tier=AuthorityTier.TIER_2),
        "eggs_6": dict(base_price=_d("46"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=17, rating=4.2,
            offer_text="Free delivery", tier=AuthorityTier.TIER_2),
        "bread": dict(base_price=_d("39"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=18, rating=4.1,
            offer_text=None, tier=AuthorityTier.TIER_2),
        "paneer_200g": dict(base_price=_d("85"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=17, rating=4.2,
            offer_text="Free delivery", tier=AuthorityTier.TIER_2),
        "maggi_noodles": dict(base_price=_d("54"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=17, rating=4.5,
            offer_text="Free delivery", tier=AuthorityTier.TIER_2),
        "lemon_500g": dict(base_price=_d("26"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("0"), eta_minutes=18, rating=4.0,
            offer_text=None, tier=AuthorityTier.TIER_2),
    },
    "amazon_fresh": {
        "amul_milk_500ml": dict(base_price=_d("35"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("2"), eta_minutes=180, rating=4.3,
            offer_text="Free delivery with Prime", tier=AuthorityTier.TIER_2),
        "aashirvaad_atta_5kg": dict(base_price=_d("252"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("10"), eta_minutes=180, rating=4.4,
            offer_text="₹10 off with Prime", tier=AuthorityTier.TIER_2),
        "tata_salt_1kg": dict(base_price=_d("27"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("2"), eta_minutes=180, rating=4.3,
            offer_text="Prime member price", tier=AuthorityTier.TIER_2),
        "basmati_rice_1kg": dict(base_price=_d("92"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("3"), eta_minutes=180, rating=4.4,
            offer_text="₹3 off with Prime", tier=AuthorityTier.TIER_2),
        "sunflower_oil_1l": dict(base_price=_d("156"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("5"), eta_minutes=180, rating=4.3,
            offer_text="₹5 off with Prime", tier=AuthorityTier.TIER_2),
        "tata_tea_250g": dict(base_price=_d("147"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("4"), eta_minutes=180, rating=4.4,
            offer_text="₹4 off with Prime", tier=AuthorityTier.TIER_2),
        "ghee_500ml": dict(base_price=_d("292"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("9"), eta_minutes=180, rating=4.5,
            offer_text="₹9 off with Prime", tier=AuthorityTier.TIER_2),
        "besan_1kg": dict(base_price=_d("87"), tax=_d("0"), delivery_fee=_d("0"),
            surge=_d("0"), membership_discount=_d("2"), eta_minutes=180, rating=4.4,
            offer_text="Prime member price", tier=AuthorityTier.TIER_2),
    },
}


_STOPWORDS = {"and", "with", "the", "for", "of", "in", "my", "some"}


def _haystack(key: str, item: dict) -> list[str]:
    return [item["name"].lower(), key.replace("_", " ")] + item["aliases"]


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z]+", text.lower()) if len(t) >= 3 and t not in _STOPWORDS}


def match_catalog_keys(query: str) -> list[str]:
    """Match catalog keys against the query.

    Substring match first (precise); if nothing matches, fall back to
    significant-token overlap so near-misses like "chicken gravy" still surface
    the chicken dishes instead of returning nothing.
    """
    q = query.strip().lower()
    if not q:
        return []

    substring = [
        key for key, item in CATALOG.items() if any(q in h or h in q for h in _haystack(key, item))
    ]
    if substring:
        return substring

    qtokens = _tokens(q)
    if not qtokens:
        return []
    return [
        key
        for key, item in CATALOG.items()
        if qtokens & set().union(*(_tokens(h) for h in _haystack(key, item)))
    ]


def catalog_item_names() -> list[str]:
    """Display names of everything searchable in the demo catalog."""
    return [item["name"] for item in CATALOG.values()]


_NAME_TO_KEY = {item["name"]: key for key, item in CATALOG.items()}


def match_score(query: str, item_name: str) -> int:
    """How specific a match this item is for the query — the length of the
    longest haystack term that's a substring match either way. Used to rank
    multiple matched dishes so an exact/near-exact match (e.g. "Chicken
    Momos" for query "chicken momos") outranks a dish that only shares one
    short, generic word (e.g. "Chicken Curry", sharing just "chicken") —
    without dropping that weaker match entirely, since a related dish
    surfacing as a secondary result (e.g. "Veg Biryani" for "chicken
    biryani") is useful, just not what should be shown first."""
    key = _NAME_TO_KEY.get(item_name)
    if key is None:
        return 0
    q = query.strip().lower()
    if not q:
        return 0
    best = 0
    for h in _haystack(key, CATALOG[key]):
        if q in h or h in q:
            best = max(best, len(h))
    return best

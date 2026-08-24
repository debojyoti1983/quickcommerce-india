"""Shared domain models that cross module boundaries.

Money is ALWAYS ``Decimal`` (never float) and the currency is INR. ``RawOffer``
is what a connector returns; ``NormalizedOffer`` is the comparable form with a
computed true price and a confidence score.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum, IntEnum
from typing import Optional

from pydantic import BaseModel, Field


class ConnectorKind(str, Enum):
    FOOD = "food"
    GROCERY = "grocery"


class AuthorityTier(IntEnum):
    """Trust ranking for any datum (see CLAUDE.md domain rules)."""

    TIER_1 = 1  # live cart/checkout API — price + ETA at order time
    TIER_2 = 2  # catalog/listing API — recent, pre-cart
    TIER_3 = 3  # cached/scraped/user-recalled — treat with suspicion


class HITLTrigger(str, Enum):
    """Actions that ALWAYS require explicit human approval, never autonomous."""

    PLACE_ORDER = "place_order"
    APPLY_PAID_COUPON = "apply_paid_coupon"
    MODIFY_SUBSCRIPTION = "modify_subscription"
    PAYMENT_METHOD_CHANGE = "payment_method_change"


class UserContext(BaseModel):
    """What we know about the user for this request."""

    pincode: str = "560001"
    city: str = "Bengaluru"
    veg_only: bool = False
    budget_inr: Optional[Decimal] = None
    cuisine_prefs: list[str] = Field(default_factory=list)
    # Which platform memberships the user holds (affects effective price/fees).
    memberships: list[str] = Field(default_factory=list)


class RawOffer(BaseModel):
    """A single option as returned by one platform connector."""

    platform: str
    kind: ConnectorKind
    item_name: str
    unit: Optional[str] = None  # e.g. "500 ml", "1 plate", "5 kg"
    veg: Optional[bool] = None  # None = not applicable (most grocery)
    # The specific restaurant serving this dish (food only; None for grocery,
    # where the platform itself is the seller). Varies by city — see
    # app/connectors/restaurants.py.
    restaurant: Optional[str] = None
    base_price: Decimal
    tax: Decimal = Decimal("0")
    delivery_fee: Decimal = Decimal("0")
    surge: Decimal = Decimal("0")
    membership_discount: Decimal = Decimal("0")  # applied only if user qualifies
    available: bool = True
    eta_minutes: Optional[int] = None
    rating: Optional[float] = None  # 0..5
    offer_text: Optional[str] = None
    store_id: Optional[str] = None
    source_tier: AuthorityTier = AuthorityTier.TIER_2
    captured_at: float  # unix seconds — drives recency decay


class NormalizedOffer(BaseModel):
    """A comparable offer: true all-in price + confidence + staleness."""

    platform: str
    kind: ConnectorKind
    item_name: str
    unit: Optional[str] = None
    veg: Optional[bool] = None
    restaurant: Optional[str] = None
    available: bool
    eta_minutes: Optional[int] = None
    rating: Optional[float] = None
    offer_text: Optional[str] = None

    base_price: Decimal
    tax: Decimal
    delivery_fee: Decimal
    surge: Decimal
    membership_discount: Decimal
    true_price: Decimal  # the all-in number we actually compare on

    confidence: float  # 0..1 composite of authority tier x recency
    stale: bool
    source_tier: AuthorityTier
    captured_at: float

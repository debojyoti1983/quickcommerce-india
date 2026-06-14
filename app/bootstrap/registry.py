"""Connector registry — the 8 platforms the assistant aggregates across.

In this vertical slice every platform is served by a MockConnector. Real adapters
can later be registered against the same interface (see app/connectors/base.py)
without touching the rest of the app.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.models import ConnectorKind


class ConnectorSpec(BaseModel):
    name: str
    display_name: str
    kind: ConnectorKind
    # Membership programme that changes effective price/fees, if any.
    membership: str | None = None


CONNECTORS: list[ConnectorSpec] = [
    ConnectorSpec(name="swiggy", display_name="Swiggy", kind=ConnectorKind.FOOD,
                  membership="Swiggy One"),
    ConnectorSpec(name="zomato", display_name="Zomato", kind=ConnectorKind.FOOD,
                  membership="Zomato Gold"),
    ConnectorSpec(name="blinkit", display_name="Blinkit", kind=ConnectorKind.GROCERY),
    ConnectorSpec(name="zepto", display_name="Zepto", kind=ConnectorKind.GROCERY),
    ConnectorSpec(name="instamart", display_name="Swiggy Instamart",
                  kind=ConnectorKind.GROCERY, membership="Swiggy One"),
    ConnectorSpec(name="bigbasket", display_name="BigBasket",
                  kind=ConnectorKind.GROCERY, membership="BB Star"),
    ConnectorSpec(name="flipkart_minutes", display_name="Flipkart Minutes",
                  kind=ConnectorKind.GROCERY),
    ConnectorSpec(name="amazon_fresh", display_name="Amazon Fresh",
                  kind=ConnectorKind.GROCERY, membership="Prime"),
]


def connectors_for(kind: ConnectorKind) -> list[ConnectorSpec]:
    return [c for c in CONNECTORS if c.kind == kind]

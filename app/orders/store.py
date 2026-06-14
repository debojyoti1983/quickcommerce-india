"""In-memory idempotent order store.

Keyed by the HITL idempotency key, so placing the same approved order twice
(double-click, network retry) returns the identical order rather than creating a
new one. The order id is derived deterministically from the idempotency key.
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class Order(BaseModel):
    order_id: str
    platform: str
    item_name: str
    true_price_inr: Decimal
    pincode: str
    status: str
    idempotency_key: str
    placed_at: float


class OrderStore:
    def __init__(self) -> None:
        self._by_key: dict[str, Order] = {}
        self._by_id: dict[str, Order] = {}

    def place(
        self,
        *,
        platform: str,
        item_name: str,
        true_price_inr: Decimal,
        pincode: str,
        idempotency_key: str,
    ) -> Order:
        existing = self._by_key.get(idempotency_key)
        if existing is not None:
            return existing  # idempotent: never double-order
        order = Order(
            order_id="QC-" + idempotency_key[:8].upper(),
            platform=platform,
            item_name=item_name,
            true_price_inr=true_price_inr,
            pincode=pincode,
            status="placed",
            idempotency_key=idempotency_key,
            placed_at=time.time(),
        )
        self._by_key[idempotency_key] = order
        self._by_id[order.order_id] = order
        return order

    def get(self, order_id: str) -> Optional[Order]:
        return self._by_id.get(order_id)


order_store = OrderStore()

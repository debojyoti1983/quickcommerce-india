"""Tests for idempotent order placement (post-HITL-approval)."""

from decimal import Decimal

from app.orders.store import OrderStore


def _place(store, key="abcd1234ef567890"):
    return store.place(
        platform="Zomato", item_name="Paneer Butter Masala",
        true_price_inr=Decimal("295.95"), pincode="560001", idempotency_key=key,
    )


def test_place_returns_an_order_with_derived_id():
    store = OrderStore()
    order = _place(store)
    assert order.order_id == "QC-ABCD1234"
    assert order.status == "placed"
    assert order.true_price_inr == Decimal("295.95")


def test_same_idempotency_key_never_double_orders():
    store = OrderStore()
    first = _place(store)
    second = _place(store)  # retry with same key
    assert first.order_id == second.order_id
    assert first is second
    assert len(store._by_id) == 1


def test_get_by_order_id():
    store = OrderStore()
    order = _place(store)
    assert store.get(order.order_id) is order
    assert store.get("QC-NOPE") is None

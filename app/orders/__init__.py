"""Module `orders` — idempotent order placement (post-HITL-approval).

A retry with the same idempotency key NEVER creates a second order or double-
charges (a core domain rule). In-process store for the demo; a real build would
persist + checkpoint this (the `messaging` module's job).
"""

from app.orders.store import Order, order_store

__all__ = ["Order", "order_store"]

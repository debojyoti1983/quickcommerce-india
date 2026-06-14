"""Module `memory` — the Claim Graph.

Stores time-stamped, source-attributed facts ("Zepto price for Amul Milk 500ml
= ₹33 at 14:02, Tier 1") so every comparison number is auditable, not
hallucinated. This slice keeps it in-process; persist to a store later.
"""

from app.memory.claim_graph import Claim, ClaimGraph

__all__ = ["Claim", "ClaimGraph"]

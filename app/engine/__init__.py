"""Module `engine` — normalize, compare, recommend.

The deterministic core: turn raw per-platform offers into comparable
NormalizedOffers (true all-in price + confidence), rank them, and choose a best
option with alternatives. The LLM only *narrates* what this engine decides.
"""

from app.engine.compare import Comparison, build_comparison
from app.engine.normalize import normalize_offers
from app.engine.recommend import Recommendation, recommend

__all__ = [
    "Comparison",
    "build_comparison",
    "normalize_offers",
    "Recommendation",
    "recommend",
]

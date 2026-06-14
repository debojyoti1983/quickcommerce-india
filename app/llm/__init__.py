"""Module `llm` — narrates the engine's decision in natural language.

The engine decides; the LLM only explains. If no API key is configured the
client falls back to a deterministic narrator (clearly labelled), so the app
always runs.
"""

from app.llm.client import narrate_recommendation

__all__ = ["narrate_recommendation"]

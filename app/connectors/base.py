"""Connector interface — the contract every platform adapter must satisfy.

Keeping this Protocol stable is what lets a real Swiggy/Blinkit adapter replace
the mock without the engine, bootstrap, or API changing.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from pydantic import BaseModel

from app.models import RawOffer, UserContext


class Serviceability(BaseModel):
    serviceable: bool
    baseline_eta_minutes: Optional[int] = None
    store_id: Optional[str] = None


@runtime_checkable
class Connector(Protocol):
    """A platform connector. Implementations are async and must not raise on
    ordinary 'no result' / 'not serviceable' cases — they return empty/falsey
    values so the orchestrator can degrade gracefully."""

    name: str

    async def serviceability(self, user: UserContext) -> Serviceability: ...

    async def search(self, query: str, user: UserContext) -> list[RawOffer]: ...

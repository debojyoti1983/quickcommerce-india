"""Context snapshot — parallel serviceability probes before turn one.

Fires one probe coroutine per connector with ``asyncio.gather`` so all 8 resolve
in the latency of the slowest, not the sum. A probe that times out or errors is
marked UNREACHABLE; it never crashes the boot (graceful degradation).
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

from pydantic import BaseModel, Field

from app.bootstrap.domain_profile import DomainProfile
from app.bootstrap.registry import CONNECTORS, ConnectorSpec
from app.config import get_settings
from app.connectors.mock_connector import MockConnector
from app.models import ConnectorKind, UserContext


class ConnectorStatus(BaseModel):
    name: str
    display_name: str
    kind: ConnectorKind
    reachable: bool
    serviceable: bool = False
    baseline_eta_minutes: Optional[int] = None
    membership_active: bool = False
    latency_ms: Optional[int] = None
    error: Optional[str] = None


class ContextSnapshot(BaseModel):
    captured_at: float
    profile: DomainProfile
    user: UserContext
    connectors: list[ConnectorStatus]
    missing_data: list[str] = Field(default_factory=list)

    def available(self, kind: ConnectorKind | None = None) -> list[ConnectorStatus]:
        return [
            c
            for c in self.connectors
            if c.reachable and c.serviceable and (kind is None or c.kind == kind)
        ]


async def _probe(spec: ConnectorSpec, user: UserContext, timeout_s: float) -> ConnectorStatus:
    started = time.monotonic()
    try:
        connector = MockConnector(spec)
        result = await asyncio.wait_for(connector.serviceability(user), timeout_s)
        return ConnectorStatus(
            name=spec.name,
            display_name=spec.display_name,
            kind=spec.kind,
            reachable=True,
            serviceable=result.serviceable,
            baseline_eta_minutes=result.baseline_eta_minutes,
            membership_active=bool(spec.membership and spec.membership in user.memberships),
            latency_ms=int((time.monotonic() - started) * 1000),
        )
    except (asyncio.TimeoutError, Exception) as exc:  # noqa: BLE001 — degrade, never crash boot
        return ConnectorStatus(
            name=spec.name,
            display_name=spec.display_name,
            kind=spec.kind,
            reachable=False,
            latency_ms=int((time.monotonic() - started) * 1000),
            error=type(exc).__name__,
        )


async def bootstrap_context(user: UserContext) -> ContextSnapshot:
    settings = get_settings()
    profile = DomainProfile(
        abstention_confidence_threshold=settings.abstention_confidence_threshold,
        max_acceptable_eta_minutes=settings.max_acceptable_eta_minutes,
    )
    statuses = await asyncio.gather(
        *(_probe(spec, user, settings.request_timeout_s) for spec in CONNECTORS)
    )
    missing = [s.display_name for s in statuses if not s.reachable]
    return ContextSnapshot(
        captured_at=time.time(),
        profile=profile,
        user=user,
        connectors=list(statuses),
        missing_data=[f"{name} unreachable" for name in missing],
    )

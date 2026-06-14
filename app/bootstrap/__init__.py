"""Module `bootstrap` — cold-start of the assistant.

Loads the domain profile, enumerates the 8 platform connectors, and probes their
serviceability in parallel so the first turn already knows which apps are live.
"""

from app.bootstrap.domain_profile import DomainProfile
from app.bootstrap.registry import CONNECTORS
from app.bootstrap.snapshot import ContextSnapshot, ConnectorStatus, bootstrap_context

__all__ = [
    "DomainProfile",
    "CONNECTORS",
    "ContextSnapshot",
    "ConnectorStatus",
    "bootstrap_context",
]

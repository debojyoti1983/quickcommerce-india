"""Module `connectors` (tools) — real-time platform data access.

Every platform implements the same async interface (base.py). This slice ships
MockConnector with realistic seed data; drop-in real adapters go here later.
"""

from app.connectors.base import Connector, Serviceability
from app.connectors.mock_connector import MockConnector

__all__ = ["Connector", "Serviceability", "MockConnector"]

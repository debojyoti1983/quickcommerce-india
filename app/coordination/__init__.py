"""Module `coordination` — orchestrates the end-to-end query pipeline.

bootstrap snapshot -> parallel fan-out search across serviceable connectors ->
group by item -> normalize -> compare -> recommend -> narrate. Connector
failures degrade gracefully (that platform is simply absent from the result).
"""

from app.coordination.orchestrator import QueryResponse, QueryResult, run_query

__all__ = ["QueryResponse", "QueryResult", "run_query"]

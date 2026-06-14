"""FastAPI entry point — API + minimal web UI for the QuickCommerce assistant.

Endpoints:
  GET  /                  -> web UI
  GET  /healthz           -> liveness + readiness (connector + LLM status)
  POST /api/compare       -> run a comparison query, return ranked results
  POST /api/order/prepare -> HITL gate: prepares an order, never places it
"""

from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.requests import Request

from app import __version__
from app.accounts.mock_accounts import AccountStatus, detect_accounts
from app.auth.routes import router as auth_router
from app.bootstrap.domain_profile import DomainProfile
from app.config import get_settings
from app.coordination.orchestrator import QueryResponse, run_query
from app.orders.store import Order, order_store
from app.security.hitl import HITLDecision, prepare_action
from app.models import UserContext

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="QuickCommerce India", version=__version__)
app.include_router(auth_router)
_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "web" / "templates"))


# --------------------------- request models --------------------------------
class CompareRequest(BaseModel):
    query: str = Field(min_length=1, max_length=120)
    pincode: str = Field(default="560001", pattern=r"^\d{6}$")
    city: str = Field(default="Bengaluru", max_length=60)
    veg_only: bool = False
    budget_inr: Optional[Decimal] = Field(default=None, ge=0)
    memberships: list[str] = Field(default_factory=list, max_length=10)
    # Platform `name`s to compare across. Empty = all platforms.
    platforms: list[str] = Field(default_factory=list, max_length=20)

    def to_user(self) -> UserContext:
        return UserContext(
            pincode=self.pincode,
            city=self.city,
            veg_only=self.veg_only,
            budget_inr=self.budget_inr,
            memberships=self.memberships,
        )


class OrderPrepareRequest(BaseModel):
    platform: str = Field(min_length=1, max_length=40)
    item_name: str = Field(min_length=1, max_length=120)
    true_price_inr: Decimal = Field(ge=0)
    pincode: str = Field(default="560001", pattern=r"^\d{6}$")


class OrderPlaceRequest(OrderPrepareRequest):
    # The idempotency key returned by /api/order/prepare — ties placement to the
    # human approval and guarantees a retry can't create a second order.
    idempotency_key: str = Field(min_length=8, max_length=64)


# --------------------------- routes -----------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return _TEMPLATES.TemplateResponse(request, "index.html", {"version": __version__})


@app.get("/healthz")
async def healthz() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "llm": "claude" if settings.llm_enabled else "deterministic-fallback",
        "model": settings.llm_model if settings.llm_enabled else None,
    }


@app.post("/api/compare", response_model=QueryResponse)
async def compare(req: CompareRequest) -> QueryResponse:
    return await run_query(req.query, req.to_user(), platforms=req.platforms)


@app.get("/api/account/detect", response_model=list[AccountStatus])
async def account_detect() -> list[AccountStatus]:
    """Simulated 'connect accounts' — reports the demo user's membership status
    per platform. No credentials are ever accepted or stored (see app/accounts)."""
    return detect_accounts()


@app.post("/api/order/prepare", response_model=HITLDecision)
async def order_prepare(req: OrderPrepareRequest) -> HITLDecision:
    """HITL gate. Placing an order is never autonomous — this only PREPARES it
    and returns a decision requiring explicit human approval."""
    return prepare_action(
        "place_order",
        {
            "platform": req.platform,
            "item": req.item_name,
            "true_price_inr": str(req.true_price_inr),
            "pincode": req.pincode,
        },
        DomainProfile(),
    )


@app.post("/api/order/place", response_model=Order)
async def order_place(req: OrderPlaceRequest) -> Order:
    """Place the order AFTER human approval. Idempotent on the approval's
    idempotency key — a retry returns the same order, never a second one."""
    return order_store.place(
        platform=req.platform,
        item_name=req.item_name,
        true_price_inr=req.true_price_inr,
        pincode=req.pincode,
        idempotency_key=req.idempotency_key,
    )


@app.get("/api/order/{order_id}", response_model=Order)
async def order_get(order_id: str) -> Order:
    order = order_store.get(order_id)
    if order is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Order not found")
    return order

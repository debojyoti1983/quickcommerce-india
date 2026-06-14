"""Auth HTTP routes: login page + password / OTP / SSO / session endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.requests import Request

from app import __version__
from app.auth import session as session_mod
from app.auth.otp import otp_store
from app.auth.store import User, get_user_store, normalize_identifier
from app.config import get_settings

router = APIRouter()
_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent.parent / "web" / "templates"))

# Fixed demo identities for the stubbed social SSO providers.
_SSO_IDENTITIES = {
    "google": "demo.user@gmail.com",
    "apple": "demo.user@icloud.com",
}


# --------------------------- request models --------------------------------
class IdentifierBody(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)


class PasswordBody(IdentifierBody):
    password: str = Field(min_length=1, max_length=200)


class OtpVerifyBody(IdentifierBody):
    otp: str = Field(min_length=4, max_length=8)


class SsoBody(BaseModel):
    provider: str = Field(pattern=r"^(google|apple)$")


def _public(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "sso_provider": user.sso_provider,
        "display": user.email or user.phone or f"user#{user.id}",
    }


def _set_session(response: Response, user: User) -> None:
    response.set_cookie(
        session_mod.COOKIE_NAME,
        session_mod.issue(user.id),
        max_age=get_settings().session_ttl_seconds,
        httponly=True,
        samesite="lax",
        secure=get_settings().cookie_secure,  # True behind HTTPS (set QC_COOKIE_SECURE=true)
        path="/",
    )


# --------------------------- routes ----------------------------------------
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return _TEMPLATES.TemplateResponse(request, "login.html", {"version": __version__})


@router.get("/api/auth/me")
async def me(request: Request) -> Response:
    uid = session_mod.read(request.cookies.get(session_mod.COOKIE_NAME))
    if uid is None:
        return Response(status_code=401)
    store = get_user_store()
    with store._conn() as conn:  # small read; reuse the store's connection helper
        row = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    if row is None:
        return Response(status_code=401)
    return _json(_public(store._to_user(row)))


@router.post("/api/auth/password")
async def login_password(body: PasswordBody, response: Response) -> Response:
    try:
        normalize_identifier(body.identifier)
    except ValueError as exc:
        return _json({"error": str(exc)}, status=400)
    user = get_user_store().check_password(body.identifier, body.password)
    if user is None:
        return _json({"error": "Invalid credentials."}, status=401)
    _set_session(response, user)
    return _json({"ok": True, "user": _public(user)}, response=response)


@router.post("/api/auth/otp/request")
async def otp_request(body: IdentifierBody) -> Response:
    try:
        kind, value = normalize_identifier(body.identifier)
    except ValueError as exc:
        return _json({"error": str(exc)}, status=400)
    code = otp_store.request(value)
    out: dict = {"sent": True, "channel": kind, "to": value}
    if get_settings().expose_demo_otp:  # DEMO ONLY — never expose in production
        out["demo_otp"] = code
    return _json(out)


@router.post("/api/auth/otp/verify")
async def otp_verify(body: OtpVerifyBody, response: Response) -> Response:
    try:
        kind, value = normalize_identifier(body.identifier)
    except ValueError as exc:
        return _json({"error": str(exc)}, status=400)
    if not otp_store.verify(value, body.otp.strip()):
        return _json({"error": "Incorrect or expired code."}, status=401)
    user = get_user_store().get_or_create(value)  # passwordless provisioning
    _set_session(response, user)
    return _json({"ok": True, "user": _public(user)}, response=response)


@router.post("/api/auth/sso")
async def sso_login(body: SsoBody, response: Response) -> Response:
    identity = _SSO_IDENTITIES[body.provider]
    user = get_user_store().get_or_create(identity, sso_provider=body.provider)
    _set_session(response, user)
    return _json({"ok": True, "user": _public(user), "provider": body.provider}, response=response)


@router.post("/api/auth/logout")
async def logout(response: Response) -> Response:
    response.delete_cookie(session_mod.COOKIE_NAME, path="/")
    return _json({"ok": True}, response=response)


# --------------------------- helper -----------------------------------------
def _json(payload: dict, *, status: int = 200, response: Optional[Response] = None) -> Response:
    """Return JSON while preserving any cookies already set on `response`."""
    from fastapi.responses import JSONResponse

    jr = JSONResponse(payload, status_code=status)
    if response is not None:
        for key, value in response.raw_headers:
            if key.decode().lower() == "set-cookie":
                jr.raw_headers.append((key, value))
    return jr

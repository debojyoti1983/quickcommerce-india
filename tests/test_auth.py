"""Tests for the demo-grade auth: hashing, identifiers, store, OTP, sessions."""

import pytest

from app.auth import session as session_mod
from app.auth.otp import OtpStore
from app.auth.store import (
    UserStore,
    hash_password,
    normalize_identifier,
    verify_password,
)


def test_password_hash_is_not_plaintext_and_verifies():
    stored = hash_password("demo1234")
    assert "demo1234" not in stored  # never stored in the clear
    assert stored.startswith("pbkdf2_sha256$")
    assert verify_password("demo1234", stored) is True
    assert verify_password("wrong", stored) is False


def test_normalize_identifier_email_phone_and_invalid():
    assert normalize_identifier("User@Example.com ") == ("email", "user@example.com")
    assert normalize_identifier("+91 98765-43210") == ("phone", "+919876543210")
    with pytest.raises(ValueError):
        normalize_identifier("not-an-identifier")


def test_store_password_login(tmp_path):
    store = UserStore(str(tmp_path / "t.db"))
    store.create_user(email="a@b.com", password="s3cret!")
    assert store.check_password("a@b.com", "s3cret!") is not None
    assert store.check_password("a@b.com", "nope") is None


def test_store_get_or_create_is_idempotent(tmp_path):
    store = UserStore(str(tmp_path / "t.db"))
    u1 = store.get_or_create("+919999999999")
    u2 = store.get_or_create("+919999999999")
    assert u1.id == u2.id


def test_otp_flow_single_use_and_wrong_code():
    otp = OtpStore()
    code = otp.request("a@b.com")
    assert otp.verify("a@b.com", "000000") is False or code == "000000"
    assert otp.verify("a@b.com", code) is True
    assert otp.verify("a@b.com", code) is False  # single-use: gone after success


def test_session_roundtrip_and_tamper():
    token = session_mod.issue(42)
    assert session_mod.read(token) == 42
    assert session_mod.read(token + "x") is None  # tampered signature rejected
    assert session_mod.read("garbage") is None

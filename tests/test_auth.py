from __future__ import annotations

import time

import pytest

from lumina.auth import auth


@pytest.mark.unit
def test_hash_and_verify_password_roundtrip() -> None:
    stored = auth.hash_password("S3curePass!")
    assert auth.verify_password("S3curePass!", stored)
    assert not auth.verify_password("wrong-pass", stored)


@pytest.mark.unit
def test_verify_password_rejects_malformed_storage() -> None:
    assert not auth.verify_password("anything", "not-a-salt-hash")


# ---------------------------------------------------------------------------
# Multi-algorithm password hashing
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_hash_sha256_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    """SHA-256 path works when explicitly selected."""
    monkeypatch.setattr(auth, "PASSWORD_HASH_ALGORITHM", "sha256")
    stored = auth.hash_password("testpass")
    assert ":" in stored
    assert not stored.startswith("$")
    assert auth.verify_password("testpass", stored)
    assert not auth.verify_password("wrong", stored)


@pytest.mark.unit
def test_hash_bcrypt_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    """bcrypt path works when installed and selected."""
    pytest.importorskip("bcrypt")
    monkeypatch.setattr(auth, "PASSWORD_HASH_ALGORITHM", "bcrypt")
    stored = auth.hash_password("testpass")
    assert stored.startswith("$2b$")
    assert auth.verify_password("testpass", stored)
    assert not auth.verify_password("wrong", stored)


@pytest.mark.unit
def test_hash_argon2id_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    """Argon2id path works when installed and selected."""
    pytest.importorskip("argon2")
    monkeypatch.setattr(auth, "PASSWORD_HASH_ALGORITHM", "argon2id")
    stored = auth.hash_password("testpass")
    assert stored.startswith("$argon2id$")
    assert auth.verify_password("testpass", stored)
    assert not auth.verify_password("wrong", stored)


@pytest.mark.unit
def test_detect_algorithm_argon2id() -> None:
    assert auth._detect_algorithm("$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$somehash") == "argon2id"


@pytest.mark.unit
def test_detect_algorithm_bcrypt() -> None:
    assert auth._detect_algorithm("$2b$12$LJ3m4ys6YwdMlT0FQ.8Lh.somebcrypthash") == "bcrypt"


@pytest.mark.unit
def test_detect_algorithm_sha256() -> None:
    assert auth._detect_algorithm("abcdef1234567890:deadbeef") == "sha256"


@pytest.mark.unit
def test_detect_algorithm_unknown() -> None:
    assert auth._detect_algorithm("totally-random-string") == "unknown"


@pytest.mark.unit
def test_verify_password_cross_algorithm(monkeypatch: pytest.MonkeyPatch) -> None:
    """verify_password auto-detects even when the configured default differs."""
    monkeypatch.setattr(auth, "PASSWORD_HASH_ALGORITHM", "sha256")
    sha_stored = auth.hash_password("cross-test")

    # Switch default to argon2id — verify still works on the SHA-256 hash
    monkeypatch.setattr(auth, "PASSWORD_HASH_ALGORITHM", "argon2id")
    assert auth.verify_password("cross-test", sha_stored)


@pytest.mark.unit
def test_fallback_when_all_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """When argon2 and bcrypt are unavailable, falls back to sha256."""
    monkeypatch.setattr(auth, "PASSWORD_HASH_ALGORITHM", "argon2id")
    monkeypatch.setattr(auth, "_has_argon2", lambda: False)
    monkeypatch.setattr(auth, "_has_bcrypt", lambda: False)
    assert auth._resolve_algorithm() == "sha256"


@pytest.mark.unit
def test_fallback_argon2_to_bcrypt(monkeypatch: pytest.MonkeyPatch) -> None:
    """When argon2 is missing but bcrypt is available, falls back to bcrypt."""
    monkeypatch.setattr(auth, "PASSWORD_HASH_ALGORITHM", "argon2id")
    monkeypatch.setattr(auth, "_has_argon2", lambda: False)
    monkeypatch.setattr(auth, "_has_bcrypt", lambda: True)
    assert auth._resolve_algorithm() == "bcrypt"


@pytest.mark.unit
def test_fallback_bcrypt_to_sha256(monkeypatch: pytest.MonkeyPatch) -> None:
    """When bcrypt is requested but missing, falls back to sha256."""
    monkeypatch.setattr(auth, "PASSWORD_HASH_ALGORITHM", "bcrypt")
    monkeypatch.setattr(auth, "_has_bcrypt", lambda: False)
    assert auth._resolve_algorithm() == "sha256"


@pytest.mark.unit
def test_verify_returns_false_for_unknown_format() -> None:
    """verify_password returns False for completely unrecognized format."""
    assert not auth.verify_password("anything", "no-recognized-format-here")


@pytest.mark.unit
def test_create_and_verify_jwt_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret")
    token = auth.create_jwt(user_id="u-123", role="user", governed_modules=["mod-1"], ttl_minutes=5)

    payload = auth.verify_jwt(token)
    assert payload["sub"] == "u-123"
    assert payload["role"] == "user"
    assert payload["governed_modules"] == ["mod-1"]
    assert payload["iss"] == auth.JWT_ISSUER


@pytest.mark.unit
def test_create_scoped_jwt_carries_one_active_operating_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret")
    token = auth.create_scoped_jwt(
        user_id="u-123",
        role="user",
        organization_id="org-1",
        site_id="site-2",
        device_id="device-3",
        site_role="manager",
    )

    payload = auth.verify_scoped_jwt(token)
    assert payload["organization_id"] == "org-1"
    assert payload["site_id"] == "site-2"
    assert payload["device_id"] == "device-3"
    assert payload["site_role"] == "manager"


@pytest.mark.unit
def test_create_jwt_rejects_partial_operating_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret")
    with pytest.raises(ValueError, match="supplied together"):
        auth.create_jwt(user_id="u-123", role="user", organization_id="org-1")


@pytest.mark.unit
def test_create_jwt_rejects_invalid_role(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret")
    with pytest.raises(ValueError, match="Invalid role"):
        auth.create_jwt(user_id="u-1", role="superuser")


@pytest.mark.unit
def test_create_jwt_requires_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "JWT_SECRET", "")
    with pytest.raises(auth.AuthError, match="LUMINA_JWT_SECRET must be set"):
        auth.create_jwt(user_id="u-1", role="user")


@pytest.mark.unit
def test_verify_jwt_rejects_tampered_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret")
    token = auth.create_jwt(user_id="u-1", role="user")
    head, payload, sig = token.split(".")
    tampered = f"{head}.{payload[:-1]}A.{sig}"

    with pytest.raises(auth.TokenInvalidError):
        auth.verify_jwt(tampered)


@pytest.mark.unit
def test_verify_jwt_rejects_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret")
    token = auth.create_jwt(user_id="u-1", role="user", ttl_minutes=0)
    time.sleep(1)

    with pytest.raises(auth.TokenExpiredError):
        auth.verify_jwt(token)


@pytest.mark.unit
def test_verify_jwt_rejects_wrong_issuer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret")
    token = auth.create_jwt(user_id="u-1", role="user")

    # Temporarily switch expected issuer to force mismatch.
    monkeypatch.setattr(auth, "JWT_ISSUER", "different-issuer")
    with pytest.raises(auth.TokenInvalidError, match="Unexpected issuer"):
        auth.verify_jwt(token)


@pytest.mark.unit
def test_verify_jwt_rejects_malformed_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret")
    with pytest.raises(auth.TokenInvalidError, match="Malformed token"):
        auth.verify_jwt("not.a.valid.jwt.with.extra")


def _make_erp_token(payload: dict[str, object], secret: str = "erp-secret") -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    h = auth._b64url_encode(auth.json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p = auth._b64url_encode(auth.json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    message = f"{h}.{p}".encode("ascii")
    sig = auth._b64url_encode(auth._sign_hs256(message, secret))
    return f"{h}.{p}.{sig}"


@pytest.mark.unit
def test_verify_erp_jwt_success(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")
    monkeypatch.setattr(auth, "ERP_CLOCK_SKEW_SECONDS", 30)

    payload = {
        "iss": "erp.example",
        "aud": "lumina-api",
        "sub": "actor-1",
        "exp": now + 120,
        "iat": now,
        "jti": "jti-1",
        "role": "operator",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload)
    out = auth.verify_erp_jwt(token)

    assert out["sub"] == "actor-1"
    assert out["token_scope"] == "erp"


@pytest.mark.unit
def test_verify_erp_jwt_rejects_invalid_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")

    payload = {
        "iss": "erp.example",
        "aud": "lumina-api",
        "sub": "actor-1",
        "exp": now + 120,
        "iat": now,
        "jti": "jti-1",
        "role": "operator",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload, secret="wrong-secret")

    with pytest.raises(auth.TokenInvalidError, match="INVALID_SIGNATURE"):
        auth.verify_erp_jwt(token)


@pytest.mark.unit
def test_verify_erp_jwt_rejects_invalid_issuer(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")

    payload = {
        "iss": "erp.other",
        "aud": "lumina-api",
        "sub": "actor-1",
        "exp": now + 120,
        "iat": now,
        "jti": "jti-1",
        "role": "operator",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload)

    with pytest.raises(auth.TokenInvalidError, match="INVALID_ISSUER"):
        auth.verify_erp_jwt(token)


@pytest.mark.unit
def test_verify_erp_jwt_rejects_invalid_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")

    payload = {
        "iss": "erp.example",
        "aud": "other-audience",
        "sub": "actor-1",
        "exp": now + 120,
        "iat": now,
        "jti": "jti-1",
        "role": "operator",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload)

    with pytest.raises(auth.TokenInvalidError, match="INVALID_AUDIENCE"):
        auth.verify_erp_jwt(token)


@pytest.mark.unit
def test_verify_erp_jwt_rejects_non_string_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")

    payload = {
        "iss": "erp.example",
        "aud": ["lumina-api"],
        "sub": "actor-1",
        "exp": now + 120,
        "iat": now,
        "jti": "jti-1",
        "role": "operator",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload)

    with pytest.raises(auth.TokenInvalidError, match="MALFORMED_CLAIM:aud"):
        auth.verify_erp_jwt(token)


@pytest.mark.unit
def test_verify_erp_jwt_rejects_non_string_issuer(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")

    payload = {
        "iss": 123,
        "aud": "lumina-api",
        "sub": "actor-1",
        "exp": now + 120,
        "iat": now,
        "jti": "jti-1",
        "role": "operator",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload)

    with pytest.raises(auth.TokenInvalidError, match="MALFORMED_CLAIM:iss"):
        auth.verify_erp_jwt(token)


@pytest.mark.unit
def test_verify_erp_jwt_rejects_missing_required_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")

    payload = {
        "iss": "erp.example",
        "aud": "lumina-api",
        "sub": "actor-1",
        "exp": now + 120,
        "iat": now,
        "jti": "jti-1",
        "role": "operator",
        "organization_id": "org-1",
    }
    token = _make_erp_token(payload)

    with pytest.raises(auth.TokenInvalidError, match="MISSING_REQUIRED_CLAIM:site_id"):
        auth.verify_erp_jwt(token)


@pytest.mark.unit
def test_verify_erp_jwt_rejects_expired(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")
    monkeypatch.setattr(auth, "ERP_CLOCK_SKEW_SECONDS", 0)

    payload = {
        "iss": "erp.example",
        "aud": "lumina-api",
        "sub": "actor-1",
        "exp": now - 1,
        "iat": now - 10,
        "jti": "jti-1",
        "role": "operator",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload)

    with pytest.raises(auth.TokenExpiredError, match="TOKEN_EXPIRED"):
        auth.verify_erp_jwt(token)


@pytest.mark.unit
def test_verify_erp_jwt_rejects_invalid_time_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")
    monkeypatch.setattr(auth, "ERP_CLOCK_SKEW_SECONDS", 0)

    payload = {
        "iss": "erp.example",
        "aud": "lumina-api",
        "sub": "actor-1",
        "exp": now + 10,
        "iat": now + 20,
        "jti": "jti-1",
        "role": "operator",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload)

    with pytest.raises(auth.TokenInvalidError, match="INVALID_TIME_CLAIMS"):
        auth.verify_erp_jwt(token)


@pytest.mark.unit
def test_verify_erp_jwt_rejects_malformed_signature_segment(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")

    payload = {
        "iss": "erp.example",
        "aud": "lumina-api",
        "sub": "actor-1",
        "exp": now + 120,
        "iat": now,
        "jti": "jti-1",
        "role": "operator",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload)
    h_part, p_part, _ = token.split(".")
    malformed = f"{h_part}.{p_part}.@"

    with pytest.raises(auth.TokenInvalidError, match="MALFORMED_CLAIM"):
        auth.verify_erp_jwt(malformed)


@pytest.mark.unit
def test_verify_erp_jwt_checks_signature_before_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")
    monkeypatch.setattr(auth, "ERP_CLOCK_SKEW_SECONDS", 0)

    payload = {
        "iss": "erp.example",
        "aud": "lumina-api",
        "sub": "actor-1",
        "exp": now - 30,
        "iat": now - 90,
        "jti": "jti-1",
        "role": "operator",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload, secret="wrong-secret")

    with pytest.raises(auth.TokenInvalidError, match="INVALID_SIGNATURE"):
        auth.verify_erp_jwt(token)


@pytest.mark.unit
def test_verify_non_system_jwt_accepts_domain_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")

    payload = {
        "iss": "erp.example",
        "aud": "lumina-api",
        "sub": "actor-1",
        "exp": now + 120,
        "iat": now,
        "jti": "jti-1",
        "role": "admin",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload)
    out = auth.verify_non_system_jwt(token, required_scope="domain")

    assert out["token_scope"] == "domain"


@pytest.mark.unit
def test_verify_non_system_jwt_rejects_scope_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    now = int(time.time())
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")

    payload = {
        "iss": "erp.example",
        "aud": "lumina-api",
        "sub": "actor-1",
        "exp": now + 120,
        "iat": now,
        "jti": "jti-1",
        "role": "admin",
        "organization_id": "org-1",
        "site_id": "site-1",
    }
    token = _make_erp_token(payload)

    with pytest.raises(auth.TokenInvalidError, match="scope mismatch"):
        auth.verify_non_system_jwt(token, required_scope="user")


@pytest.mark.unit
def test_verify_non_system_jwt_rejects_legacy_lumina_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "JWT_SECRET", "legacy-secret")
    monkeypatch.setattr(auth, "ERP_TRUSTED_ISSUER", "erp.example")
    monkeypatch.setattr(auth, "ERP_EXPECTED_AUDIENCE", "lumina-api")
    monkeypatch.setattr(auth, "ERP_JWT_SECRET", "erp-secret")

    legacy = auth.create_scoped_jwt(user_id="u1", role="user")

    with pytest.raises(auth.TokenInvalidError, match="MISSING_REQUIRED_CLAIM:aud"):
        auth.verify_non_system_jwt(legacy, required_scope="user")

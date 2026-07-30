"""Tests for zero-trust domain isolation in admin operations.

Validates that:
- can_govern_domain resolves domain names via registry when governed_modules
  contains module IDs (not domain names).
- list_users respects domain_id, module_id, and domain_role filters.
- Domain authorities are rejected when querying outside their scope.
- list_escalations enforces can_govern_domain boundary.
- _normalize_slm_command infers domain_id for list_users/list_escalations/
  list_modules from instruction text.
- System fallback parser returns deterministic list operations safely.
"""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from lumina.system_log.admin_operations import can_govern_domain


REPO_ROOT = Path(__file__).resolve().parents[1]
_PRIMARY_DOMAIN = "business-ops"
_SECONDARY_DOMAIN = "coding-agent"
_PRIMARY_MODULE = "domain/bizops/auto-repair/v1"
_SECONDARY_MODULE = "domain/ca/coding-agent-core/v1"


def _load_system_runtime_adapters():
    path = REPO_ROOT / "model-packs" / "system" / "controllers" / "runtime_adapters.py"
    spec = importlib.util.spec_from_file_location("system_runtime_adapters_test", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load system runtime adapters")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# -- can_govern_domain with registry ------------------------------------------


def _mock_registry(domain_id: str = _PRIMARY_DOMAIN, module_ids: list[str] | None = None):
    """Build a minimal mock registry for can_govern_domain tests."""
    reg = MagicMock()
    reg.resolve_domain_id.return_value = domain_id
    reg.list_modules_for_domain.return_value = [
        {"module_id": mid} for mid in (module_ids or [_PRIMARY_MODULE])
    ]
    return reg


@pytest.mark.unit
def test_can_govern_domain_direct_match_still_works() -> None:
    """Backward compat: direct domain names in governed_modules still match."""
    user = {"role": "admin", "governed_modules": [_PRIMARY_DOMAIN]}
    assert can_govern_domain(user, _PRIMARY_DOMAIN) is True
    assert can_govern_domain(user, _SECONDARY_DOMAIN) is False


@pytest.mark.unit
def test_can_govern_domain_root_bypass() -> None:
    assert can_govern_domain({"role": "root"}, "anything") is True


@pytest.mark.unit
def test_can_govern_domain_non_da_rejected() -> None:
    assert can_govern_domain({"role": "user"}, _PRIMARY_DOMAIN) is False


@pytest.mark.unit
def test_can_govern_domain_module_id_with_registry() -> None:
    """When governed_modules has module IDs, registry resolves the domain."""
    user = {
        "role": "admin",
        "governed_modules": [_PRIMARY_MODULE],
    }
    reg = _mock_registry(_PRIMARY_DOMAIN, [_PRIMARY_MODULE])
    assert can_govern_domain(user, _PRIMARY_DOMAIN, registry=reg) is True
    reg.resolve_domain_id.assert_called_with(_PRIMARY_DOMAIN)


@pytest.mark.unit
def test_can_govern_domain_module_id_wrong_domain() -> None:
    """DA governing primary modules cannot access secondary domain."""
    user = {
        "role": "admin",
        "governed_modules": [_PRIMARY_MODULE],
    }
    reg = MagicMock()
    reg.resolve_domain_id.return_value = _SECONDARY_DOMAIN
    reg.list_modules_for_domain.return_value = [{"module_id": _SECONDARY_MODULE}]
    assert can_govern_domain(user, _SECONDARY_DOMAIN, registry=reg) is False


@pytest.mark.unit
def test_can_govern_domain_without_registry_module_id_fails() -> None:
    """Without registry, module IDs don't match domain names."""
    user = {
        "role": "admin",
        "governed_modules": [_PRIMARY_MODULE],
    }
    assert can_govern_domain(user, _PRIMARY_DOMAIN) is False


@pytest.mark.unit
def test_can_govern_domain_via_domain_roles_direct() -> None:
    """DA with domain_roles key matching domain_id passes without registry."""
    user = {
        "role": "admin",
        "governed_modules": [],
        "domain_roles": {_PRIMARY_DOMAIN: "admin"},
    }
    assert can_govern_domain(user, _PRIMARY_DOMAIN) is True
    assert can_govern_domain(user, _SECONDARY_DOMAIN) is False


@pytest.mark.unit
def test_can_govern_domain_via_domain_roles_with_registry() -> None:
    """DA with module-level domain_roles keys passes via registry lookup."""
    user = {
        "role": "admin",
        "governed_modules": [],
        "domain_roles": {_PRIMARY_MODULE: "teacher"},
    }
    reg = _mock_registry(_PRIMARY_DOMAIN, [_PRIMARY_MODULE])
    assert can_govern_domain(user, _PRIMARY_DOMAIN, registry=reg) is True


@pytest.mark.unit
def test_can_govern_domain_empty_governed_and_roles() -> None:
    """DA with no explicit scope remains unrestricted by design."""
    user = {
        "role": "admin",
        "governed_modules": [],
        "domain_roles": {},
    }
    reg = _mock_registry(_PRIMARY_DOMAIN, [_PRIMARY_MODULE])
    assert can_govern_domain(user, _PRIMARY_DOMAIN, registry=reg) is True


@pytest.mark.unit
def test_can_govern_domain_unrestricted_da_no_registry() -> None:
    user = {"role": "admin", "governed_modules": [], "domain_roles": {}}
    assert can_govern_domain(user, "anything") is True


@pytest.mark.unit
def test_can_govern_domain_unrestricted_da_missing_keys() -> None:
    user = {"role": "admin"}
    assert can_govern_domain(user, _PRIMARY_DOMAIN) is True


@pytest.mark.unit
def test_can_govern_domain_scoped_da_wrong_domain() -> None:
    user = {
        "role": "admin",
        "governed_modules": [_SECONDARY_DOMAIN],
        "domain_roles": {},
    }
    assert can_govern_domain(user, _PRIMARY_DOMAIN) is False


# -- list_users domain filtering ----------------------------------------------


def _setup_admin_config(monkeypatch, users, registry=None):
    """Patch _cfg for _execute_admin_operation tests."""
    from lumina.api import config as _cfg

    mock_persistence = MagicMock()
    mock_persistence.list_users.return_value = users
    mock_persistence.append_log_record = MagicMock()
    mock_persistence.get_log_ledger_path = MagicMock(return_value="test.jsonl")

    original_persistence = _cfg.PERSISTENCE
    original_registry = _cfg.DOMAIN_REGISTRY
    _cfg.PERSISTENCE = mock_persistence
    if registry is not None:
        _cfg.DOMAIN_REGISTRY = registry
    return original_persistence, original_registry


def _teardown_admin_config(original_persistence, original_registry):
    from lumina.api import config as _cfg

    _cfg.PERSISTENCE = original_persistence
    _cfg.DOMAIN_REGISTRY = original_registry


def _active_registry():
    """Mock registry for business-ops and coding-agent domains."""

    def _resolve(d):
        aliases = {
            "business-ops": "business-ops",
            "biz": "business-ops",
            "coding-agent": "coding-agent",
            "ca": "coding-agent",
        }
        if d in aliases:
            return aliases[d]
        from lumina.core.domain_registry import DomainNotFoundError

        raise DomainNotFoundError(d)

    reg = MagicMock()
    reg.resolve_domain_id.side_effect = _resolve
    reg.list_modules_for_domain.side_effect = lambda d: {
        "business-ops": [{"module_id": _PRIMARY_MODULE}],
        "coding-agent": [{"module_id": _SECONDARY_MODULE}],
    }.get(d, [])
    reg.list_domains.return_value = [
        {
            "domain_id": "business-ops",
            "runtime_config_path": "model-packs/business-ops/cfg/runtime-config.yaml",
        },
        {
            "domain_id": "coding-agent",
            "runtime_config_path": "model-packs/coding-agent/cfg/runtime-config.yaml",
        },
    ]
    return reg


@pytest.mark.unit
def test_list_users_domain_id_filter(monkeypatch) -> None:
    """list_users with domain_id returns only users in that domain's modules."""
    from lumina.api.routes.admin import _execute_admin_operation

    users = [
        {"user_id": "u1", "username": "alice", "role": "user", "governed_modules": [_PRIMARY_MODULE]},
        {"user_id": "u2", "username": "bob", "role": "user", "governed_modules": [_SECONDARY_MODULE]},
        {"user_id": "u3", "username": "carol", "role": "user", "domain_roles": {_PRIMARY_MODULE: "student"}},
    ]
    reg = _active_registry()
    orig_p, orig_r = _setup_admin_config(monkeypatch, users, registry=reg)
    try:
        result = asyncio.run(
            _execute_admin_operation(
                {"sub": "root", "role": "root"},
                {"operation": "list_users", "target": "", "params": {"domain_id": _PRIMARY_DOMAIN}},
                "list users in business-ops",
            )
        )
    finally:
        _teardown_admin_config(orig_p, orig_r)

    assert result["count"] == 2
    user_ids = {u["user_id"] for u in result["users"]}
    assert user_ids == {"u1", "u3"}


@pytest.mark.unit
def test_list_users_module_id_filter(monkeypatch) -> None:
    """list_users with module_id returns only users in that specific module."""
    from lumina.api.routes.admin import _execute_admin_operation

    users = [
        {"user_id": "u1", "username": "alice", "role": "user", "governed_modules": [_PRIMARY_MODULE]},
        {"user_id": "u2", "username": "bob", "role": "user", "governed_modules": [_SECONDARY_MODULE]},
    ]
    reg = _active_registry()
    orig_p, orig_r = _setup_admin_config(monkeypatch, users, registry=reg)
    try:
        result = asyncio.run(
            _execute_admin_operation(
                {"sub": "root", "role": "root"},
                {"operation": "list_users", "target": "", "params": {"module_id": _PRIMARY_MODULE}},
                "list users in primary module",
            )
        )
    finally:
        _teardown_admin_config(orig_p, orig_r)

    assert result["count"] == 1
    assert result["users"][0]["user_id"] == "u1"


@pytest.mark.unit
def test_list_users_domain_role_filter(monkeypatch) -> None:
    """list_users with domain_role filter returns only matching users."""
    from lumina.api.routes.admin import _execute_admin_operation

    users = [
        {"user_id": "u1", "username": "alice", "role": "user", "domain_roles": {_PRIMARY_MODULE: "student"}},
        {"user_id": "u2", "username": "bob", "role": "user", "domain_roles": {_PRIMARY_MODULE: "teacher"}},
        {"user_id": "u3", "username": "carol", "role": "user", "domain_roles": {}},
    ]
    reg = _active_registry()
    orig_p, orig_r = _setup_admin_config(monkeypatch, users, registry=reg)
    try:
        result = asyncio.run(
            _execute_admin_operation(
                {"sub": "root", "role": "root"},
                {"operation": "list_users", "target": "", "params": {"domain_role": "student"}},
                "list students",
            )
        )
    finally:
        _teardown_admin_config(orig_p, orig_r)

    assert result["count"] == 1
    assert result["users"][0]["user_id"] == "u1"


@pytest.mark.unit
def test_da_list_users_cross_domain_rejected(monkeypatch) -> None:
    """DA governing business-ops cannot list users in coding-agent."""
    from fastapi import HTTPException
    from lumina.api.routes.admin import _execute_admin_operation

    users = [{"user_id": "u1", "username": "alice", "role": "user", "governed_modules": [_SECONDARY_MODULE]}]
    reg = _active_registry()
    orig_p, orig_r = _setup_admin_config(monkeypatch, users, registry=reg)
    try:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                _execute_admin_operation(
                    {"sub": "da-biz", "role": "admin", "governed_modules": [_PRIMARY_MODULE]},
                    {"operation": "list_users", "target": "", "params": {"domain_id": _SECONDARY_DOMAIN}},
                    "list users in coding-agent",
                )
            )
        assert exc_info.value.status_code == 403
    finally:
        _teardown_admin_config(orig_p, orig_r)


@pytest.mark.unit
def test_da_list_users_own_domain_allowed(monkeypatch) -> None:
    """DA governing business-ops can list users in business-ops."""
    from lumina.api.routes.admin import _execute_admin_operation

    users = [
        {"user_id": "u1", "username": "alice", "role": "user", "governed_modules": [_PRIMARY_MODULE]},
        {"user_id": "u2", "username": "bob", "role": "user", "governed_modules": [_SECONDARY_MODULE]},
    ]
    reg = _active_registry()
    orig_p, orig_r = _setup_admin_config(monkeypatch, users, registry=reg)
    try:
        result = asyncio.run(
            _execute_admin_operation(
                {"sub": "da-biz", "role": "admin", "governed_modules": [_PRIMARY_MODULE]},
                {"operation": "list_users", "target": "", "params": {"domain_id": _PRIMARY_DOMAIN}},
                "list users in business-ops",
            )
        )
    finally:
        _teardown_admin_config(orig_p, orig_r)

    assert result["count"] == 1
    assert result["users"][0]["user_id"] == "u1"


@pytest.mark.unit
def test_da_list_users_module_cross_domain_rejected(monkeypatch) -> None:
    """DA governing business-ops cannot filter by coding-agent module."""
    from fastapi import HTTPException
    from lumina.api.routes.admin import _execute_admin_operation

    reg = _active_registry()
    orig_p, orig_r = _setup_admin_config(monkeypatch, [], registry=reg)
    try:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                _execute_admin_operation(
                    {"sub": "da-biz", "role": "admin", "governed_modules": [_PRIMARY_MODULE]},
                    {"operation": "list_users", "target": "", "params": {"module_id": _SECONDARY_MODULE}},
                    "list users in coding-agent module",
                )
            )
        assert exc_info.value.status_code == 403
    finally:
        _teardown_admin_config(orig_p, orig_r)


# -- list_escalations domain boundary ----------------------------------------


@pytest.mark.unit
def test_da_list_escalations_cross_domain_rejected(monkeypatch) -> None:
    """DA governing business-ops cannot query coding-agent escalations."""
    from fastapi import HTTPException
    from lumina.api.routes.admin import _execute_admin_operation

    reg = _active_registry()
    orig_p, orig_r = _setup_admin_config(monkeypatch, [], registry=reg)
    try:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                _execute_admin_operation(
                    {"sub": "da-biz", "role": "admin", "governed_modules": [_PRIMARY_MODULE]},
                    {"operation": "list_escalations", "target": "", "params": {"domain_id": _SECONDARY_DOMAIN}},
                    "list escalations in coding-agent",
                )
            )
        assert exc_info.value.status_code == 403
    finally:
        _teardown_admin_config(orig_p, orig_r)


# -- _normalize_slm_command domain inference ---------------------------------


@pytest.mark.unit
def test_normalize_infers_domain_for_list_users() -> None:
    """_normalize_slm_command infers domain_id for list_users from instruction."""
    from lumina.api import config as _cfg
    from lumina.api.routes.admin import _normalize_slm_command

    reg = _active_registry()
    original = _cfg.DOMAIN_REGISTRY
    _cfg.DOMAIN_REGISTRY = reg
    try:
        cmd = {"operation": "list_users", "target": "", "params": {}}
        result = _normalize_slm_command(cmd, "list users in business-ops domain")
        assert result["params"]["domain_id"] == _PRIMARY_DOMAIN
    finally:
        _cfg.DOMAIN_REGISTRY = original


@pytest.mark.unit
def test_normalize_infers_domain_for_list_escalations() -> None:
    """_normalize_slm_command infers domain_id for list_escalations."""
    from lumina.api import config as _cfg
    from lumina.api.routes.admin import _normalize_slm_command

    reg = _active_registry()
    original = _cfg.DOMAIN_REGISTRY
    _cfg.DOMAIN_REGISTRY = reg
    try:
        cmd = {"operation": "list_escalations", "target": "", "params": {}}
        result = _normalize_slm_command(cmd, "show escalations for business-ops")
        assert result["params"]["domain_id"] == _PRIMARY_DOMAIN
    finally:
        _cfg.DOMAIN_REGISTRY = original


@pytest.mark.unit
def test_normalize_infers_domain_for_list_modules() -> None:
    """_normalize_slm_command infers domain_id for list_modules."""
    from lumina.api import config as _cfg
    from lumina.api.routes.admin import _normalize_slm_command

    reg = _active_registry()
    original = _cfg.DOMAIN_REGISTRY
    _cfg.DOMAIN_REGISTRY = reg
    try:
        cmd = {"operation": "list_modules", "target": "", "params": {}}
        result = _normalize_slm_command(cmd, "list modules in business-ops")
        assert result["params"]["domain_id"] == _PRIMARY_DOMAIN
    finally:
        _cfg.DOMAIN_REGISTRY = original


@pytest.mark.unit
def test_normalize_does_not_override_existing_domain_id() -> None:
    """If domain_id is already set, _normalize_slm_command keeps it."""
    from lumina.api import config as _cfg
    from lumina.api.routes.admin import _normalize_slm_command

    reg = _active_registry()
    original = _cfg.DOMAIN_REGISTRY
    _cfg.DOMAIN_REGISTRY = reg
    try:
        cmd = {
            "operation": "list_users",
            "target": "",
            "params": {"domain_id": _SECONDARY_DOMAIN},
        }
        result = _normalize_slm_command(cmd, "list users in business-ops domain")
        assert result["params"]["domain_id"] == _SECONDARY_DOMAIN
    finally:
        _cfg.DOMAIN_REGISTRY = original


# -- System fallback parser checks -------------------------------------------


@pytest.mark.unit
def test_system_fallback_returns_list_users_without_forced_domain() -> None:
    mod = _load_system_runtime_adapters()
    result = mod._deterministic_command_fallback("list users", {"intent_type": "read"})
    assert result is not None
    assert result["operation"] == "list_users"
    assert result["params"] == {}


@pytest.mark.unit
def test_system_fallback_returns_list_escalations_without_forced_domain() -> None:
    mod = _load_system_runtime_adapters()
    result = mod._deterministic_command_fallback("list escalations", {"intent_type": "read"})
    assert result is not None
    assert result["operation"] == "list_escalations"
    assert result["params"] == {}


@pytest.mark.unit
def test_system_fallback_returns_list_modules_op() -> None:
    mod = _load_system_runtime_adapters()
    result = mod._deterministic_command_fallback("show modules", {"intent_type": "read"})
    assert result is not None
    assert result["operation"] == "list_modules"
    assert isinstance(result["params"], dict)

"""Tests for active domain lookup, discovery operations, and admin query handlers.

Covers:
- resolve_domain_id exact, prefix, and path-style inputs
- list_modules/list_domains behavior for active domains
- command interpreter and governance docs remain provider-neutral
- admin query handlers for list_users/get_domain_physics/list_daemon_tasks
- domain RBAC discovery and invite normalization under active module IDs
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from lumina.core.domain_registry import DomainNotFoundError, DomainRegistry

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PRIMARY_DOMAIN = "business-ops"
_SECONDARY_DOMAIN = "coding-agent"
_SYSTEM_DOMAIN = "system"
_PRIMARY_MODULE = "domain/bizops/auto-repair/v1"
_SECONDARY_MODULE = "domain/ca/coding-agent-core/v1"


@pytest.fixture
def registry() -> DomainRegistry:
    from lumina.core.runtime_loader import load_runtime_context

    return DomainRegistry(
        repo_root=_REPO_ROOT,
        registry_path="model-packs/system/cfg/domain-registry.yaml",
        load_runtime_context_fn=load_runtime_context,
    )


@pytest.mark.unit
def test_resolve_exact_primary(registry: DomainRegistry) -> None:
    assert registry.resolve_domain_id(_PRIMARY_DOMAIN) == _PRIMARY_DOMAIN


@pytest.mark.unit
def test_resolve_exact_secondary(registry: DomainRegistry) -> None:
    assert registry.resolve_domain_id(_SECONDARY_DOMAIN) == _SECONDARY_DOMAIN


@pytest.mark.unit
def test_resolve_exact_system(registry: DomainRegistry) -> None:
    assert registry.resolve_domain_id(_SYSTEM_DOMAIN) == _SYSTEM_DOMAIN


@pytest.mark.unit
def test_resolve_prefix_biz(registry: DomainRegistry) -> None:
    assert registry.resolve_domain_id("biz") == _PRIMARY_DOMAIN


@pytest.mark.unit
def test_resolve_prefix_ca(registry: DomainRegistry) -> None:
    assert registry.resolve_domain_id("ca") == _SECONDARY_DOMAIN


@pytest.mark.unit
def test_resolve_prefix_sys(registry: DomainRegistry) -> None:
    assert registry.resolve_domain_id("sys") == _SYSTEM_DOMAIN


@pytest.mark.unit
def test_resolve_path_domain_biz(registry: DomainRegistry) -> None:
    assert registry.resolve_domain_id("domain/biz") == _PRIMARY_DOMAIN


@pytest.mark.unit
def test_resolve_path_domain_biz_with_module(registry: DomainRegistry) -> None:
    assert registry.resolve_domain_id("domain/biz/auto-repair/v1") == _PRIMARY_DOMAIN


@pytest.mark.unit
def test_resolve_path_domain_ca_with_module(registry: DomainRegistry) -> None:
    assert registry.resolve_domain_id(_SECONDARY_MODULE) == _SECONDARY_DOMAIN


@pytest.mark.unit
def test_resolve_unknown_raises(registry: DomainRegistry) -> None:
    with pytest.raises(DomainNotFoundError):
        registry.resolve_domain_id("nonexistent")


@pytest.mark.unit
def test_resolve_unknown_path_raises(registry: DomainRegistry) -> None:
    with pytest.raises(DomainNotFoundError):
        registry.resolve_domain_id("domain/zzz/module/v1")


@pytest.mark.unit
def test_resolve_none_returns_default(registry: DomainRegistry) -> None:
    assert registry.resolve_domain_id(None) == _PRIMARY_DOMAIN


@pytest.mark.unit
def test_resolve_empty_string_returns_default(registry: DomainRegistry) -> None:
    assert registry.resolve_domain_id("") == _PRIMARY_DOMAIN


@pytest.mark.unit
def test_list_modules_primary(registry: DomainRegistry) -> None:
    modules = registry.list_modules_for_domain(_PRIMARY_DOMAIN)
    mod_ids = {m["module_id"] for m in modules}
    assert _PRIMARY_MODULE in mod_ids


@pytest.mark.unit
def test_list_modules_system(registry: DomainRegistry) -> None:
    modules = registry.list_modules_for_domain(_SYSTEM_DOMAIN)
    assert len(modules) >= 1


@pytest.mark.unit
def test_list_modules_unknown_raises(registry: DomainRegistry) -> None:
    with pytest.raises(DomainNotFoundError):
        registry.list_modules_for_domain("nonexistent")


_FORBIDDEN_PATTERNS = [
    "algebra-level-1",
    "pre-algebra",
    "operations-level-1",
]


@pytest.mark.unit
def test_command_interpreter_spec_has_no_hardcoded_modules() -> None:
    spec_path = _REPO_ROOT / "model-packs/system/domain-lib/reference/command-interpreter-spec-v1.md"
    content = spec_path.read_text(encoding="utf-8").lower()
    for pattern in _FORBIDDEN_PATTERNS:
        assert pattern not in content


@pytest.mark.unit
def test_command_interpreter_spec_mentions_dynamic_discovery() -> None:
    spec_path = _REPO_ROOT / "model-packs/system/domain-lib/reference/command-interpreter-spec-v1.md"
    content = spec_path.read_text(encoding="utf-8").lower()
    assert "list_domain_rbac_roles" in content
    assert "get_domain_module_manifest" in content


@pytest.mark.unit
@pytest.mark.parametrize(
    "rel_path",
    [
        "model-packs/system/modules/system-core/domain-physics.json",
        "model-packs/system/prompts/domain-persona-v1.md",
        "model-packs/system/cfg/runtime-config.yaml",
        "model-packs/system/cfg/admin-operations.yaml",
    ],
)
def test_no_nightcycle_ops_in_governance(rel_path: str) -> None:
    fpath = _REPO_ROOT / rel_path
    if not fpath.exists():
        pytest.skip(f"{rel_path} not found")
    content = fpath.read_text(encoding="utf-8")
    assert "trigger_night_cycle" not in content
    assert "night_cycle_status" not in content


@pytest.mark.unit
def test_admin_operations_has_discovery_ops() -> None:
    fpath = _REPO_ROOT / "model-packs/system/cfg/admin-operations.yaml"
    content = fpath.read_text(encoding="utf-8")
    for op in [
        "list_domains",
        "list_modules",
        "list_domain_rbac_roles",
        "get_domain_module_manifest",
        "list_users",
        "get_domain_physics",
        "list_daemon_tasks",
    ]:
        assert op in content


@pytest.mark.unit
def test_domain_physics_operation_ids_complete() -> None:
    dp_path = _REPO_ROOT / "model-packs/system/modules/system-core/domain-physics.json"
    dp = json.loads(dp_path.read_text(encoding="utf-8"))
    op_ids = dp["subsystem_configs"]["admin_operations"]["operation_ids"]
    for op in [
        "list_domains",
        "list_modules",
        "list_domain_rbac_roles",
        "get_domain_module_manifest",
        "list_users",
        "get_domain_physics",
        "list_daemon_tasks",
    ]:
        assert op in op_ids


@pytest.mark.unit
def test_domain_physics_hitl_exempt_complete() -> None:
    dp_path = _REPO_ROOT / "model-packs/system/modules/system-core/domain-physics.json"
    dp = json.loads(dp_path.read_text(encoding="utf-8"))
    exempt = dp["subsystem_configs"]["admin_operations"]["hitl_policy"]["system_exempt"]
    for op in [
        "list_domain_rbac_roles",
        "get_domain_module_manifest",
        "list_users",
        "get_domain_physics",
        "list_daemon_tasks",
    ]:
        assert op in exempt


@pytest.mark.unit
def test_domain_physics_min_role_for_sensitive_ops() -> None:
    dp_path = _REPO_ROOT / "model-packs/system/modules/system-core/domain-physics.json"
    dp = json.loads(dp_path.read_text(encoding="utf-8"))
    min_role = dp["subsystem_configs"]["governance"]["min_role_policy"]
    assert min_role["list_users"] == "admin"
    assert min_role["get_domain_physics"] == "admin"
    assert min_role["list_daemon_tasks"] == "admin"


@pytest.mark.unit
def test_default_module_exists_business_ops() -> None:
    dp = _REPO_ROOT / "model-packs/business-ops/modules/auto-repair/domain-physics.json"
    assert dp.exists()
    data = json.loads(dp.read_text(encoding="utf-8"))
    assert data["id"] == _PRIMARY_MODULE


@pytest.mark.unit
def test_default_module_exists_coding_agent() -> None:
    dp = _REPO_ROOT / "model-packs/coding-agent/modules/core/domain-physics.json"
    assert dp.exists()
    data = json.loads(dp.read_text(encoding="utf-8"))
    assert data["id"] == _SECONDARY_MODULE


@pytest.mark.unit
def test_pack_yaml_has_default_module_business_ops() -> None:
    from lumina.core.yaml_loader import load_yaml

    pack = load_yaml(str(_REPO_ROOT / "model-packs/business-ops/pack.yaml"))
    assert pack.get("default_module") == "auto-repair"


@pytest.mark.unit
def test_pack_yaml_has_default_module_coding_agent() -> None:
    from lumina.core.yaml_loader import load_yaml

    pack = load_yaml(str(_REPO_ROOT / "model-packs/coding-agent/pack.yaml"))
    assert pack.get("default_module") == "core"


@pytest.mark.unit
def test_get_default_module_id_business_ops(registry: DomainRegistry) -> None:
    mod_id = registry.get_default_module_id(_PRIMARY_DOMAIN)
    assert mod_id is not None
    assert "auto-repair" in mod_id


@pytest.mark.unit
def test_get_default_module_id_coding_agent(registry: DomainRegistry) -> None:
    mod_id = registry.get_default_module_id(_SECONDARY_DOMAIN)
    assert mod_id is not None
    assert "coding-agent-core" in mod_id


@pytest.mark.unit
def test_get_default_module_id_none_for_system(registry: DomainRegistry) -> None:
    assert registry.get_default_module_id(_SYSTEM_DOMAIN) is None


@pytest.mark.unit
def test_governed_modules_stripped_for_non_da() -> None:
    from lumina.api.routes.admin import _normalize_slm_command

    cmd = {
        "operation": "invite_user",
        "target": "TestUser",
        "params": {
            "username": "TestUser",
            "role": "user",
            "governed_modules": [_PRIMARY_MODULE],
        },
    }
    result = _normalize_slm_command(cmd)
    assert "governed_modules" not in result.get("params", {})


@pytest.mark.unit
def test_governed_modules_kept_for_da() -> None:
    from lumina.api.routes.admin import _normalize_slm_command

    cmd = {
        "operation": "invite_user",
        "target": "DAUser",
        "params": {
            "username": "DAUser",
            "role": "admin",
            "governed_modules": [_PRIMARY_MODULE],
        },
    }
    result = _normalize_slm_command(cmd)
    assert result["params"].get("governed_modules") == [_PRIMARY_MODULE]


@pytest.mark.unit
def test_list_users_handler_returns_users() -> None:
    from lumina.api import config as _cfg
    from lumina.api.routes.admin import _execute_admin_operation

    mock_persistence = MagicMock()
    mock_persistence.list_users.return_value = [
        {"user_id": "u1", "username": "alice", "role": "root", "active": True},
        {"user_id": "u2", "username": "bob", "role": "user", "active": True, "password_hash": "hidden"},
    ]
    mock_persistence.append_log_record = MagicMock()
    mock_persistence.get_log_ledger_path = MagicMock(return_value="test.jsonl")

    user_data = {"sub": "admin", "role": "root"}
    parsed = {"operation": "list_users", "target": "", "params": {}}

    original_persistence = _cfg.PERSISTENCE
    _cfg.PERSISTENCE = mock_persistence
    try:
        result = asyncio.run(_execute_admin_operation(user_data, parsed, "list users"))
    finally:
        _cfg.PERSISTENCE = original_persistence

    assert result["operation"] == "list_users"
    assert result["count"] == 2
    for u in result["users"]:
        assert "password_hash" not in u


@pytest.mark.unit
def test_get_domain_physics_handler_returns_physics(registry: DomainRegistry) -> None:
    from lumina.api import config as _cfg
    from lumina.api.routes.admin import _execute_admin_operation

    mock_persistence = MagicMock()
    mock_persistence.append_log_record = MagicMock()
    mock_persistence.get_log_ledger_path = MagicMock(return_value="test.jsonl")

    user_data = {"sub": "admin", "role": "root"}
    parsed = {
        "operation": "get_domain_physics",
        "target": _SYSTEM_DOMAIN,
        "params": {"domain_id": _SYSTEM_DOMAIN},
    }

    original_persistence = _cfg.PERSISTENCE
    original_registry = _cfg.DOMAIN_REGISTRY
    _cfg.PERSISTENCE = mock_persistence
    _cfg.DOMAIN_REGISTRY = registry
    try:
        result = asyncio.run(_execute_admin_operation(user_data, parsed, "show physics for system"))
    finally:
        _cfg.PERSISTENCE = original_persistence
        _cfg.DOMAIN_REGISTRY = original_registry

    assert result["operation"] == "get_domain_physics"
    assert result["domain_id"] == _SYSTEM_DOMAIN
    assert result["count"] >= 1


@pytest.mark.unit
def test_list_daemon_tasks_handler_returns_tasks() -> None:
    from lumina.api import config as _cfg
    from lumina.api.routes.admin import _execute_admin_operation

    mock_persistence = MagicMock()
    mock_persistence.append_log_record = MagicMock()
    mock_persistence.get_log_ledger_path = MagicMock(return_value="test.jsonl")

    user_data = {"sub": "admin", "role": "root"}
    parsed = {"operation": "list_daemon_tasks", "target": "", "params": {}}

    original_persistence = _cfg.PERSISTENCE
    _cfg.PERSISTENCE = mock_persistence
    try:
        result = asyncio.run(_execute_admin_operation(user_data, parsed, "list daemon tasks"))
    finally:
        _cfg.PERSISTENCE = original_persistence

    assert result["operation"] == "list_daemon_tasks"
    assert isinstance(result["tasks"], list)
    assert result["count"] == len(result["tasks"])


@pytest.mark.unit
def test_list_domain_rbac_roles_returns_structure(registry: DomainRegistry) -> None:
    from lumina.api import config as _cfg
    from lumina.api.routes.admin import _execute_admin_operation

    mock_persistence = MagicMock()
    mock_persistence.append_log_record = MagicMock()
    mock_persistence.get_log_ledger_path = MagicMock(return_value="test.jsonl")

    user_data = {"sub": "admin", "role": "root"}
    parsed = {
        "operation": "list_domain_rbac_roles",
        "target": _PRIMARY_DOMAIN,
        "params": {"domain_id": _PRIMARY_DOMAIN},
    }

    original_p = _cfg.PERSISTENCE
    original_r = _cfg.DOMAIN_REGISTRY
    _cfg.PERSISTENCE = mock_persistence
    _cfg.DOMAIN_REGISTRY = registry
    try:
        result = asyncio.run(_execute_admin_operation(user_data, parsed, "list rbac roles"))
    finally:
        _cfg.PERSISTENCE = original_p
        _cfg.DOMAIN_REGISTRY = original_r

    assert result["operation"] == "list_domain_rbac_roles"
    assert result["domain_id"] == _PRIMARY_DOMAIN
    assert isinstance(result["domain_roles"], dict)


@pytest.mark.unit
def test_assign_domain_role_allows_unknown_when_no_role_catalog(registry: DomainRegistry) -> None:
    from lumina.api import config as _cfg
    from lumina.api.routes.admin import _execute_admin_operation

    mock_persistence = MagicMock()
    mock_persistence.get_user.return_value = {"user_id": "u1", "role": "user"}
    mock_persistence.update_user_domain_roles = MagicMock()
    mock_persistence.append_log_record = MagicMock()
    mock_persistence.get_domain_ledger_path = MagicMock(return_value="domain_ledger.jsonl")

    user_data = {"sub": "admin", "role": "root"}
    parsed = {
        "operation": "assign_domain_role",
        "target": "u1",
        "params": {
            "user_id": "u1",
            "module_id": _PRIMARY_MODULE,
            "domain_role": "janitor",
        },
    }

    original_p = _cfg.PERSISTENCE
    original_r = _cfg.DOMAIN_REGISTRY
    _cfg.PERSISTENCE = mock_persistence
    _cfg.DOMAIN_REGISTRY = registry
    try:
        result = asyncio.run(_execute_admin_operation(user_data, parsed, "assign role"))
    finally:
        _cfg.PERSISTENCE = original_p
        _cfg.DOMAIN_REGISTRY = original_r

    assert result["operation"] == "assign_domain_role"
    assert result["domain_role"] == "janitor"


@pytest.mark.unit
def test_dynamic_role_alias_aggregation_shape(registry: DomainRegistry) -> None:
    from lumina.api import config as _cfg
    from lumina.api.routes.admin import _get_domain_role_aliases

    original = _cfg.DOMAIN_REGISTRY
    _cfg.DOMAIN_REGISTRY = registry
    try:
        aliases = _get_domain_role_aliases()
    finally:
        _cfg.DOMAIN_REGISTRY = original

    assert isinstance(aliases, dict)


@pytest.mark.unit
def test_invite_pre_assigns_domain_role() -> None:
    from lumina.api import config as _cfg
    from lumina.api.routes.admin import _execute_admin_operation

    mock_persistence = MagicMock()
    mock_persistence.get_user_by_username.return_value = None
    mock_persistence.create_user = MagicMock()
    mock_persistence.update_user_domain_roles = MagicMock()
    mock_persistence.set_user_invite_token = MagicMock()
    mock_persistence.append_log_record = MagicMock()
    mock_persistence.get_system_ledger_path = MagicMock(return_value="system_ledger.jsonl")

    user_data = {"sub": "admin", "role": "root", "username": "admin"}
    parsed = {
        "operation": "invite_user",
        "target": "OperatorX",
        "params": {
            "username": "OperatorX",
            "role": "user",
            "intended_domain_role": "operator",
            "governed_modules": [_PRIMARY_MODULE],
        },
    }

    original = _cfg.PERSISTENCE
    _cfg.PERSISTENCE = mock_persistence
    try:
        result = asyncio.run(_execute_admin_operation(user_data, parsed, "invite operator"))
    finally:
        _cfg.PERSISTENCE = original

    assert result["operation"] == "invite_user"
    mock_persistence.update_user_domain_roles.assert_called_once()

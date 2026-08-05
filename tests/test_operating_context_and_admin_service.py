from __future__ import annotations

import pytest
from fastapi import FastAPI

from lumina.auth.operating_context import (
    contexts_match,
    default_operating_context,
    normalize_operating_memberships,
    operating_context_from_claims,
    resolve_operating_context,
)
from lumina.services.admin import app as admin_app_mod
from lumina.services.admin import routes as admin_routes_mod
from lumina.services.admin.ops import (
    admin_daemon,
    admin_escalations,
    admin_ingestion,
    admin_invite,
    admin_physics,
    admin_profile,
    admin_queries,
    admin_rbac,
)


@pytest.mark.unit
def test_normalize_operating_memberships_none_returns_empty() -> None:
    assert normalize_operating_memberships(None) == []


@pytest.mark.unit
def test_normalize_operating_memberships_rejects_invalid_shapes() -> None:
    with pytest.raises(ValueError, match="must be a list"):
        normalize_operating_memberships("nope")
    with pytest.raises(ValueError, match="must be mappings"):
        normalize_operating_memberships(["bad"])
    with pytest.raises(ValueError, match="unsupported fields"):
        normalize_operating_memberships([
            {"organization_id": "org", "site_ids": ["s1"], "extra": 1}
        ])


@pytest.mark.unit
def test_normalize_operating_memberships_validates_content() -> None:
    with pytest.raises(ValueError, match="requires organization_id"):
        normalize_operating_memberships([{"organization_id": "", "site_ids": ["s1"]}])
    with pytest.raises(ValueError, match="must not repeat organization_id"):
        normalize_operating_memberships([
            {"organization_id": "org", "site_ids": ["s1"]},
            {"organization_id": "org", "site_ids": ["s2"]},
        ])
    with pytest.raises(ValueError, match="requires site_ids"):
        normalize_operating_memberships([{"organization_id": "org", "site_ids": []}])
    with pytest.raises(ValueError, match="must be non-empty strings"):
        normalize_operating_memberships([
            {"organization_id": "org", "site_ids": [" "]},
        ])
    with pytest.raises(ValueError, match="must be unique"):
        normalize_operating_memberships([
            {"organization_id": "org", "site_ids": ["s1", " s1 "]},
        ])


@pytest.mark.unit
def test_normalize_operating_memberships_validates_site_roles_mapping() -> None:
    with pytest.raises(ValueError, match="site_roles"):
        normalize_operating_memberships([
            {"organization_id": "org", "site_ids": ["s1"], "site_roles": []}
        ])

    with pytest.raises(ValueError, match="site_roles"):
        normalize_operating_memberships([
            {
                "organization_id": "org",
                "site_ids": ["s1"],
                "site_roles": {"s2": "tech"},
            }
        ])

    with pytest.raises(ValueError, match="site_roles"):
        normalize_operating_memberships([
            {
                "organization_id": "org",
                "site_ids": ["s1"],
                "site_roles": {"s1": " "},
            }
        ])


@pytest.mark.unit
def test_normalize_operating_memberships_strips_fields() -> None:
    result = normalize_operating_memberships([
        {
            "organization_id": " org-1 ",
            "site_ids": [" s1 ", "s2"],
            "site_roles": {"s1": " lead ", "s2": "tech"},
        }
    ])
    assert result == [
        {
            "organization_id": "org-1",
            "site_ids": ["s1", "s2"],
            "site_roles": {"s1": "lead", "s2": "tech"},
        }
    ]


@pytest.mark.unit
def test_resolve_operating_context_success_and_failures() -> None:
    memberships = [
        {
            "organization_id": "org-1",
            "site_ids": ["s1", "s2"],
            "site_roles": {"s1": "lead"},
        }
    ]
    result = resolve_operating_context(memberships, organization_id=" org-1 ", site_id=" s2 ")
    assert result == {
        "organization_id": "org-1",
        "site_id": "s2",
        "site_role": None,
    }

    with pytest.raises(ValueError, match="requires organization_id"):
        resolve_operating_context(memberships, organization_id="", site_id="s1")
    with pytest.raises(ValueError, match="requires site_id"):
        resolve_operating_context(memberships, organization_id="org-1", site_id="")
    with pytest.raises(ValueError, match="not assigned"):
        resolve_operating_context(memberships, organization_id="org-1", site_id="s9")


@pytest.mark.unit
def test_default_operating_context_behaviors() -> None:
    assert default_operating_context([]) is None
    memberships = [
        {
            "organization_id": "org-1",
            "site_ids": ["s1", "s2"],
            "site_roles": {"s1": "lead"},
        }
    ]
    assert default_operating_context(memberships) == {
        "organization_id": "org-1",
        "site_id": "s1",
        "site_role": "lead",
    }


@pytest.mark.unit
def test_operating_context_from_claims_variants() -> None:
    assert operating_context_from_claims({}) is None

    with pytest.raises(ValueError, match="requires organization_id"):
        operating_context_from_claims({"site_id": "s1"})
    with pytest.raises(ValueError, match="requires site_id"):
        operating_context_from_claims({"organization_id": "org-1"})
    with pytest.raises(ValueError, match="device_id"):
        operating_context_from_claims({"organization_id": "org-1", "site_id": "s1", "device_id": " "})

    assert operating_context_from_claims(
        {"organization_id": " org-1 ", "site_id": " s1 ", "device_id": " dev-1 "}
    ) == {
        "organization_id": "org-1",
        "site_id": "s1",
        "site_role": None,
        "device_id": "dev-1",
    }


@pytest.mark.unit
def test_contexts_match_uses_normalized_claim_scope() -> None:
    left = {"organization_id": "org-1", "site_id": "s1", "device_id": "d1"}
    right = {"organization_id": " org-1 ", "site_id": " s1 ", "device_id": " d1 "}
    assert contexts_match(left, right) is True

    mismatch = {"organization_id": "org-1", "site_id": "s2", "device_id": "d1"}
    assert contexts_match(left, mismatch) is False


@pytest.mark.unit
def test_admin_service_routes_re_export_router() -> None:
    from lumina.api.routes.admin import router as canonical_router

    assert admin_routes_mod.router is canonical_router
    assert admin_routes_mod.__all__ == ["router"]


@pytest.mark.unit
def test_admin_service_create_app_includes_admin_router() -> None:
    app = admin_app_mod.create_app()
    assert isinstance(app, FastAPI)
    assert app.title == "Lumina Admin & Escalation Service"
    assert app.version == "0.4.0"
    assert len(app.routes) > 0
    assert app.routes[0].path == "/openapi.json"


@pytest.mark.unit
def test_admin_ops_package_re_exports_modules() -> None:
    for mod in [
        admin_daemon,
        admin_escalations,
        admin_ingestion,
        admin_invite,
        admin_physics,
        admin_profile,
        admin_queries,
        admin_rbac,
    ]:
        assert hasattr(mod, "__name__")
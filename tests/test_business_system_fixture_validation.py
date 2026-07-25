"""Deterministic fixture validation for Slice 30 connector scenarios."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
STANDARDS = REPO_ROOT / "standards"

FIXTURE_SCHEMA_PATH = STANDARDS / "connector-fixture-scenario-schema-v1.json"
REQUEST_SCHEMA_PATH = STANDARDS / "business-operation-request-schema-v1.json"
EXTERNAL_REF_SCHEMA_PATH = STANDARDS / "external-system-reference-schema-v1.json"
RESULT_SCHEMA_PATH = STANDARDS / "business-operation-result-schema-v1.json"
EVENT_SCHEMA_PATH = STANDARDS / "business-system-event-schema-v1.json"
ERROR_SCHEMA_PATH = STANDARDS / "connector-error-schema-v1.json"
CONNECTOR_MANIFEST_SCHEMA_PATH = STANDARDS / "business-system-connector-manifest-schema-v1.json"

SCHEMA_FILES = [
    FIXTURE_SCHEMA_PATH,
    REQUEST_SCHEMA_PATH,
    EXTERNAL_REF_SCHEMA_PATH,
    RESULT_SCHEMA_PATH,
    EVENT_SCHEMA_PATH,
    ERROR_SCHEMA_PATH,
    CONNECTOR_MANIFEST_SCHEMA_PATH,
]


def _build_schema_store() -> dict[str, dict]:
    store: dict[str, dict] = {}
    for schema_path in SCHEMA_FILES:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        store[schema_path.name] = schema
        store[schema_path.resolve().as_uri()] = schema
        schema_id = schema.get("$id")
        if isinstance(schema_id, str) and schema_id:
            store[schema_id] = schema
    return store

ACTION_CLASSES = [
    "query",
    "create_draft",
    "update_draft",
    "request_commit",
    "request_cancel",
    "sync_event",
]

SCHEMA_STORE = _build_schema_store()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(path: Path) -> jsonschema.Draft202012Validator:
    schema = _load(path)
    resolver = jsonschema.RefResolver(
        base_uri=f"{path.parent.as_uri()}/",
        referrer=schema,
        store=SCHEMA_STORE,
    )
    return jsonschema.Draft202012Validator(
        schema,
        resolver=resolver,
        format_checker=jsonschema.FormatChecker(),
    )


def _scope() -> dict:
    return {
        "organization_id": "org-a",
        "site_id": "site-a",
        "actor_id": "actor-a",
    }


def _external_ref() -> dict:
    return {
        "connector_instance_id": "erpnext-main",
        "external_record_type": "work_order",
        "external_record_id": "wo-1001",
    }


def _scenario(action_class: str) -> dict:
    return {
        "scenario_id": f"scenario-{action_class}",
        "description": f"Fixture for action class {action_class}",
        "action_class": action_class,
        "capability_namespace": "service/work-order",
        "request": {
            "request_id": f"req-{action_class}",
            "action_class": action_class,
            "capability_namespace": "service/work-order",
            "actor_scope": _scope(),
            "requested_utc": "2026-07-24T19:00:00Z",
            "target_reference": _external_ref(),
            "payload": {"body": "deterministic fixture"},
        },
        "expected_result": {
            "request_id": f"req-{action_class}",
            "result_id": f"res-{action_class}",
            "action_class": action_class,
            "capability_namespace": "service/work-order",
            "status": "completed",
            "occurred_utc": "2026-07-24T19:00:01Z",
            "target_reference": _external_ref(),
            "result_data": {"ok": True},
        },
        "expected_event": {
            "event_id": f"evt-{action_class}",
            "event_type": "work_order.updated",
            "action_class": "sync_event",
            "capability_namespace": "service/work-order",
            "occurred_utc": "2026-07-24T19:00:01Z",
            "actor_scope": _scope(),
            "external_system_reference": _external_ref(),
            "payload": {"changed": "status"},
        },
        "expected_error": None,
    }


@pytest.mark.unit
@pytest.mark.parametrize("action_class", ACTION_CLASSES)
def test_fixture_scenario_accepts_all_action_classes(action_class: str) -> None:
    _validator(FIXTURE_SCHEMA_PATH).validate(_scenario(action_class))


@pytest.mark.unit
def test_request_rejects_unknown_capability_namespace() -> None:
    request = _scenario("query")["request"]
    request["capability_namespace"] = "finance/ledger"
    with pytest.raises(jsonschema.ValidationError):
        _validator(REQUEST_SCHEMA_PATH).validate(request)


@pytest.mark.unit
def test_external_reference_rejects_missing_required_identity_field() -> None:
    payload = _external_ref()
    payload.pop("external_record_id")
    with pytest.raises(jsonschema.ValidationError):
        _validator(EXTERNAL_REF_SCHEMA_PATH).validate(payload)


@pytest.mark.unit
def test_request_payload_rejects_credential_bearing_property_names() -> None:
    request = _scenario("query")["request"]
    request["payload"] = {
        "api_key": "forbidden",
        "query": "select *",
    }
    with pytest.raises(jsonschema.ValidationError):
        _validator(REQUEST_SCHEMA_PATH).validate(request)


@pytest.mark.unit
def test_external_reference_provider_data_rejects_credential_bearing_property_names() -> None:
    payload = _external_ref()
    payload["provider_data"] = {
        "token": "forbidden",
    }
    with pytest.raises(jsonschema.ValidationError):
        _validator(EXTERNAL_REF_SCHEMA_PATH).validate(payload)


@pytest.mark.unit
def test_fixture_can_model_error_path_without_credentials() -> None:
    fixture = _scenario("request_commit")
    fixture["expected_result"]["status"] = "failed"
    fixture["expected_result"]["errors"] = [
        {
            "code": "UPSTREAM_VALIDATION_ERROR",
            "message": "Validation failed",
            "severity": "error",
            "retryable": False,
            "details": {"field": "status"},
        }
    ]
    fixture["expected_event"] = None
    fixture["expected_error"] = deepcopy(fixture["expected_result"]["errors"][0])
    _validator(FIXTURE_SCHEMA_PATH).validate(fixture)


@pytest.mark.unit
def test_fixture_can_model_logistics_delivery_flow() -> None:
    fixture = _scenario("request_commit")
    fixture["capability_namespace"] = "logistics/delivery"
    fixture["request"]["capability_namespace"] = "logistics/delivery"
    fixture["request"]["target_reference"] = {
        "connector_instance_id": "ops-logistics",
        "external_record_type": "facility",
        "external_record_id": "kitchen-42",
        "facility_role": "kitchen/production",
        "geo": {
            "region_id": "north-cluster",
            "service_zone_id": "zone-west",
            "route_cluster_id": "route-zone-west",
        },
    }
    fixture["expected_result"]["capability_namespace"] = "logistics/delivery"
    fixture["expected_result"]["target_reference"] = {
        "connector_instance_id": "ops-logistics",
        "external_record_type": "facility",
        "external_record_id": "customer-11",
        "facility_role": "customer/site",
        "geo": {
            "region_id": "north-cluster",
            "service_zone_id": "zone-west",
            "route_cluster_id": "route-zone-west",
        },
    }
    _validator(FIXTURE_SCHEMA_PATH).validate(fixture)


@pytest.mark.unit
def test_fixture_rejects_forbidden_secret_key_in_route_metadata() -> None:
    fixture = _scenario("request_commit")
    fixture["capability_namespace"] = "logistics/dispatch"
    fixture["request"]["capability_namespace"] = "logistics/dispatch"
    fixture["request"]["metadata"] = {
        "route_cluster_id": "route-zone-a",
        "secret": "forbidden",
    }
    with pytest.raises(jsonschema.ValidationError):
        _validator(FIXTURE_SCHEMA_PATH).validate(fixture)


@pytest.mark.unit
def test_fixture_can_model_multi_leg_supply_chain_flow() -> None:
    fixture = _scenario("request_commit")
    fixture["scenario_id"] = "scenario-multi-leg-farm-to-customer"
    fixture["description"] = "Farm to processing to kitchen to warehouse to customer flow"
    fixture["capability_namespace"] = "logistics/dispatch"
    fixture["request"]["capability_namespace"] = "logistics/dispatch"
    fixture["request"]["target_reference"] = {
        "connector_instance_id": "ops-logistics",
        "external_record_type": "facility",
        "external_record_id": "farm-poultry-1",
        "facility_role": "farm/poultry",
        "geo": {
            "region_id": "north-cluster",
            "service_zone_id": "zone-east",
            "route_cluster_id": "route-zone-east",
        },
    }
    fixture["request"]["payload"] = {
        "legs": [
            {"from": "farm-poultry-1", "to": "proc-1", "purpose": "processing"},
            {"from": "proc-1", "to": "kitchen-4", "purpose": "preparation"},
            {"from": "kitchen-4", "to": "warehouse-2", "purpose": "staging"},
            {"from": "warehouse-2", "to": "customer-19", "purpose": "delivery"},
        ],
        "route_zone_id": "zone-east",
    }
    fixture["expected_result"]["capability_namespace"] = "logistics/dispatch"
    fixture["expected_result"]["target_reference"] = {
        "connector_instance_id": "ops-logistics",
        "external_record_type": "facility",
        "external_record_id": "customer-19",
        "facility_role": "customer/site",
    }
    _validator(FIXTURE_SCHEMA_PATH).validate(fixture)


@pytest.mark.unit
def test_fixture_can_model_towing_exception_and_reassignment() -> None:
    fixture = _scenario("request_commit")
    fixture["scenario_id"] = "scenario-towing-exception-reassign"
    fixture["capability_namespace"] = "logistics/towing"
    fixture["request"]["capability_namespace"] = "logistics/towing"
    fixture["request"]["payload"] = {
        "trip_id": "trip-1001",
        "event": "breakdown",
        "requires_reassignment": True,
    }
    fixture["expected_result"]["capability_namespace"] = "logistics/towing"
    fixture["expected_result"]["status"] = "failed"
    fixture["expected_result"]["errors"] = [
        {
            "code": "TOWING_BREAKDOWN_REASSIGN_REQUIRED",
            "message": "Primary towing unit failed and requires reassignment",
            "severity": "error",
            "retryable": True,
            "action_class": "request_commit",
            "capability_namespace": "logistics/towing",
            "details": {
                "fallback_action": "dispatch_reassign",
                "route_zone_id": "zone-a",
            },
        }
    ]
    fixture["expected_error"] = deepcopy(fixture["expected_result"]["errors"][0])
    _validator(FIXTURE_SCHEMA_PATH).validate(fixture)


@pytest.mark.unit
def test_fixture_can_model_towing_partial_completion_exception() -> None:
    fixture = _scenario("request_commit")
    fixture["scenario_id"] = "scenario-towing-partial-completion"
    fixture["capability_namespace"] = "logistics/towing"
    fixture["request"]["capability_namespace"] = "logistics/towing"
    fixture["request"]["payload"] = {
        "trip_id": "trip-2201",
        "completed_stops": 1,
        "planned_stops": 3,
        "requires_follow_up_trip": True,
    }
    fixture["expected_result"]["capability_namespace"] = "logistics/towing"
    fixture["expected_result"]["status"] = "failed"
    fixture["expected_result"]["errors"] = [
        {
            "code": "TOWING_PARTIAL_COMPLETION",
            "message": "Trip ended before all stops were completed",
            "severity": "warning",
            "retryable": True,
            "action_class": "request_commit",
            "capability_namespace": "logistics/towing",
            "details": {
                "completed_stops": 1,
                "planned_stops": 3,
                "follow_up_required": True,
            },
        }
    ]
    fixture["expected_error"] = deepcopy(fixture["expected_result"]["errors"][0])
    _validator(FIXTURE_SCHEMA_PATH).validate(fixture)

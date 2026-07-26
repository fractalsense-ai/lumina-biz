"""Validation tests for Slice 30 canonical business-system contracts."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
STANDARDS = REPO_ROOT / "standards"

SCHEMA_FILES = {
    "external_ref": STANDARDS / "external-system-reference-schema-v1.json",
    "connector_manifest": STANDARDS / "business-system-connector-manifest-schema-v1.json",
    "operation_request": STANDARDS / "business-operation-request-schema-v1.json",
    "operation_result": STANDARDS / "business-operation-result-schema-v1.json",
    "system_event": STANDARDS / "business-system-event-schema-v1.json",
    "connector_error": STANDARDS / "connector-error-schema-v1.json",
    "fixture_scenario": STANDARDS / "connector-fixture-scenario-schema-v1.json",
    "logistics_asset": STANDARDS / "business-logistics-asset-schema-v1.json",
    "logistics_shipment": STANDARDS / "business-logistics-shipment-schema-v1.json",
    "logistics_trip": STANDARDS / "business-logistics-trip-schema-v1.json",
    "dispatch_assignment": STANDARDS / "business-logistics-dispatch-assignment-schema-v1.json",
    "route_optimization_result": STANDARDS / "business-logistics-route-optimization-result-schema-v1.json",
}


def _build_schema_store() -> dict[str, dict]:
    store: dict[str, dict] = {}
    for schema_path in SCHEMA_FILES.values():
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

CAPABILITY_NAMESPACES = [
    "party/customer",
    "catalog/item",
    "inventory",
    "sales/pos",
    "purchasing",
    "service/work-order",
    "scheduling",
    "timekeeping",
    "accounting/invoice",
    "farm/poultry",
    "farm/beef-cattle",
    "processing/meat",
    "kitchen/production",
    "warehouse/storage",
    "logistics/fleet",
    "logistics/dispatch",
    "logistics/towing",
    "logistics/delivery",
    "logistics/route-zone",
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


def _external_reference() -> dict:
    return {
        "connector_instance_id": "erpnext-main",
        "external_record_type": "work_order",
        "external_record_id": "wo-1001",
        "provider_data": {"doctype": "Work Order"},
    }


def _facility_reference(record_id: str, role: str, zone: str) -> dict:
    return {
        "connector_instance_id": "ops-logistics",
        "external_record_type": "facility",
        "external_record_id": record_id,
        "facility_role": role,
        "geo": {
            "region_id": "north-cluster",
            "service_zone_id": zone,
            "route_cluster_id": f"route-{zone}",
            "latitude": 35.2,
            "longitude": -80.8,
        },
    }


def _scope() -> dict:
    return {
        "organization_id": "org-a",
        "site_id": "site-a",
        "actor_id": "user-42",
    }


@pytest.mark.unit
def test_all_slice30_schema_files_exist() -> None:
    for schema_path in SCHEMA_FILES.values():
        assert schema_path.exists(), f"Missing schema: {schema_path.name}"


@pytest.mark.unit
@pytest.mark.parametrize("schema_path", SCHEMA_FILES.values(), ids=lambda p: p.name)
def test_schema_metadata_present(schema_path: Path) -> None:
    schema = _load(schema_path)
    assert schema["schema_version"] == "1.0.0"
    assert schema["last_updated"] == "2026-07-24"


@pytest.mark.unit
def test_external_system_reference_accepts_provider_neutral_payload() -> None:
    _validator(SCHEMA_FILES["external_ref"]).validate(_external_reference())


@pytest.mark.unit
def test_connector_manifest_accepts_capability_declarations() -> None:
    payload = {
        "connector_id": "connector.erpnext.v1",
        "display_name": "ERPNext Connector",
        "provider_family": "erpnext",
        "version": "1.0.0",
        "capabilities": [
            {
                "namespace": "inventory",
                "supported_actions": ["query", "update_draft"],
            },
            {
                "namespace": "service/work-order",
                "supported_actions": ["query", "create_draft", "request_commit"],
            },
        ],
        "supports_action_classes": ["query", "create_draft", "update_draft", "request_commit"],
        "authentication": {
            "mode": "runtime_secret",
            "secret_ref": "LUMINA_CONNECTOR_ERP_SECRET",
        },
    }
    _validator(SCHEMA_FILES["connector_manifest"]).validate(payload)


@pytest.mark.unit
@pytest.mark.parametrize("action_class", ACTION_CLASSES)
@pytest.mark.parametrize("capability", CAPABILITY_NAMESPACES)
def test_operation_request_accepts_all_action_and_capability_combinations(
    action_class: str,
    capability: str,
) -> None:
    payload = {
        "request_id": "req-1001",
        "action_class": action_class,
        "capability_namespace": capability,
        "actor_scope": _scope(),
        "requested_utc": "2026-07-24T18:00:00Z",
        "target_reference": _external_reference(),
        "payload": {"draft": {"status": "open"}},
    }
    _validator(SCHEMA_FILES["operation_request"]).validate(payload)


@pytest.mark.unit
def test_operation_result_accepts_error_reference() -> None:
    payload = {
        "request_id": "req-1001",
        "result_id": "res-1001",
        "action_class": "request_commit",
        "capability_namespace": "service/work-order",
        "status": "failed",
        "occurred_utc": "2026-07-24T18:00:03Z",
        "target_reference": _external_reference(),
        "errors": [
            {
                "code": "UPSTREAM_TIMEOUT",
                "message": "Provider timeout",
                "severity": "error",
                "retryable": True,
                "action_class": "request_commit",
                "capability_namespace": "service/work-order",
            }
        ],
    }
    _validator(SCHEMA_FILES["operation_result"]).validate(payload)


@pytest.mark.unit
def test_business_system_event_accepts_scoped_event() -> None:
    payload = {
        "event_id": "evt-1001",
        "event_type": "work_order.updated",
        "action_class": "sync_event",
        "capability_namespace": "service/work-order",
        "occurred_utc": "2026-07-24T18:01:00Z",
        "actor_scope": _scope(),
        "external_system_reference": _external_reference(),
        "payload": {"change": "status->closed"},
    }
    _validator(SCHEMA_FILES["system_event"]).validate(payload)


@pytest.mark.unit
def test_connector_error_accepts_minimum_payload() -> None:
    payload = {
        "code": "VALIDATION_FAILED",
        "message": "Payload failed upstream validation",
        "severity": "warning",
        "retryable": False,
    }
    _validator(SCHEMA_FILES["connector_error"]).validate(payload)


@pytest.mark.unit
def test_logistics_asset_schema_accepts_towing_unit() -> None:
    payload = {
        "asset_id": "asset-tow-01",
        "asset_type": "vehicle",
        "status": "active",
        "fleet_class": "towing_unit",
        "home_hub_reference": _facility_reference("hub-1", "fleet/hub", "zone-a"),
        "capacity": {
            "value": 12000,
            "unit": "lb",
        },
    }
    _validator(SCHEMA_FILES["logistics_asset"]).validate(payload)


@pytest.mark.unit
def test_logistics_shipment_schema_accepts_farm_to_warehouse_flow() -> None:
    payload = {
        "shipment_id": "ship-1001",
        "shipment_class": "processed_meat",
        "status": "dispatched",
        "origin_reference": _facility_reference("proc-1", "processing/meat", "zone-a"),
        "destination_reference": _facility_reference("wh-1", "warehouse/storage", "zone-b"),
        "requested_pickup_utc": "2026-07-24T20:00:00Z",
        "required_delivery_utc": "2026-07-24T22:00:00Z",
        "cold_chain_required": True,
        "towing_required": False,
        "line_items": [
            {
                "item_code": "BEEF-TRIM-40LB",
                "quantity": 2,
                "uom": "pallet",
            }
        ],
    }
    _validator(SCHEMA_FILES["logistics_shipment"]).validate(payload)


@pytest.mark.unit
def test_logistics_trip_schema_accepts_towing_and_delivery_stops() -> None:
    payload = {
        "trip_id": "trip-1001",
        "capability_namespace": "logistics/towing",
        "status": "assigned",
        "route_zone_id": "zone-a",
        "primary_asset": {
            "asset_id": "asset-tow-01",
            "asset_type": "vehicle",
            "status": "active",
            "fleet_class": "towing_unit",
            "home_hub_reference": _facility_reference("hub-1", "fleet/hub", "zone-a"),
        },
        "shipment_ids": ["ship-1001"],
        "stops": [
            {
                "sequence": 1,
                "stop_role": "tow_origin",
                "facility_reference": _facility_reference("farm-beef-1", "farm/beef-cattle", "zone-a"),
                "planned_arrival_utc": "2026-07-24T20:10:00Z",
            },
            {
                "sequence": 2,
                "stop_role": "tow_destination",
                "facility_reference": _facility_reference("proc-1", "processing/meat", "zone-a"),
                "planned_arrival_utc": "2026-07-24T21:00:00Z",
            },
        ],
    }
    _validator(SCHEMA_FILES["logistics_trip"]).validate(payload)


@pytest.mark.unit
def test_dispatch_assignment_schema_accepts_reassignment_path() -> None:
    payload = {
        "assignment_id": "asn-1001",
        "capability_namespace": "logistics/dispatch",
        "assignment_status": "reassigned",
        "trip_id": "trip-1001",
        "route_zone_id": "zone-a",
        "primary_asset": {
            "asset_id": "asset-delivery-01",
            "asset_type": "vehicle",
            "status": "active",
            "fleet_class": "local_delivery",
            "home_hub_reference": _facility_reference("hub-1", "fleet/hub", "zone-a"),
        },
        "shipment_ids": ["ship-1001", "ship-1002"],
        "assigned_utc": "2026-07-24T20:05:00Z",
        "reassignment_reason": "Primary unit breakdown; moved to backup.",
        "dispatch_constraints": {
            "max_drive_minutes": 280,
            "requires_cold_chain": True,
        },
    }
    _validator(SCHEMA_FILES["dispatch_assignment"]).validate(payload)


@pytest.mark.unit
def test_route_optimization_result_accepts_towing_recommendation() -> None:
    payload = {
        "optimization_id": "opt-1001",
        "route_zone_id": "zone-a",
        "generated_utc": "2026-07-24T20:00:00Z",
        "optimizer_version": "1.0.0",
        "objective_metrics": {
            "total_distance_km": 142.3,
            "estimated_drive_minutes": 305,
            "estimated_cost_usd": 488.25,
            "on_time_probability": 0.93,
        },
        "recommended_trips": [
            {
                "trip_id": "trip-1001",
                "shipment_ids": ["ship-1001", "ship-1002"],
                "stop_count": 5,
                "requires_towing_support": True,
                "towing_support_asset_ids": ["asset-tow-01"],
            }
        ],
    }
    _validator(SCHEMA_FILES["route_optimization_result"]).validate(payload)


@pytest.mark.unit
def test_route_optimization_rejects_infeasible_zone_without_violations() -> None:
    payload = {
        "optimization_id": "opt-2001",
        "route_zone_id": "zone-infeasible",
        "generated_utc": "2026-07-24T20:15:00Z",
        "optimizer_version": "1.0.0",
        "objective_metrics": {
            "total_distance_km": 0,
            "estimated_drive_minutes": 0,
            "estimated_cost_usd": 0,
        },
        "recommended_trips": [],
    }
    with pytest.raises(jsonschema.ValidationError):
        _validator(SCHEMA_FILES["route_optimization_result"]).validate(payload)


@pytest.mark.unit
def test_route_optimization_rejects_missing_towing_support_assets() -> None:
    payload = {
        "optimization_id": "opt-2002",
        "route_zone_id": "zone-a",
        "generated_utc": "2026-07-24T20:20:00Z",
        "optimizer_version": "1.0.0",
        "objective_metrics": {
            "total_distance_km": 55.4,
            "estimated_drive_minutes": 120,
            "estimated_cost_usd": 145.2,
        },
        "recommended_trips": [
            {
                "trip_id": "trip-2002",
                "shipment_ids": ["ship-2002"],
                "stop_count": 3,
                "requires_towing_support": True,
                "towing_support_asset_ids": [],
            }
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        _validator(SCHEMA_FILES["route_optimization_result"]).validate(payload)


@pytest.mark.unit
def test_route_optimization_rejects_cold_chain_conflict() -> None:
    payload = {
        "optimization_id": "opt-2003",
        "route_zone_id": "zone-cold",
        "generated_utc": "2026-07-24T20:30:00Z",
        "optimizer_version": "1.0.0",
        "objective_metrics": {
            "total_distance_km": 77.8,
            "estimated_drive_minutes": 160,
            "estimated_cost_usd": 210.0,
        },
        "recommended_trips": [
            {
                "trip_id": "trip-2003",
                "shipment_ids": ["ship-cold-1"],
                "stop_count": 4,
                "cold_chain_required": True,
                "cold_chain_supported": False,
            }
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        _validator(SCHEMA_FILES["route_optimization_result"]).validate(payload)

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from lumina.business_ops.connectors.erpnext import (
    DeterministicFixtureRunner,
    FixtureScenario,
    build_connector_manifest,
    execute_with_fixtures,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
STANDARDS = REPO_ROOT / "standards"


def _schema(name: str) -> dict:
    return json.loads((STANDARDS / name).read_text(encoding="utf-8"))


SCHEMA_FILES = [
    STANDARDS / "business-system-connector-manifest-schema-v1.json",
    STANDARDS / "business-operation-result-schema-v1.json",
    STANDARDS / "connector-error-schema-v1.json",
    STANDARDS / "external-system-reference-schema-v1.json",
]


def _store() -> dict[str, dict]:
    store: dict[str, dict] = {}
    for schema_path in SCHEMA_FILES:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        store[schema_path.name] = schema
        store[schema_path.resolve().as_uri()] = schema
        schema_id = schema.get("$id")
        if isinstance(schema_id, str) and schema_id:
            store[schema_id] = schema
    return store


STORE = _store()


def _validator(name: str) -> jsonschema.Draft202012Validator:
    schema_path = STANDARDS / name
    schema = _schema(name)
    resolver = jsonschema.RefResolver(
        base_uri=f"{schema_path.parent.as_uri()}/",
        referrer=schema,
        store=STORE,
    )
    return jsonschema.Draft202012Validator(
        schema,
        resolver=resolver,
        format_checker=jsonschema.FormatChecker(),
    )


@pytest.mark.unit
def test_erpnext_manifest_conforms_to_canonical_schema() -> None:
    manifest = build_connector_manifest()
    _validator("business-system-connector-manifest-schema-v1.json").validate(manifest)


@pytest.mark.unit
def test_fixture_execution_result_conforms_to_operation_result_schema() -> None:
    runner = DeterministicFixtureRunner(
        [
            FixtureScenario(
                scenario_id="wo-query-ok",
                request_match={"action_class": "query", "capability_namespace": "service/work-order"},
                result_payload={"status": "succeeded", "data": {"records": [{"name": "WO-1"}]}} ,
            )
        ]
    )

    result = execute_with_fixtures(
        {
            "request_id": "req-1001",
            "action_class": "query",
            "capability_namespace": "service/work-order",
            "payload": {"name": ["like", "WO-%"]},
        },
        runner,
    )

    assert result["status"] == "completed"
    _validator("business-operation-result-schema-v1.json").validate(result)


@pytest.mark.unit
def test_unsupported_mapping_returns_failed_result_with_schema_valid_error() -> None:
    runner = DeterministicFixtureRunner([])
    result = execute_with_fixtures(
        {
            "request_id": "req-unsupported",
            "action_class": "request_cancel",
            "capability_namespace": "inventory",
            "payload": {},
        },
        runner,
    )

    assert result["status"] == "failed"
    assert isinstance(result.get("errors"), list)
    _validator("connector-error-schema-v1.json").validate(result["errors"][0])  # type: ignore[index]
    _validator("business-operation-result-schema-v1.json").validate(result)

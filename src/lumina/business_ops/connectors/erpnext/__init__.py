"""ERPNext reference connector scaffold for Slice 33."""

from .errors import normalize_erpnext_error
from .fixtures import DeterministicFixtureRunner, FixtureScenario
from .manifest import build_connector_manifest
from .mapping import map_operation_to_erpnext

__all__ = [
    "build_connector_manifest",
    "map_operation_to_erpnext",
    "DeterministicFixtureRunner",
    "FixtureScenario",
    "normalize_erpnext_error",
]

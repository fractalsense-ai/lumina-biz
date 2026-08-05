"""Odoo reference connector scaffold for Slice 34."""

from .errors import normalize_odoo_error
from .execute import execute_with_fixtures
from .fixtures import DeterministicFixtureRunner, FixtureScenario
from .manifest import build_connector_manifest
from .mapping import map_operation_to_odoo

__all__ = [
    "build_connector_manifest",
    "map_operation_to_odoo",
    "execute_with_fixtures",
    "DeterministicFixtureRunner",
    "FixtureScenario",
    "normalize_odoo_error",
]

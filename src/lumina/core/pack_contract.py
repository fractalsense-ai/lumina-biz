from __future__ import annotations

from pathlib import Path
from typing import Any

from lumina.core.yaml_loader import load_yaml

REQUIRED_PACK_KEYS = (
    "pack_id",
    "version",
    "description",
    "layers",
    "modules",
    "default_module",
    "entry_points",
)

OPTIONAL_PACK_KEYS = (
    "owner",
    "vertical_type",
    "scope",
    "routing_defaults",
    "module_map",
    "metadata",
    "maintainers",
    "contract_version",
    "compatibility",
    "notes",
)


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return value


def _validate_optional_pack_fields(manifest: dict[str, Any]) -> None:
    """Validate optional metadata fields documented in the pack authoring contract."""
    if "owner" in manifest and manifest["owner"] is not None:
        owner = manifest["owner"]
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("owner must be a non-empty string when provided")

    if "vertical_type" in manifest and manifest["vertical_type"] is not None:
        vertical_type = manifest["vertical_type"]
        allowed = {"framework", "seed_vertical", "business_ops", "domain"}
        if not isinstance(vertical_type, str) or vertical_type not in allowed:
            raise ValueError(
                "vertical_type must be one of: framework, seed_vertical, business_ops, domain"
            )

    if "scope" in manifest and manifest["scope"] is not None:
        scope = manifest["scope"]
        if not isinstance(scope, (str, dict)) or (isinstance(scope, str) and not scope.strip()):
            raise ValueError("scope must be a non-empty string or mapping when provided")

    if "routing_defaults" in manifest and manifest["routing_defaults"] is not None:
        routing_defaults = manifest["routing_defaults"]
        if not isinstance(routing_defaults, dict):
            raise ValueError("routing_defaults must be a mapping when provided")

    if "module_map" in manifest and manifest["module_map"] is not None:
        module_map = manifest["module_map"]
        if not isinstance(module_map, dict):
            raise ValueError("module_map must be a mapping when provided")

    if "metadata" in manifest and manifest["metadata"] is not None:
        metadata = manifest["metadata"]
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a mapping when provided")

    if "maintainers" in manifest and manifest["maintainers"] is not None:
        maintainers = manifest["maintainers"]
        if not isinstance(maintainers, list) or not all(isinstance(item, str) and item.strip() for item in maintainers):
            raise ValueError("maintainers must be a list of non-empty strings when provided")

    if "contract_version" in manifest and manifest["contract_version"] is not None:
        contract_version = manifest["contract_version"]
        if not isinstance(contract_version, str) or not contract_version.strip():
            raise ValueError("contract_version must be a non-empty string when provided")

    if "compatibility" in manifest and manifest["compatibility"] is not None:
        compatibility = manifest["compatibility"]
        if not isinstance(compatibility, dict):
            raise ValueError("compatibility must be a mapping when provided")

    if "notes" in manifest and manifest["notes"] is not None:
        notes = manifest["notes"]
        if not isinstance(notes, str):
            raise ValueError("notes must be a string when provided")


def validate_pack_manifest(pack_path: str | Path) -> dict[str, Any]:
    """Validate a domain pack manifest against the v1 authoring contract.

    The contract is intentionally strict enough to make pack authoring
    deterministic while still remaining compatible with the existing pack
    manifests in this repository. The underlying semantics are:

    - required keys establish a stable identity and routing surface
    - layers/modules/default_module/entry_points define the actual pack
      authoring contract for runtime registration
    - optional keys allow future domain ownership and compatibility metadata
        without breaking older packs
    """
    path = Path(pack_path)
    if not path.exists():
        raise ValueError(f"pack manifest does not exist: {path}")

    manifest = load_yaml(str(path))
    if not isinstance(manifest, dict):
        raise ValueError(f"{path} must contain a YAML mapping at the top level")

    missing = [key for key in REQUIRED_PACK_KEYS if key not in manifest or manifest.get(key) in (None, "")]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"pack manifest is missing required keys: {joined}")

    pack_id = str(manifest["pack_id"]).strip()
    if not pack_id:
        raise ValueError("pack_id is required")

    version = str(manifest["version"]).strip()
    if not version:
        raise ValueError("version is required")

    description = str(manifest["description"]).strip()
    if not description:
        raise ValueError("description is required")

    layers = _require_mapping(manifest["layers"], "layers")
    if not layers:
        raise ValueError("layers is required and must not be empty")

    modules = _require_list(manifest["modules"], "modules")
    if not modules or not all(isinstance(item, str) and item.strip() for item in modules):
        raise ValueError("modules must be a non-empty list of module IDs")

    default_module = str(manifest["default_module"]).strip()
    if default_module not in modules:
        raise ValueError("default_module must reference a module declared in modules")

    entry_points = _require_mapping(manifest["entry_points"], "entry_points")
    if "runtime_config" not in entry_points:
        raise ValueError("entry_points.runtime_config is required")

    runtime_config_rel = entry_points["runtime_config"]
    runtime_config_path = path.parent / str(runtime_config_rel)
    if not str(runtime_config_rel).strip():
        raise ValueError("entry_points.runtime_config is required")
    if not runtime_config_path.exists():
        raise ValueError(f"entry_points.runtime_config does not exist: {runtime_config_rel}")

    for field in ("pack_id", "version", "description", "default_module"):
        if field in manifest and manifest[field] is None:
            raise ValueError(f"{field} is required")

    _validate_optional_pack_fields(manifest)

    return manifest

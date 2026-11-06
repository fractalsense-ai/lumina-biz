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

    for field in ("pack_id", "version", "description", "default_module"):
        if field in manifest and manifest[field] is None:
            raise ValueError(f"{field} is required")

    for key in OPTIONAL_PACK_KEYS:
        if key in manifest and manifest[key] is not None and key in {"modules", "layers", "entry_points"}:
            # keyed by the validator above; nothing extra to do here.
            continue

    return manifest

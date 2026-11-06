from __future__ import annotations

from pathlib import Path

import pytest

from lumina.core.pack_contract import validate_pack_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.unit
def test_business_ops_pack_manifest_validates() -> None:
    manifest = validate_pack_manifest(REPO_ROOT / "model-packs" / "business-ops" / "pack.yaml")
    assert manifest["pack_id"] == "business-ops"
    assert manifest["default_module"] == "auto-repair"
    assert "modules" in manifest


@pytest.mark.unit
def test_invalid_pack_manifest_rejects_missing_required_fields(tmp_path: Path) -> None:
    pack_path = tmp_path / "pack.yaml"
    pack_path.write_text(
        "pack_id: bad\nversion: \"0.1.0\"\n" "modules:\n  - foo\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="default_module|required"):
        validate_pack_manifest(pack_path)


@pytest.mark.unit
def test_invalid_pack_manifest_rejects_missing_runtime_config_file(tmp_path: Path) -> None:
    pack_path = tmp_path / "pack.yaml"
    pack_path.write_text(
        "pack_id: missing-runtime-config\n"
        "version: \"0.1.0\"\n"
        "description: \"Pack with missing runtime config\"\n"
        "layers:\n"
        "  model:\n"
        "    - modules/\n"
        "  controller:\n"
        "    - controllers/\n"
        "  domain_lib:\n"
        "    - domain-lib/\n"
        "  view:\n"
        "    - prompts/\n"
        "  docs:\n"
        "    - docs/\n"
        "modules:\n"
        "  - foo\n"
        "default_module: foo\n"
        "entry_points:\n"
        "  runtime_config: cfg/runtime-config.yaml\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="runtime_config.*not exist|runtime_config.*missing|runtime_config"):
        validate_pack_manifest(pack_path)


@pytest.mark.unit
def test_valid_pack_manifest_accepts_structured_optional_metadata(tmp_path: Path) -> None:
    pack_path = tmp_path / "pack.yaml"
    runtime_cfg_dir = tmp_path / "cfg"
    runtime_cfg_dir.mkdir(parents=True, exist_ok=True)
    (runtime_cfg_dir / "runtime-config.yaml").write_text("runtime: {}\n", encoding="utf-8")
    pack_path.write_text(
        "pack_id: demo-pack\n"
        "version: \"0.2.0\"\n"
        "description: \"Demo pack with structured metadata\"\n"
        "owner: demo-team\n"
        "vertical_type: seed_vertical\n"
        "scope:\n"
        "  organization_id: org-1\n"
        "  site_id: site-1\n"
        "routing_defaults:\n"
        "  default_role: operator\n"
        "module_map:\n"
        "  demo-module:\n"
        "    route: demo-module\n"
        "metadata:\n"
        "  source: internal\n"
        "maintainers:\n"
        "  - demo@example.com\n"
        "contract_version: v1\n"
        "compatibility:\n"
        "  major: 0\n"
        "  back_compatible: true\n"
        "notes: Demo pack contract\n"
        "layers:\n"
        "  model:\n"
        "    - modules/\n"
        "  controller:\n"
        "    - controllers/\n"
        "  domain_lib:\n"
        "    - domain-lib/\n"
        "  view:\n"
        "    - prompts/\n"
        "  docs:\n"
        "    - docs/\n"
        "modules:\n"
        "  - demo-module\n"
        "default_module: demo-module\n"
        "entry_points:\n"
        "  runtime_config: cfg/runtime-config.yaml\n",
        encoding="utf-8",
    )

    manifest = validate_pack_manifest(pack_path)
    assert manifest["vertical_type"] == "seed_vertical"
    assert manifest["routing_defaults"]["default_role"] == "operator"


@pytest.mark.unit
def test_invalid_pack_manifest_rejects_malformed_optional_metadata(tmp_path: Path) -> None:
    pack_path = tmp_path / "pack.yaml"
    runtime_cfg_dir = tmp_path / "cfg"
    runtime_cfg_dir.mkdir(parents=True, exist_ok=True)
    (runtime_cfg_dir / "runtime-config.yaml").write_text("runtime: {}\n", encoding="utf-8")
    pack_path.write_text(
        "pack_id: demo-pack\n"
        "version: \"0.2.0\"\n"
        "description: \"Demo pack with malformed metadata\"\n"
        "maintainers: owner@example.com\n"
        "routing_defaults: non-mapping\n"
        "layers:\n"
        "  model:\n"
        "    - modules/\n"
        "  controller:\n"
        "    - controllers/\n"
        "  domain_lib:\n"
        "    - domain-lib/\n"
        "  view:\n"
        "    - prompts/\n"
        "  docs:\n"
        "    - docs/\n"
        "modules:\n"
        "  - demo-module\n"
        "default_module: demo-module\n"
        "entry_points:\n"
        "  runtime_config: cfg/runtime-config.yaml\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="maintainers|routing_defaults"):
        validate_pack_manifest(pack_path)

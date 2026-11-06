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

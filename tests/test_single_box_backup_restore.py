from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from zipfile import ZipFile

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = REPO_ROOT / "scripts" / "single_box_backup_restore.py"


@pytest.fixture(scope="module")
def backup_mod():
    spec = importlib.util.spec_from_file_location("single_box_backup_restore", _SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _seed_artifacts(repo_root: Path) -> None:
    paths = [
        repo_root / "data" / "profiles" / "u1" / "business-ops.yaml",
        repo_root / "data" / "retrieval-index" / "chunks.jsonl",
        repo_root / "data" / "knowledge-index" / "graph.json",
        repo_root / "data" / "blackbox" / "snap-1.json",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("seed\n", encoding="utf-8")


def test_create_backup_writes_archive_and_manifest(tmp_path: Path, backup_mod):
    _seed_artifacts(tmp_path)
    output_dir = tmp_path / "data" / "staging" / "backups"

    result = backup_mod.create_backup(
        repo_root=tmp_path,
        output_dir=output_dir,
        include_dirs=backup_mod.DEFAULT_ARTIFACT_DIRS,
        retention_limit=5,
    )

    archive = Path(result["archive"])
    assert archive.exists()
    assert result["manifest"]["file_count"] == 4

    with ZipFile(archive, "r") as zf:
        assert backup_mod.MANIFEST_NAME in zf.namelist()
        manifest = json.loads(zf.read(backup_mod.MANIFEST_NAME).decode("utf-8"))
    assert manifest["profile"] == "single-box-v1"


def test_restore_backup_recovers_overwritten_file(tmp_path: Path, backup_mod):
    _seed_artifacts(tmp_path)
    output_dir = tmp_path / "data" / "staging" / "backups"

    result = backup_mod.create_backup(
        repo_root=tmp_path,
        output_dir=output_dir,
        include_dirs=backup_mod.DEFAULT_ARTIFACT_DIRS,
        retention_limit=5,
    )
    archive = Path(result["archive"])

    target = tmp_path / "data" / "profiles" / "u1" / "business-ops.yaml"
    target.write_text("changed\n", encoding="utf-8")

    restore = backup_mod.restore_backup(
        repo_root=tmp_path,
        archive_path=archive,
        dry_run=False,
    )
    assert restore["restored_file_count"] >= 1
    assert target.read_text(encoding="utf-8") == "seed\n"


def test_prune_backups_keeps_newest(tmp_path: Path, backup_mod):
    backup_dir = tmp_path / "data" / "staging" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    names = [
        "single-box-backup-20260101T000000Z.zip",
        "single-box-backup-20260102T000000Z.zip",
        "single-box-backup-20260103T000000Z.zip",
    ]
    for name in names:
        (backup_dir / name).write_text("x", encoding="utf-8")

    removed = backup_mod.prune_backups(backup_dir, keep=2)
    assert len(removed) == 1
    remaining = [p.name for p in backup_mod.list_backups(backup_dir)]
    assert remaining == names[1:]


def test_restore_rejects_unsafe_archive_member(tmp_path: Path, backup_mod):
    archive = tmp_path / "bad.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("../escape.txt", "bad")

    with pytest.raises(RuntimeError):
        backup_mod.restore_backup(repo_root=tmp_path, archive_path=archive, dry_run=False)

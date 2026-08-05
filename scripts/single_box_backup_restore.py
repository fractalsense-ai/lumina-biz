#!/usr/bin/env python3
"""Single-box backup/restore with deterministic retention pruning.

Backs up local institutional-memory artifact directories into a zip archive,
restores from an archive, and prunes old backups by keep-count.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

DEFAULT_ARTIFACT_DIRS = (
    "data/profiles",
    "data/retrieval-index",
    "data/knowledge-index",
    "data/blackbox",
)
BACKUP_PREFIX = "single-box-backup"
MANIFEST_NAME = "backup-manifest.json"


def _utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _to_abs(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _safe_rel(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def list_backups(output_dir: Path) -> list[Path]:
    backups = [p for p in output_dir.glob(f"{BACKUP_PREFIX}-*.zip") if p.is_file()]
    backups.sort(key=lambda p: p.name)
    return backups


def prune_backups(output_dir: Path, keep: int) -> list[str]:
    if keep < 0:
        raise ValueError("keep must be >= 0")
    backups = list_backups(output_dir)
    if keep >= len(backups):
        return []
    to_remove = backups[: len(backups) - keep]
    removed: list[str] = []
    for item in to_remove:
        item.unlink()
        removed.append(str(item))
    return removed


def _collect_files(repo_root: Path, include_dirs: tuple[str, ...]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    included_dirs: list[str] = []
    for rel_dir in include_dirs:
        abs_dir = _to_abs(repo_root, rel_dir)
        if not abs_dir.exists():
            continue
        included_dirs.append(_safe_rel(abs_dir, repo_root))
        for item in abs_dir.rglob("*"):
            if item.is_file():
                files.append(item)
    files.sort()
    return files, included_dirs


def create_backup(
    *,
    repo_root: Path,
    output_dir: Path,
    include_dirs: tuple[str, ...],
    retention_limit: int,
) -> dict[str, Any]:
    if retention_limit < 0:
        raise ValueError("retention_limit must be >= 0")

    output_dir.mkdir(parents=True, exist_ok=True)
    files, included_dirs = _collect_files(repo_root, include_dirs)
    if not files:
        raise RuntimeError("No artifact files found for backup")

    stamp = _utc_stamp()
    archive_name = f"{BACKUP_PREFIX}-{stamp}.zip"
    archive_path = output_dir / archive_name

    manifest = {
        "schema_version": "1.0.0",
        "profile": "single-box-v1",
        "created_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "repo_root": str(repo_root),
        "included_dirs": included_dirs,
        "file_count": len(files),
        "archive_name": archive_name,
    }

    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as zf:
        for file_path in files:
            zf.write(file_path, arcname=_safe_rel(file_path, repo_root))
        zf.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2, ensure_ascii=True) + "\n")

    removed = prune_backups(output_dir, retention_limit)
    return {
        "status": "ok",
        "operation": "backup",
        "archive": str(archive_path),
        "manifest": manifest,
        "retention_limit": retention_limit,
        "removed_backups": removed,
    }


def _safe_extract_member(repo_root: Path, member_name: str) -> Path:
    target = (repo_root / member_name).resolve()
    repo_resolved = repo_root.resolve()
    if repo_resolved == target or repo_resolved in target.parents:
        return target
    raise RuntimeError(f"Unsafe archive member path: {member_name}")


def restore_backup(*, repo_root: Path, archive_path: Path, dry_run: bool = False) -> dict[str, Any]:
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    restored_files: list[str] = []
    manifest_data: dict[str, Any] | None = None

    with ZipFile(archive_path, "r") as zf:
        for member in zf.infolist():
            name = member.filename.replace("\\", "/")
            if name.endswith("/") or name == MANIFEST_NAME:
                if name == MANIFEST_NAME:
                    manifest_data = json.loads(zf.read(member).decode("utf-8"))
                continue
            target = _safe_extract_member(repo_root, name)
            restored_files.append(str(target))
            if dry_run:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member, "r") as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)

    return {
        "status": "ok",
        "operation": "restore",
        "archive": str(archive_path),
        "dry_run": dry_run,
        "restored_file_count": len(restored_files),
        "restored_files": restored_files,
        "manifest": manifest_data,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-box backup/restore and retention pruning")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root path",
    )
    parser.add_argument("--json-out", type=Path, default=None, help="Optional JSON report output path")

    sub = parser.add_subparsers(dest="command", required=True)

    backup = sub.add_parser("backup", help="Create a new backup archive")
    backup.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/staging/backups"),
        help="Directory where backups are stored",
    )
    backup.add_argument(
        "--include-dir",
        action="append",
        dest="include_dirs",
        default=None,
        help="Repo-relative directory to include (repeatable)",
    )
    backup.add_argument(
        "--retention-limit",
        type=int,
        default=5,
        help="Number of newest backup archives to keep",
    )

    restore = sub.add_parser("restore", help="Restore from a backup archive")
    restore.add_argument("--archive", type=Path, required=True, help="Backup archive path")
    restore.add_argument("--dry-run", action="store_true", help="Report files without writing them")

    prune = sub.add_parser("prune", help="Prune old backups")
    prune.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/staging/backups"),
        help="Directory where backups are stored",
    )
    prune.add_argument("--keep", type=int, required=True, help="Number of newest backups to keep")

    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = args.repo_root.resolve()

    if args.command == "backup":
        include_dirs = tuple(args.include_dirs) if args.include_dirs else DEFAULT_ARTIFACT_DIRS
        result = create_backup(
            repo_root=repo_root,
            output_dir=_to_abs(repo_root, args.output_dir),
            include_dirs=include_dirs,
            retention_limit=args.retention_limit,
        )
    elif args.command == "restore":
        result = restore_backup(
            repo_root=repo_root,
            archive_path=_to_abs(repo_root, args.archive),
            dry_run=bool(args.dry_run),
        )
    else:
        output_dir = _to_abs(repo_root, args.output_dir)
        removed = prune_backups(output_dir, int(args.keep))
        result = {
            "status": "ok",
            "operation": "prune",
            "output_dir": str(output_dir),
            "keep": int(args.keep),
            "removed_backups": removed,
        }

    rendered = json.dumps(result, indent=2, ensure_ascii=True)
    if args.json_out is not None:
        out_path = _to_abs(repo_root, args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

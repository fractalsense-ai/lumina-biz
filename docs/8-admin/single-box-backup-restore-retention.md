---
version: 1.0.0
last_updated: 2026-08-05
---

# Single-Box Backup, Restore, and Retention Controls

This runbook defines deterministic backup and restore controls for single-box pilot operations.

## Scope

The backup utility covers local institutional-memory artifacts:
- `data/profiles`
- `data/retrieval-index`
- `data/knowledge-index`
- `data/blackbox`

Archives are written as zip files to `data/staging/backups` by default.

## Commands

### Create backup

```bash
python scripts/single_box_backup_restore.py backup --retention-limit 5
```

PowerShell helper:

```powershell
./scripts/run-single-box-backup.ps1 -Action backup -Keep 5
```

### Restore backup

```bash
python scripts/single_box_backup_restore.py restore --archive data/staging/backups/single-box-backup-YYYYMMDDTHHMMSSZ.zip
```

Dry-run restore (no writes):

```bash
python scripts/single_box_backup_restore.py restore --archive data/staging/backups/single-box-backup-YYYYMMDDTHHMMSSZ.zip --dry-run
```

### Prune backups

```bash
python scripts/single_box_backup_restore.py prune --keep 5
```

## Retention Semantics

- `backup --retention-limit N` creates one new archive, then prunes oldest backups so only the newest `N` remain.
- `prune --keep N` prunes without creating a new backup.
- `N=0` removes all matching backup archives.

## Safety Controls

- Restore rejects unsafe archive member paths to prevent path traversal.
- Restore writes only archive members rooted under the repository path.
- A `backup-manifest.json` is embedded in every archive with profile id, included directories, and file count.

## Operator Workflow

1. Run backup before maintenance or migration events.
2. Verify archive exists in `data/staging/backups` and capture CLI JSON output as evidence.
3. If recovery is needed, run restore first with `--dry-run`, then run actual restore.
4. Re-run single-box smoke checks after restore.

## Validation

PR2 validation is covered by deterministic tests in:
- `tests/test_single_box_backup_restore.py`

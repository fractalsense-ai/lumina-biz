"""
scheduler.py -- Daemon task scheduler.

Provides a scheduler that can be driven by cron (external trigger),
by the daemon, or by manual API invocation. Keeps history of runs
and their proposals.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
from typing import Any, Callable

from lumina.daemon.report import DaemonReport, TaskResult
from lumina.daemon.task_adapter import cross_domain_execution_path_allowed
from lumina.daemon.tasks import get_task, get_cross_domain_task, list_tasks, list_cross_domain_tasks

log = logging.getLogger("lumina-daemon")


_DAEMON_AUDIT_COMMIT_PARITY_CONTRACT = "daemon_audit_commit_parity_v1"
_DAEMON_AUDIT_COMMIT_MISSING_REASON = "daemon_audit_commit_missing"


class DaemonScheduler:
    """Manages and executes daemon batch runs."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        domain_loader: Callable[[], list[dict[str, Any]]] | None = None,
        persistence: Any = None,
        call_slm_fn: Callable[..., str] | None = None,
    ) -> None:
        self._config = config or {}
        self._domain_loader = domain_loader  # returns list of {domain_id, physics}
        self._persistence = persistence
        self._call_slm_fn = call_slm_fn
        self._lock = threading.Lock()

        # Run history (most recent first)
        self._runs: list[DaemonReport] = []
        self._max_history = 50

        # Current run (if in progress)
        self._current_run: DaemonReport | None = None

    # ── Configuration helpers ─────────────────────────────────

    @property
    def enabled(self) -> bool:
        return bool(self._config.get("enabled", False))

    @property
    def configured_tasks(self) -> list[str]:
        return list(self._config.get("tasks") or list_tasks())

    @property
    def max_duration_minutes(self) -> int:
        return int(self._config.get("max_duration_minutes", 240))

    @property
    def schedule(self) -> str:
        return str(self._config.get("schedule", "0 2 * * *"))

    # ── Status ────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            current = self._current_run
            last = self._runs[0] if self._runs else None

        return {
            "enabled": self.enabled,
            "schedule": self.schedule,
            "is_running": current is not None,
            "current_run_id": current.run_id if current else None,
            "last_run": last.to_dict() if last else None,
            "run_count": len(self._runs),
        }

    def get_report(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            if self._current_run and self._current_run.run_id == run_id:
                return self._current_run.to_dict()
            for run in self._runs:
                if run.run_id == run_id:
                    return run.to_dict()
        return None

    def get_pending_proposals(self, domain_id: str | None = None) -> list[dict[str, Any]]:
        proposals: list[dict[str, Any]] = []
        with self._lock:
            for run in self._runs:
                for result in run.task_results:
                    for prop in result.proposals:
                        if prop.status != "pending":
                            continue
                        if domain_id and prop.domain_id != domain_id:
                            continue
                        proposals.append(prop.to_dict())
        return proposals

    def resolve_proposal(
        self,
        proposal_id: str,
        action: str,
        domain_id: str | None = None,
    ) -> bool:
        """Approve or reject a pending proposal.  Returns True if found.

        For cross-domain proposals with ``required_approvers``, pass
        *domain_id* to record one domain authority's decision.  The
        overall status is recomputed automatically.
        """
        if action not in ("approved", "rejected"):
            return False
        with self._lock:
            for run in self._runs:
                for result in run.task_results:
                    for prop in result.proposals:
                        if prop.proposal_id == proposal_id:
                            if prop.required_approvers and domain_id:
                                prop.resolve_approval(domain_id, action)
                            else:
                                prop.status = action
                            return True
        return False

    # ── Execution ─────────────────────────────────────────────

    def trigger_manual(
        self,
        actor_id: str,
        task_names: list[str] | None = None,
        domain_ids: list[str] | None = None,
    ) -> DaemonReport:
        """Execute a daemon batch run synchronously. Returns the report."""
        return self._execute(
            triggered_by=actor_id,
            task_names=task_names or self.configured_tasks,
            domain_ids=domain_ids,
        )

    def trigger_scheduled(self) -> DaemonReport:
        """Execute a scheduled daemon batch run."""
        return self._execute(
            triggered_by="scheduler",
            task_names=self.configured_tasks,
        )

    def trigger_async(
        self,
        actor_id: str,
        task_names: list[str] | None = None,
        domain_ids: list[str] | None = None,
    ) -> str:
        """Start a daemon batch run in a background thread. Returns run_id."""
        report = DaemonReport(triggered_by=actor_id)
        run_id = report.run_id

        def _run() -> None:
            self._execute(
                triggered_by=actor_id,
                task_names=task_names or self.configured_tasks,
                domain_ids=domain_ids,
                prebuilt_report=report,
            )

        thread = threading.Thread(target=_run, daemon=True, name=f"daemon-batch-{run_id}")
        thread.start()
        return run_id

    def _execute(
        self,
        triggered_by: str,
        task_names: list[str],
        domain_ids: list[str] | None = None,
        prebuilt_report: DaemonReport | None = None,
    ) -> DaemonReport:
        report = prebuilt_report or DaemonReport(triggered_by=triggered_by)

        with self._lock:
            if self._current_run is not None:
                report.status = "failed"
                report.finish()
                return report
            self._current_run = report

        try:
            domains = self._load_domains(domain_ids)
            deadline = time.monotonic() + self.max_duration_minutes * 60

            for task_name in task_names:
                if time.monotonic() > deadline:
                    log.warning("Daemon batch exceeded max duration, stopping")
                    break

                task_fn = get_task(task_name)
                if task_fn is None:
                    log.warning("Unknown daemon task: %s", task_name)
                    continue

                for domain in domains:
                    domain_id = domain.get("domain_id", "unknown")
                    domain_physics = domain.get("physics", {})
                    try:
                        result = task_fn(
                            domain_id=domain_id,
                            domain_physics=domain_physics,
                            persistence=self._persistence,
                            call_slm_fn=self._call_slm_fn,
                        )
                        if not isinstance(result, TaskResult):
                            result = TaskResult(
                                task=task_name,
                                domain_id=domain_id,
                                success=True,
                            )
                    except Exception as exc:
                        log.error("Task %s failed for %s: %s", task_name, domain_id, exc)
                        result = TaskResult(
                            task=task_name,
                            domain_id=domain_id,
                            success=False,
                            error=str(exc),
                        )

                    self._enforce_audit_commit_parity(
                        result,
                        triggered_by=triggered_by,
                        scope_domain_id=domain_id,
                    )
                    report.task_results.append(result)

            # ── Cross-domain tasks ──────────────────────────────
            # These receive the full list of opt-in domains rather than
            # iterating per-domain.  Only run on full (unfiltered) runs —
            # when domain_ids is specified the caller wants a targeted run
            # on specific domains, not cross-domain analysis.
            cross_domain_task_names = list_cross_domain_tasks()
            if (cross_domain_task_names
                    and domain_ids is None
                    and time.monotonic() <= deadline):
                for task_name in cross_domain_task_names:
                    if time.monotonic() > deadline:
                        log.warning("Daemon batch exceeded max duration during cross-domain tasks")
                        break

                    execution_path = "daemon_api"
                    if not cross_domain_execution_path_allowed(execution_path):
                        result = TaskResult(
                            task=task_name,
                            domain_id="cross_domain",
                            success=False,
                            error="Cross-domain task denied by API-only boundary",
                            metadata={
                                "denied": True,
                                "denial_reason": "cross_domain_api_only_boundary",
                                "boundary": {
                                    "contract": "cross_domain_api_only_enforcement_v1",
                                    "execution_path": execution_path,
                                    "status": "denied",
                                },
                            },
                        )
                        self._enforce_audit_commit_parity(
                            result,
                            triggered_by=triggered_by,
                            scope_domain_id="cross_domain",
                        )
                        report.task_results.append(result)
                        continue

                    cd_task_fn = get_cross_domain_task(task_name)
                    if cd_task_fn is None:
                        continue

                    try:
                        result = cd_task_fn(
                            domains=domains,
                            persistence=self._persistence,
                        )
                        if not isinstance(result, TaskResult):
                            result = TaskResult(
                                task=task_name,
                                domain_id="cross_domain",
                                success=True,
                            )
                    except Exception as exc:
                        log.error("Cross-domain task %s failed: %s", task_name, exc)
                        result = TaskResult(
                            task=task_name,
                            domain_id="cross_domain",
                            success=False,
                            error=str(exc),
                        )

                    self._enforce_audit_commit_parity(
                        result,
                        triggered_by=triggered_by,
                        scope_domain_id="cross_domain",
                    )
                    report.task_results.append(result)

            report.finish()
        finally:
            with self._lock:
                self._current_run = None
                self._runs.insert(0, report)
                if len(self._runs) > self._max_history:
                    self._runs = self._runs[:self._max_history]

        log.info(
            "Daemon batch %s finished: %s tasks, %d proposals",
            report.run_id,
            report.status,
            report.total_proposals,
        )
        return report

    def _load_domains(self, domain_ids: list[str] | None = None) -> list[dict[str, Any]]:
        """Load domains from the domain_loader callback or return a fallback."""
        if self._domain_loader is None:
            return [{"domain_id": "default", "physics": {}}]

        domains = self._domain_loader()
        if domain_ids:
            domains = [d for d in domains if d.get("domain_id") in domain_ids]
        return domains or [{"domain_id": "default", "physics": {}}]

    # ── Opportunistic (daemon-driven) ─────────────────────────

    def trigger_opportunistic(
        self,
        task_name: str,
        domain_ids: list[str] | None = None,
    ) -> DaemonReport:
        """Execute a single task for all (or selected) domains.

        Called by the Resource Monitor Daemon when the system is idle.
        Unlike ``trigger_manual`` this runs exactly one task, not the
        full daemon batch suite, making it suitable for interleaved
        opportunistic scheduling.

        Returns a ``DaemonReport`` containing results for the
        single task across the targeted domains.
        """
        return self._execute(
            triggered_by="daemon",
            task_names=[task_name],
            domain_ids=domain_ids,
        )

    # ── N5 audit-commit parity enforcement ───────────────────

    def _build_daemon_audit_trace_event(
        self,
        *,
        task_result: TaskResult,
        triggered_by: str,
        scope_domain_id: str,
        session_id: str,
        prev_record_hash: str,
    ) -> dict[str, Any]:
        decision = f"daemon_task:{task_result.task}:{'ok' if task_result.success else 'failed'}"
        return {
            "record_type": "TraceEvent",
            "record_id": str(uuid.uuid4()),
            "prev_record_hash": prev_record_hash,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "event_type": "other",
            "actor_id": triggered_by,
            "decision": decision[:256],
            "metadata": {
                "task": task_result.task,
                "domain_id": scope_domain_id,
                "duration_seconds": task_result.duration_seconds,
                "success": task_result.success,
                "error": task_result.error,
                "parity_contract": _DAEMON_AUDIT_COMMIT_PARITY_CONTRACT,
            },
        }

    @staticmethod
    def _hash_record(record: dict[str, Any]) -> str:
        canonical = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    @staticmethod
    def _daemon_audit_session_id(scope_domain_id: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"lumina:daemon-audit:{scope_domain_id}"))

    def _derive_prev_record_hash(self, *, session_id: str, ledger_path: str | None) -> str:
        if ledger_path and not ledger_path.startswith("sqlite://"):
            path = Path(ledger_path)
            if path.exists():
                try:
                    with open(path, encoding="utf-8") as fh:
                        lines = [ln.strip() for ln in fh if ln.strip()]
                    if lines:
                        last_record = json.loads(lines[-1])
                        if isinstance(last_record, dict):
                            return self._hash_record(last_record)
                except Exception:
                    log.debug("daemon audit parity: could not read ledger tail", exc_info=True)

        if self._persistence is not None:
            query_fn = getattr(self._persistence, "query_log_records", None)
            if callable(query_fn):
                try:
                    records = query_fn(session_id=session_id, limit=1, offset=0)
                    if records:
                        latest = records[0]
                        if isinstance(latest, dict):
                            return self._hash_record(latest)
                except Exception:
                    log.debug("daemon audit parity: could not query latest ledger record", exc_info=True)

        return "genesis"

    def _append_daemon_audit_record(
        self,
        scope_domain_id: str,
        session_id: str,
        record: dict[str, Any],
    ) -> bool | None:
        if self._persistence is None:
            return None

        append_fn = getattr(self._persistence, "append_log_record", None)
        if not callable(append_fn):
            return None

        try:
            ledger_path: Any = None
            ledger_getter = getattr(self._persistence, "get_system_ledger_path", None)
            if callable(ledger_getter):
                ledger_path = ledger_getter(scope_domain_id)
            append_fn(session_id, record, ledger_path=ledger_path)
            return True
        except Exception:
            log.warning("daemon audit parity: failed to append audit record", exc_info=True)
            return False

    def _enforce_audit_commit_parity(
        self,
        task_result: TaskResult,
        *,
        triggered_by: str,
        scope_domain_id: str,
    ) -> None:
        session_id = self._daemon_audit_session_id(scope_domain_id)
        ledger_path: str | None = None
        if self._persistence is not None:
            ledger_getter = getattr(self._persistence, "get_system_ledger_path", None)
            if callable(ledger_getter):
                try:
                    ledger_path = ledger_getter(scope_domain_id)
                except Exception:
                    ledger_path = None

        prev_record_hash = self._derive_prev_record_hash(
            session_id=session_id,
            ledger_path=ledger_path,
        )

        audit_event = self._build_daemon_audit_trace_event(
            task_result=task_result,
            triggered_by=triggered_by,
            scope_domain_id=scope_domain_id,
            session_id=session_id,
            prev_record_hash=prev_record_hash,
        )
        committed = self._append_daemon_audit_record(scope_domain_id, session_id, audit_event)

        task_result.metadata.setdefault("audit_commit_parity", {})
        task_result.metadata["audit_commit_parity"].update({
            "contract": _DAEMON_AUDIT_COMMIT_PARITY_CONTRACT,
            "status": (
                "committed"
                if committed is True
                else "missing"
                if committed is False
                else "unavailable"
            ),
        })

        # Parity rule mirrors API commit guard semantics: successful operations
        # must leave an audit commitment.
        if task_result.success and committed is False:
            task_result.success = False
            task_result.error = "Daemon task completed without audit commitment"
            task_result.metadata["audit_commit_parity"].update({
                "denied": True,
                "denial_reason": _DAEMON_AUDIT_COMMIT_MISSING_REASON,
            })

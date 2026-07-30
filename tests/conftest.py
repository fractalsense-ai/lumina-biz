from __future__ import annotations

from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


# Legacy suites pinned to removed education/agriculture/assistant pack behavior.
# Keep these out of collection in the split repo to avoid false CI failures.
_LEGACY_SPLIT_TESTS = {
    "test_admin_command_regressions.py",
    "test_assign_modules.py",
    "test_assistant_domain_pack.py",
    "test_baseline_before_escalation.py",
    "test_dashboard_roster_status.py",
    "test_domain_lib_reference_specs.py",
    "test_escalation_prevention.py",
    "test_escalation_routing.py",
    "test_escalation_unlock.py",
    "test_fluency_monitor.py",
    "test_hierarchy_visibility.py",
    "test_invariant_source_and_verification.py",
    "test_journal_sva_module.py",
    "test_journal_session_start.py",
    "test_module_switch_ux.py",
    "test_nlp_pre_interpreter.py",
    "test_profile_state_separation.py",
    "test_problem_generator.py",
    "test_rag_module_scoping.py",
    "test_routes_vocabulary.py",
    "test_round2_fixes.py",
    "test_signals_agriculture_poc.py",
    "test_sse_and_events.py",
    "test_tool_adapter_new_checks.py",
    "test_trip_module.py",
    "test_user_module_management.py",
    "test_vocabulary_growth_monitor.py",
    "test_zpd_monitor.py",
}


# pytest reads this at collection start and skips matching modules entirely.
collect_ignore = sorted(_LEGACY_SPLIT_TESTS)


def merge_module_config_sidecars(module_map: dict) -> dict:
    """Merge module-config.yaml sidecars into raw module_map entries.

    Replicates the runtime-loader auto-discovery so tests that read
    runtime-config.yaml directly see the full merged configuration.
    Inline keys always win (same semantics as the loader).
    """
    for _mod_cfg in module_map.values():
        _mod_dir = _mod_cfg.get("module_path")
        if _mod_dir:
            _mc_path = REPO_ROOT / _mod_dir / "module-config.yaml"
            if _mc_path.is_file():
                with open(_mc_path, encoding="utf-8") as f:
                    _mc = yaml.safe_load(f)
                if isinstance(_mc, dict):
                    for _k, _v in _mc.items():
                        if _k not in _mod_cfg:
                            _mod_cfg[_k] = _v
    return module_map


@pytest.fixture(autouse=True)
def _mount_domain_routes_if_loaded(request):
    """Ensure domain-declared API routes are available during tests.

    The domain routes are normally mounted by the FastAPI lifespan
    startup handler, but many test suites create a ``TestClient`` without
    entering the application lifecycle.  This fixture calls
    ``_mount_domain_api_routes()`` automatically when an ``api_module``
    fixture is in scope.
    """
    api_module = request.fixturenames
    if "api_module" not in api_module:
        return
    # Resolve the fixture (only works when the fixture is actually declared).
    try:
        mod = request.getfixturevalue("api_module")
    except pytest.FixtureLookupError:
        return
    mount_fn = getattr(mod, "_mount_domain_api_routes", None)
    if mount_fn is not None:
        mount_fn()

"""Project Lumina PPA orchestrator demo (domain-neutral system-core run).

This script demonstrates the full D.S.A. loop without business-ops-specific
wiring. It uses the system-core domain physics and invariant-driven actions,
which makes it easier to understand for institutional-knowledge and
business-ops contexts.
"""

from __future__ import annotations

import json
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[3]
_SRC_ROOT = _REPO_ROOT / "src"

if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lumina.orchestrator.ppa_orchestrator import PPAOrchestrator, load_domain_physics  # noqa: E402
from lumina.core.yaml_loader import load_yaml  # noqa: E402
from lumina.systools.system_log_validator import load_ledger, verify_chain  # noqa: E402

_DOMAIN_PHYSICS_PATH = (
    _REPO_ROOT / "model-packs" / "system" / "modules" / "system-core" / "domain-physics.json"
)
_OPTIONAL_PROFILE_PATH = (
    _REPO_ROOT / "model-packs" / "system" / "modules" / "system-core" / "example-operator-profile.yaml"
)

_FALLBACK_PROFILE: dict[str, Any] = {
    "subject_id": "ops-demo-001",
    "display_name": "Ops Demo",
    "organization_id": "org-demo",
    "site_id": "site-demo",
    "preferences": {
        "language": "en",
        "operator_mode": "system-core",
    },
}


TURNS: list[tuple[str, dict[str, Any], dict[str, Any]]] = [
    (
        "Turn 1: Grounded status summary request",
        {
            "task_id": "sys-task-001",
            "nominal_difficulty": 0.30,
            "skills_required": ["audit", "operational_monitoring"],
        },
        {
            "autonomous_policy_decision": False,
            "internal_state_disclosed": False,
            "response_grounded_in_prompt_contract": True,
            "direct_state_change_attempted": False,
            "json_in_output": False,
            "chain_of_thought_in_output": False,
        },
    ),
    (
        "Turn 2: Ungrounded response attempt",
        {
            "task_id": "sys-task-002",
            "nominal_difficulty": 0.35,
            "skills_required": ["policy_gate", "session_diagnostics"],
        },
        {
            "autonomous_policy_decision": False,
            "internal_state_disclosed": False,
            "response_grounded_in_prompt_contract": False,
            "direct_state_change_attempted": False,
            "json_in_output": False,
            "chain_of_thought_in_output": False,
        },
    ),
    (
        "Turn 3: Direct state mutation attempt",
        {
            "task_id": "sys-task-003",
            "nominal_difficulty": 0.45,
            "skills_required": ["rbac_inspection", "policy_gate"],
        },
        {
            "autonomous_policy_decision": False,
            "internal_state_disclosed": False,
            "response_grounded_in_prompt_contract": True,
            "direct_state_change_attempted": True,
            "json_in_output": False,
            "chain_of_thought_in_output": False,
        },
    ),
    (
        "Turn 4: Raw JSON leakage",
        {
            "task_id": "sys-task-004",
            "nominal_difficulty": 0.40,
            "skills_required": ["audit", "domain_physics_review"],
        },
        {
            "autonomous_policy_decision": False,
            "internal_state_disclosed": False,
            "response_grounded_in_prompt_contract": True,
            "direct_state_change_attempted": False,
            "json_in_output": True,
            "chain_of_thought_in_output": False,
        },
    ),
    (
        "Turn 5: Internal reasoning leakage",
        {
            "task_id": "sys-task-005",
            "nominal_difficulty": 0.42,
            "skills_required": ["system_administration", "policy_gate"],
        },
        {
            "autonomous_policy_decision": False,
            "internal_state_disclosed": False,
            "response_grounded_in_prompt_contract": True,
            "direct_state_change_attempted": False,
            "json_in_output": False,
            "chain_of_thought_in_output": True,
        },
    ),
    (
        "Turn 6: Autonomous policy decision attempt",
        {
            "task_id": "sys-task-006",
            "nominal_difficulty": 0.50,
            "skills_required": ["escalation_review", "rbac_inspection"],
        },
        {
            "autonomous_policy_decision": True,
            "internal_state_disclosed": False,
            "response_grounded_in_prompt_contract": True,
            "direct_state_change_attempted": False,
            "json_in_output": False,
            "chain_of_thought_in_output": False,
        },
    ),
    (
        "Turn 7: Recovery with all safeguards green",
        {
            "task_id": "sys-task-007",
            "nominal_difficulty": 0.30,
            "skills_required": ["audit", "session_diagnostics"],
        },
        {
            "autonomous_policy_decision": False,
            "internal_state_disclosed": False,
            "response_grounded_in_prompt_contract": True,
            "direct_state_change_attempted": False,
            "json_in_output": False,
            "chain_of_thought_in_output": False,
        },
    ),
]


def _sep(char: str = "-", width: int = 72) -> None:
    print(char * width)


def _print_invariant_results(results: list[dict[str, Any]]) -> None:
    if not results:
        print("  Invariants: (no invariant evidence evaluated this turn)")
        return
    for result in results:
        icon = "PASS" if result.get("passed") else "FAIL"
        sev = str(result.get("severity", "")).upper()[:4]
        note = ""
        if not result.get("passed"):
            standing = result.get("standing_order_on_violation")
            if standing:
                note = f" -> {standing}"
        print(f"  [{icon}] {result.get('id', 'unknown'):<36} ({sev}){note}")


def _simulate_operator_response(contract: dict[str, Any]) -> str:
    prompt_type = str(contract.get("prompt_type", "task_presentation"))
    task_id = str(contract.get("task_id", "unknown-task"))
    messages = {
        "task_presentation": f"Please review task {task_id} and provide a contract-grounded response.",
        "enforce_contract_boundaries": "Action blocked: output must stay within active contract boundaries.",
        "retract_and_self_correct": "Previous output retracted. Reissuing a compliant response.",
        "strip_and_reformat_output": "Output reformatted to remove raw JSON/internal reasoning.",
        "escalate": "Issue escalated to a human operator for review.",
    }
    return messages.get(prompt_type, f"[{prompt_type}]")


def run_demo() -> None:
    _sep("=")
    print("  Project Lumina - PPA Orchestrator Demo (System Core)")
    print("  Domain: System Core  |  Subject: Ops Demo")
    _sep("=")

    print("\nLoading domain physics from:")
    print(f"  {_DOMAIN_PHYSICS_PATH}")
    domain = load_domain_physics(_DOMAIN_PHYSICS_PATH)
    print(f"  -> {domain['id']}  v{domain['version']}")
    print(f"  -> {len(domain.get('invariants', []))} invariants, {len(domain.get('standing_orders', []))} standing orders")

    print("\nLoading optional profile from:")
    print(f"  {_OPTIONAL_PROFILE_PATH}")
    try:
        profile = load_yaml(_OPTIONAL_PROFILE_PATH)
        if not profile.get("organization_id") or not profile.get("site_id"):
            raise ValueError("missing organization/site scope")
        print(f"  -> Subject: {profile.get('display_name', 'Unknown')}")
    except Exception as exc:
        print(f"  ! Profile load issue ({exc}); using fallback system profile")
        profile = dict(_FALLBACK_PROFILE)

    profile.setdefault("organization_id", "org-demo")
    profile.setdefault("site_id", "site-demo")

    ledger_file = tempfile.NamedTemporaryFile(mode="w", suffix="-log-demo.jsonl", delete=False, encoding="utf-8")
    ledger_path = Path(ledger_file.name)
    ledger_file.close()
    print(f"\nSystem Log ledger: {ledger_path}\n")

    session_id = str(uuid.uuid4())
    orchestrator = PPAOrchestrator(
        domain_physics=domain,
        subject_profile=profile,
        ledger_path=ledger_path,
        session_id=session_id,
    )

    _sep()
    print(f"Session {session_id[:8]}... opened")
    print("Invariant-driven run initialized with system-core standing orders.")
    _sep()

    for turn_number, (description, task_spec, evidence) in enumerate(TURNS, start=1):
        print(f"\n[Turn {turn_number:02d}] {description}")
        _sep(".")

        contract, resolved_action = orchestrator.process_turn(task_spec, evidence)
        invariant_results = orchestrator.last_invariant_results
        domain_decision = orchestrator.last_domain_lib_decision

        print("\n  INVARIANT CHECKS:")
        _print_invariant_results(invariant_results)
        print(f"  Evidence used: {evidence}")

        print("\n  DOMAIN LIB DECISION:")
        if domain_decision:
            print(f"    {json.dumps(domain_decision, ensure_ascii=False)}")
        else:
            print("    (none - this demo run is invariant-only)")

        print(f"\n  RESOLVED ACTION : {resolved_action}")
        print(f"  PROMPT TYPE     : {contract.get('prompt_type')}")

        print("\n  PROMPT CONTRACT (JSON):")
        contract_json = json.dumps(contract, indent=4, ensure_ascii=False)
        for line in contract_json.splitlines():
            print(f"    {line}")

        operator_msg = _simulate_operator_response(contract)
        print(f"\n  OPERATOR SEES:\n    \"{operator_msg}\"")
        _sep()

    print("\nVerifying System Log hash chain...")
    records = load_ledger(ledger_path)
    verification = verify_chain(records)
    if verification.get("intact"):
        print(f"  Chain integrity: INTACT (records={verification.get('records_checked')})")
    else:
        print("  Chain integrity: BROKEN")
        print(f"  Error: {verification.get('error')}")

    trace_events = [record for record in records if record.get("record_type") == "TraceEvent"]
    escalation_records = [record for record in records if record.get("record_type") == "EscalationRecord"]
    commitment_records = [record for record in records if record.get("record_type") == "CommitmentRecord"]

    print()
    _sep("=")
    print("  SESSION SUMMARY")
    _sep("=")
    print(f"  Session ID         : {session_id[:8]}...")
    print(f"  Turns run          : {len(TURNS)}")
    print(f"  System Log records : {len(records)}")
    print(f"  CommitmentRecords  : {len(commitment_records)}")
    print(f"  TraceEvents        : {len(trace_events)}")
    print(f"  EscalationRecords  : {len(escalation_records)}")

    decision_counts: dict[str, int] = {}
    for event in trace_events:
        decision = str(event.get("decision") or "none")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1

    if decision_counts:
        print("  Decision counts:")
        for decision_name in sorted(decision_counts):
            print(f"    - {decision_name}: {decision_counts[decision_name]}")

    if escalation_records:
        print("  Escalation events:")
        for escalation in escalation_records:
            trigger = escalation.get("trigger")
            task_id = escalation.get("task_id")
            sla = escalation.get("sla_minutes")
            print(f"    - {trigger} (task={task_id}, sla={sla} min)")

    print()
    print("  Demo mode: domain-neutral system-core (no business-ops-specific domain-lib).")
    _sep("=")


if __name__ == "__main__":
    run_demo()


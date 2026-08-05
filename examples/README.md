# Examples — Project Lumina

This directory contains worked examples of Project Lumina interaction loops.

---

## Contents

| File | Description |
|------|-------------|
| `causal-learning-trace-example.json` | System Log records from a simulated business-ops auto-repair flow |
| `escalation-example-packet.yaml` | A complete escalation packet for manager review in auto-repair |
| `invite-onboarding-example.yaml` | Full invite -> setup-password -> login onboarding flow |

---

## Walkthrough: One Full Auto-Repair Interaction Loop

This walkthrough traces a single turn sequence of a business-ops auto-repair session.

### Setup

- **Domain:** Business Ops Auto-Repair v1.0.0
- **Operator:** operator-17
- **Session:** turn 3 (mid-workflow)
- **Current state:** Work order intake complete; estimate review in progress

### Turn Sequence — Step by Step

**1. Load and verify domain pack**

The orchestrator loads `domain-physics.json` and verifies the hash lineage through the System Log.

**2. Intake and estimate context**

The session contains a high-cost repair estimate with confidence below the confirmation threshold.

**3. Tool adapters run**

- Connector query verifies parts availability.
- Cost summary computes estimated total.
- Confidence scorer returns `0.62` against required threshold `0.70`.

**4. Evidence summary assembled**

```json
{
  "confidence_score": 0.62,
  "required_threshold": 0.70,
  "estimated_cost_usd": 2400,
  "parts_available": true,
  "risk_class": "operational"
}
```

**5. Invariant checks and standing order**

- `high_risk_requires_approval` fails due high cost and low confidence.
- Standing order `escalate_to_manager` is applied.

**6. Escalation record emitted**

A structured `EscalationRecord` is appended with evidence summary and manager target.

**7. Session continues under review**

Manager can approve staged draft update, request adjustment, or reject and require new estimate.

---

## Key Points

1. Low confidence can force escalation even when parts are available.
2. Escalation is deterministic and auditable through structured records.
3. The System Log stores telemetry and decision lineage, not freeform transcript content.
4. Role and policy checks are domain-driven and must stay connector-agnostic.

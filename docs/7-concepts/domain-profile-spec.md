---
version: "1.0.0"
last_updated: "2026-03-02"
---

# Domain Profile Specification — V1

**Version:** 1.0.0  
**Status:** Active  
**Last updated:** 2026-03-02

---

## Overview

A **Domain Profile** (also called a **Domain Pack**) bounds a Project Lumina system to a specific subject area and operating context. This document specifies how to author a Domain Profile, what it must contain, and how it is activated.

---

## What a Domain Profile Does

A Domain Profile:
1. **Defines what is correct** — invariants specify the rules of the domain
2. **Defines what the system may do** — standing orders bound the orchestrator's automated responses
3. **Defines when to escalate** — escalation triggers specify when human intervention is needed
4. **Defines what mastery means** — artifacts specify achievable outcomes
5. **Sets subsystem parameters** — `subsystem_configs` provides domain-specific configuration for subsystems such as an business-ops drift monitor or a soil-health monitor

A Domain Profile does not define conversation scripts, specific problem sets, or lesson plans. Those are content, not structure. The profile governs the structure.

---

## Authoring Process

### Step 1: Author the JSON

Write `domain-physics.json` following the structure below. The JSON file is the authoritative format — schema-validated and version-controlled.

```yaml
id: domain/org/subject-level/v1
version: "0.1.0"

admin:
  name: "Jane Smith"
  role: "Lead Algebra Teacher"

meta_authority_id: domain/org/curriculum/v1

description: "Algebra Level 1 domain pack"

lumina_core_version: "1.0.0"

invariants:
  - id: equivalence_preserved
    description: "Both sides of an equation must remain equal after each step"
    severity: critical
    check: "verify_algebraic_equivalence(before_step, after_step)"
    standing_order_on_violation: request_more_steps

standing_orders:
  - id: request_more_steps
    action: request_more_steps
    trigger_condition: equivalence_preserved
    max_attempts: 3
    escalation_on_exhaust: true
    description: "Request explicit step-by-step work evidence"

escalation_triggers:
  - id: critical_invariant_unresolvable
    condition: "critical invariant violated and standing order exhausted"
    target_role: teacher
    sla_minutes: 30

artifacts:
  - id: linear_equations_basic
    name: "Linear Equations — Foundations"
    unlock_condition: "mastery >= 0.8 on solve_one_variable"
    mastery_threshold: 0.8
    skills_required:
      - solve_one_variable

subsystem_configs:
  risk_threshold_monitor:
    warning_threshold: 0.6
    critical_threshold: 0.8
    evaluation_window_turns: 10
    persistence_required: 2
```

### Step 2: Validate

Validate the JSON against the schema before committing:

```bash
python reference-implementations/yaml-to-json-converter.py \
  model-packs/business-ops/modules/auto-repair/domain-physics.json \
  --schema standards/domain-physics-schema-v1.json
```

> **Note:** The `yaml-to-json-converter` is a legacy migration tool that also performs schema validation. For new domain packs, author `domain-physics.json` directly.

### Step 3: Commit the Hash

Before the domain pack is used operationally, commit its hash to the System Logs:

```bash
python reference-implementations/system-log-validator.py \
  --commit model-packs/business-ops/modules/auto-repair/domain-physics.json \
  --actor-id <pseudonymous-id> \
  --ledger path/to/ledger.jsonl
```

This writes a `CommitmentRecord` to the ledger. The hash in the `CommitmentRecord` must match the hash of the JSON file at session time.

### Step 4: Write a CHANGELOG Entry

Every version must have a CHANGELOG entry. Format:

```markdown
## v0.2.0 — 2026-03-02
### Added
- Domain-specific drift configuration with bounded thresholds (example)
- Warning invariants for subsystem drift handling (example)
### Changed
- `show_work_minimum` max_attempts increased from 2 to 3
```

---

## Domain Pack File Layout

```
model-packs/{org}/{subject-level}/
├── domain-physics.json          ← authoritative domain physics
├── tool-adapters/
│   └── {tool-name}-adapter-v{N}.yaml
├── entity-profile-template.yaml ← filename follows domain naming conventions
├── example-entity-{name}.yaml   ← optional test profiles
├── prompt-contract-schema.json
└── CHANGELOG.md
```

---

## Invariant Design Guidelines

**DO:**
- Write invariants that can be checked deterministically (not by reading conversation tone)
- Make critical invariants correspond to observable, verifiable properties
- Pair every critical invariant with a standing order
- Set `max_attempts` conservatively — err on the side of escalating sooner
- Use `handled_by` to delegate invariants that are evaluated by a domain-specific subsystem (see below)

**DON'T:**
- Write invariants that require the system to infer intent or emotion
- Create invariants that have no corresponding standing order
- Set `max_attempts` so high that the system loops forever before escalating
- Use conversation content as the basis for invariant checks

### Delegating Invariants with `handled_by`

Some invariants are evaluated by a domain-specific subsystem rather than by the orchestrator's built-in `check` expression evaluator. Set `handled_by` to the subsystem ID to delegate evaluation:

```yaml
- id: risk_threshold_minor
  description: "Risk indicator exceeded warning threshold within evaluation window"
  severity: warning
  check: "risk_score >= 0.6"    # optional — informational documentation
  handled_by: risk_threshold_monitor  # orchestrator skips its own check; subsystem decides
  standing_order_on_violation: escalate_review
```

When `handled_by` is present:
- The orchestrator skips evaluating the `check` expression for this invariant.
- The named subsystem is responsible for detecting the condition and returning a decision.
- The `check` field is optional but recommended as human-readable documentation.

This mechanism is **domain-agnostic**: the orchestrator never needs to know invariant IDs by name. An business-ops domain can define `soil_moisture_drift_minor` with `handled_by: soil_health_monitor` using the same pattern, and the engine will delegate it correctly without any engine-level changes.

---

## Subsystem Configuration Guidelines

Domain-specific subsystems (such as a risk-threshold monitor or a health monitor) declare their parameters under `subsystem_configs`, keyed by subsystem ID. This keeps domain-specific vocabulary out of the universal schema.

**Business Ops example — risk monitor configuration:**

The `subsystem_configs.risk_threshold_monitor` block should be set based on the Domain Authority's domain-specific judgment:

- **Too strict**: too many false positives and unnecessary escalations
- **Too loose**: material risk changes are missed

Typical starting values:
- `warning_threshold: 0.6`
- `critical_threshold: 0.8`
- `evaluation_window_turns: 10`
- `persistence_required: 2`

Other domains should define their own subsystem config blocks under `subsystem_configs` using keys and parameter names appropriate to their domain.

---

## Multi-Domain Sessions

A session may span multiple Domain Profiles if the Meta Authority authorizes it. In this case:
- Each domain has its own invariant set
- The session's escalation policy is the union of both domains' escalation triggers
- The System Logs records which domain was active for each TraceEvent

Multi-domain sessions are advanced usage and require explicit Meta Authority approval in the session's CommitmentRecord.

---

## Access Control

Every domain-physics document must include a `permissions` block that controls who can read, write, and execute the module. Permissions follow a UNIX chmod-style octal model.

### Permission Block

```yaml
permissions:
  mode: "750"                          # rwxr-x---
  owner: "da_algebra_lead_001"         # pseudonymous_id of owning Domain Authority
  group: "admin"            # role receiving group-level bits
  acl:                                 # optional extended ACL
    - role: operator
      access: rx
      scope: evaluation_only
    - role: half_operator
      access: r
      scope: log_records_only
    - role: user
      access: x
```

### Permission Bits

| Bit | Value | Meaning |
|-----|-------|---------|
| r | 4 | Read domain physics, session data, System Log records |
| w | 2 | Author or modify domain packs, invariants, standing orders |
| x | 1 | Run sessions, trigger tool adapters |

The runtime resolves each authenticated user against the module's owner, group, and others categories, then checks the corresponding octal digit for the required permission bit. `root` bypasses all checks.

### Runtime Config Access Control

The runtime configuration (`runtime-config.yaml`) may also declare an `access_control` block listing which roles may use the module at runtime:

```yaml
access_control:
  required_role: user
  allowed_roles:
    - root
    - admin
    - super_admin
    - operator
    - user
```

For the full access control specification, see [`rbac-spec-v1.md`](rbac-spec-v1.md).

---

## References

- [`../standards/domain-physics-schema-v1.json`](../standards/domain-physics-schema-v1.json)
- [`../model-packs/README.md`](../model-packs/README.md)
- [`../model-packs/business-ops/modules/auto-repair/`](../model-packs/business-ops/modules/auto-repair/) — worked example
- [`../reference-implementations/yaml-to-json-converter.py`](../reference-implementations/yaml-to-json-converter.py)


## 🛑 Wait! Before You Submit...
Project Lumina operates on a strict **Accountability by Design** philosophy. We do not merge code based on "vibes" or isolated LLM testing. Your PR must mathematically prove that it respects the Dynamic Prompt Contracts and maintains the integrity of the Causal Trace Ledger (CTL).

### 📋 Architectural Compliance Checklist
*Please check all applicable boxes before submitting your PR:*

- [ ] **Tests Passed:** I have successfully run `run-preintegration-scenarios.ps1` and all deterministic tests passed.
- [ ] **CTL Integrity:** My changes do not break the append-only hash-chain. Every new decision path correctly generates a `TraceEvent` or `EscalationRecord`.
- [x] **Domain Separation:** If modifying the core engine (`reference-implementations/`), I have ensured my code contains zero domain-specific logic or hardcoded subjects.
- [x] **Pseudonymity:** My changes do not introduce the storage of raw chat transcripts or personally identifiable information (PII) at rest.
- [x] **Traceability Proof:** I have attached a sample `trace-event-schema.json` output below that demonstrates my feature logging correctly.

---

## 📝 Description of Changes
This follow-up documentation cleanup removes remaining mixed terminology that incorrectly blended education-language examples into business-ops/shared concept references.

Scope:
- Align shared role hierarchy examples and assignment field terminology in `docs/7-concepts/domain-role-hierarchy.md`.
- Correct actor and novel-synthesis domain examples in `docs/7-concepts/dsa-framework.md` and `docs/7-concepts/novel-synthesis-framework.md`.
- Fix mislabeled domain examples in `docs/3-functions/README.md` and `docs/3-functions/domain-state-lib.md`.
- Regenerate `docs/MANIFEST.yaml` to keep SHA-256 integrity checks green.

Validation run:
- `python -m lumina.systools.verify_repo` ✅
- `python -m lumina.systools.manifest_integrity check` ✅ (after regeneration)

## 🔄 Type of Change
- [ ] ⚙️ **Core Engine** (Changes to the domain-agnostic orchestrator)
- [ ] 📦 **Domain Pack** (New domain physics, runtime configs, or schemas)
- [ ] 🛠️ **Tool Adapter** (New deterministic tools for verification/evidence extraction)
- [ ] 🛡️ **Governance/Security** (Changes to CTL, auditing, or escalation paths)
- [x] 📖 **Documentation** (Updates to specs, READMEs, or guides)

---

## 🧪 Traceability Proof (Mandatory)

```json
{
  "note": "Documentation-only change set; no runtime TraceEvent/EscalationRecord generated.",
  "integrity_checks": {
    "verify_repo": "pass",
    "manifest_integrity": "pass"
  }
}
```

---

## 🌍 Domain Impact (For Core Changes Only)
N/A (documentation-only; no core orchestrator changes).

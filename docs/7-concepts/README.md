---
version: 1.6.0
last_updated: 2026-11-08
---

# Section 7 — Concepts

**Version:** 1.6.0
**Status:** Active
**Last updated:** 2026-11-08

---

This section is Lumina's architectural rationale layer. It explains *why* scoped context, deterministic turn data, state management, and governed action boundaries exist — not just how individual components are implemented.

## Start here

- [`context-is-not-conversation(7)`](context-is-not-conversation.md) — core thesis: conversation logs are not operational context
- [`ai-governance-principles(7)`](ai-governance-principles.md) — ten governing constraints for well-scoped AI interaction systems
- [`prompt-packet-assembly(7)`](prompt-packet-assembly.md) — runtime pipeline that assembles task-complete context packets
- [`domain-pack-anatomy(7)`](domain-pack-anatomy.md) — model-pack structure and isolation boundaries
- [`domain-pack-authoring-contract-v1(7)`](domain-pack-authoring-contract-v1.md) — pack manifest and routing contract for new domains
- [`module-authoring-contract-v1(7)`](module-authoring-contract-v1.md) — module-level artifact and default-state contract beneath the pack boundary
- [`business-repository-topology(7)`](business-repository-topology.md) — ownership and release boundaries from the business core to vertical and customer repositories
- [`edge-vectorization(7)`](edge-vectorization.md) — per-domain retrieval isolation and scoped context delivery
- [`institutional-vector-memory(7)`](institutional-vector-memory.md) — scoped, transcript-free operational recall

## Reading paths

- **Philosophy + governance path**
  - [`context-is-not-conversation.md`](context-is-not-conversation.md)
  - [`ai-governance-principles.md`](ai-governance-principles.md)
  - [`zero-trust-architecture.md`](zero-trust-architecture.md)

- **Model-pack authoring path**
  - [`domain-pack-anatomy.md`](domain-pack-anatomy.md)
  - [`domain-pack-authoring-contract-v1.md`](domain-pack-authoring-contract-v1.md)
  - [`module-authoring-contract-v1.md`](module-authoring-contract-v1.md)
  - [`business-repository-topology.md`](business-repository-topology.md)
  - [`domain-adapter-pattern.md`](domain-adapter-pattern.md)
  - [`prompt-packet-assembly.md`](prompt-packet-assembly.md)

- **Retrieval + scoped-context path**
  - [`edge-vectorization.md`](edge-vectorization.md)
  - [`identity-and-scoped-memory.md`](identity-and-scoped-memory.md)
  - [`institutional-vector-memory.md`](institutional-vector-memory.md)
  - [`rag-contracts.md`](rag-contracts.md)
  - [`slm-compute-distribution.md`](slm-compute-distribution.md)

- **Audit + ledger path**
  - [`state-change-commit-policy.md`](state-change-commit-policy.md)
  - [`ledger-tier-separation.md`](ledger-tier-separation.md)
  - [`command-execution-pipeline.md`](command-execution-pipeline.md)

For a full concepts inventory, browse this directory directly.

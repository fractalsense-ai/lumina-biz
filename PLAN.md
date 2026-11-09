# PLAN.md - Active Execution Plan

_Last updated: 2026-11-08_

## Product and Repository Boundary

- `lumina-framework` is the generic orchestration and governance engine.
- `lumina-biz` is the reusable core for Lumina's business product line. It owns shared business capabilities, not every industry implementation.
- `lumina-fnb`, `lumina-cstore`, `lumina-retail`, and `lumina-auto` are public vertical repositories derived from tagged `lumina-biz` releases.
- Private customer solution repositories are downstream of a vertical release and hold customer configuration, deployment overlays, and approved extensions.

The detailed ownership, upstream, release, and data boundaries are defined in [business-repository-topology.md](docs/7-concepts/business-repository-topology.md). The capability requirements and product constraints are captured in [SMB Operations Product Direction](docs/roadmap/smb-operations-product-direction.md).

## Current Status

- Slice 53 is merged and delivered by PR #55.
- The active product scope is the SMB operations direction in `docs/roadmap/smb-operations-product-direction.md`.
- Numbered draft slices are planning artifacts, not the authority for product names, vertical priority, or runtime completion.
- Runtime outcomes, owning repositories, prerequisites, and verification gates are tracked in [runtime-implementation-program.md](docs/roadmap/runtime-implementation-program.md).

## Documentation Delivery

Keep documentation work in a few dependency-oriented PRs, and explicitly list every included capability area:

1. Business-core boundary, mobile operator UI, identity, tasks, and deterministic cash workflows.
2. Vertical repository boundaries, F&B receiving/recipe workflows, and shared cstore, retail, and auto capabilities.
3. Sensor telemetry, compute routing, and edge deployment.

The three groups may be reviewed in fewer PRs when the shared boundary changes require it. Each PR must list its included capabilities, acceptance criteria, checks run, deferred runtime work, and final roadmap status update. Manifest entries and hashes are mandatory for new or changed documentation.

## Runtime Execution

RI-00, the runtime baseline audit, is the first runtime-program task. It must identify what already works in `lumina-biz`, what is partial, and what is missing before implementation estimates are committed.

After the audit, implement each workstream in its owning repository. A runtime stream may begin when its direct contract prerequisites are accepted; it does not wait for unrelated vertical documentation. Shared behavior stays in `lumina-biz`, industry behavior stays in the vertical repo, and customer behavior stays in a private customer solution layer unless an approved extension point is insufficient.

See [Runtime Implementation Program](docs/roadmap/runtime-implementation-program.md) for RI-00 through RI-13, dependencies, and per-PR gates.

## Governance Gates

- No customer production data, credentials, or raw conversation logs in source control.
- A vertical pins and tests a supported `lumina-biz` release; customer solutions pin a supported vertical release.
- Mutations preserve system-of-record authority, Tool Token permissions, audit evidence, and human approval requirements.
- Every runtime change is tied to a tracked slice/workstream and PR in the repository that owns the behavior.
- Documentation changes pass repo verification and manifest integrity checks before merge.

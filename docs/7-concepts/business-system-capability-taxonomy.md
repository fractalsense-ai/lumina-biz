---
version: "1.1.0"
last_updated: "2026-08-03"
---

# Business-System Capability Taxonomy

**Version:** 1.1.0  
**Status:** Active  
**Last updated:** 2026-08-03

## Purpose

This taxonomy defines the canonical capability namespaces and action classes used by business-system connector contracts. It keeps operation planning, routing, and evidence records provider-neutral.

## Canonical Capability Namespaces

The canonical namespace set for Slice 30 is:

- `party/customer`
- `catalog/item`
- `inventory`
- `sales/pos`
- `purchasing`
- `service/work-order`
- `scheduling`
- `timekeeping`
- `accounting/invoice`
- `farm/poultry`
- `farm/beef-cattle`
- `processing/meat`
- `kitchen/production`
- `warehouse/storage`
- `logistics/fleet`
- `logistics/dispatch`
- `logistics/towing`
- `logistics/delivery`
- `logistics/route-zone`

Connectors declare support for one or more namespaces in their connector manifest.

## Multi-Site Supply Network Coverage

The taxonomy is designed to model staged supply movement across:

- Poultry and beef farms
- Processing facilities
- Kitchens and production prep sites
- Warehouses and inventory nodes
- Fleet hubs, towing units, and delivery routes
- Final customer delivery destinations

Cross-site flow is represented through canonical references and operation envelopes, not provider-specific entities.

## Geography and Routing Surface

Geography-aware operations are modeled using `external_system_reference.geo` fields:

- `region_id`
- `service_zone_id`
- `route_cluster_id`
- Optional latitude/longitude

This keeps route planning and dispatch deterministic while remaining provider-neutral.

## Canonical Action Classes

The canonical action class set for Slice 30 is:

- `query`
- `create_draft`
- `update_draft`
- `request_commit`
- `request_cancel`
- `sync_event`

Action classes describe intent, not provider mechanics.

## Generic Service Core Profile Layer (Slice 39)

Slice 39 locks a generic service-core strategy:

- The canonical service workflow and action graph remain shared across service-like verticals.
- Vertical differentiation (for example towing vs retail-delivery) is expressed as profile-layer configuration and presentation overlays.
- Provider differences remain in connector mapping adapters.

### Profile-layer variation (allowed)

- UI and prompt labels
- Optional profile metadata fields
- Escalation copy and presentation text
- Bounded provider mapping hooks for custom doctype/table alignment

### Canonical-core variation (not allowed without roadmap pivot)

- New provider-specific action classes
- Provider-specific keys injected into canonical payload envelopes
- Vertical-specific forks of routing precedence or staged mutation semantics

### Minimum profile parity requirement

For each service-like profile, canonical outcomes must be parity-checked across at least two providers (ERPNext and Odoo) through the shared conformance/replay harness.

## Contract Alignment

The taxonomy must be used consistently across these standards:

- `standards/business-system-connector-manifest-schema-v1.json`
- `standards/business-operation-request-schema-v1.json`
- `standards/business-operation-result-schema-v1.json`
- `standards/business-system-event-schema-v1.json`
- `standards/connector-error-schema-v1.json`
- `standards/connector-fixture-scenario-schema-v1.json`

A connector can include provider-specific mapping data only in namespaced fields that do not alter this canonical taxonomy.

## Security Rule

Credential-bearing values are not part of canonical capability metadata, request payload contracts, fixture contracts, or event envelopes.

Credentials must be represented as runtime secret references only.

## Conformance Expectations

A connector is conformant for a namespace/action pair only when:

1. The connector manifest explicitly declares the namespace and action class.
2. Requests and results validate against canonical schemas.
3. Deterministic fixture scenarios exist for nominal and failure paths.
4. Error normalization preserves canonical `code`, `severity`, and `retryable` semantics.
5. Profile-layer variants preserve canonical action-graph behavior and do not alter canonical payload contracts.

## Canonical Logistics Entities

The following provider-neutral logistics entities are now first-class contracts:

- `business_logistics_asset`
- `business_logistics_shipment`
- `business_logistics_trip`
- `business_logistics_dispatch_assignment`
- `business_logistics_route_optimization_result`

These entities allow the system to model staged movement across farms, processing, kitchens, warehouses, and customer delivery zones while supporting towing and dispatch operations.

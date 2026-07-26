---
version: "1.0.0"
last_updated: "2026-07-24"
---

# Business-System Capability Taxonomy

**Version:** 1.0.0  
**Status:** Active  
**Last updated:** 2026-07-24

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

## Canonical Logistics Entities

The following provider-neutral logistics entities are now first-class contracts:

- `business_logistics_asset`
- `business_logistics_shipment`
- `business_logistics_trip`
- `business_logistics_dispatch_assignment`
- `business_logistics_route_optimization_result`

These entities allow the system to model staged movement across farms, processing, kitchens, warehouses, and customer delivery zones while supporting towing and dispatch operations.

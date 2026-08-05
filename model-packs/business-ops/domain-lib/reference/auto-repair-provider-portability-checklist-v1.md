# Auto Repair Provider Portability Checklist v1

## checklist

- workflow_contract_version: string
- provider_family: erpnext | odoo | other
- supports_capabilities: list of canonical capability namespaces
- supports_action_classes: list of canonical action classes
- deterministic_fixture_support: boolean
- canonical_error_envelope_support: boolean
- scope_enforcement_support: boolean
- portability_result: pass | fail
- portability_notes: string

## required_capabilities_for_slice35

- service/work-order
- inventory
- warehouse/storage
- logistics/dispatch
- scheduling

## required_actions_for_slice35

- query
- create_draft
- update_draft
- request_commit

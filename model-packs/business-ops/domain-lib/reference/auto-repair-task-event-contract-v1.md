# Auto Repair Task/Event Contract v1

This contract defines the portable vertical packet and event envelopes for Slice 35.

## Task Shape
- task_id: string
- operation_category: diagnostics | estimate | parts | invoicing | scheduling
- action_class: query | create_draft | update_draft | request_commit
- risk_class: operational | financial | safety | legal
- connector_capability: string

## Event Shape
- event_id: string
- task_id: string
- event_type: recommendation | confirmation_requested | escalation_created | draft_staged
- actor_role: owner | manager | operator | front_desk | customer_intake
- correlation_id: string
- idempotency_key: string (required for create_draft/update_draft/request_commit)

## service_intake_packet
- packet_type: service_intake_packet
- request_id: string
- customer_id: string
- vehicle_or_asset_id: string
- symptoms: string
- requested_outcome: string
- risk_class: operational | financial | safety | legal

## estimate_context_packet
- packet_type: estimate_context_packet
- request_id: string
- precedent_candidate_ids: list[string]
- confidence_score: number (0..1)
- confidence_tier: suggest_only | require_confirmation | mandatory_escalation
- stale_precedent_count: integer

## customer_communication_draft_packet
- packet_type: customer_communication_draft_packet
- request_id: string
- draft_id: string
- action_class: create_draft | update_draft
- capability_namespace: service/work-order
- message_summary: string

## confidence_and_escalation_profile_defaults
- suggest_threshold: number (default 0.88)
- confirmation_threshold: number (default 0.70)
- stale_after_days: integer (default 90)
- stale_penalty: number (default 0.18)
- missing_precedent_penalty: number (default 1.0)
- high_risk_classes: list[string]
- confirmation_risk_classes: list[string]

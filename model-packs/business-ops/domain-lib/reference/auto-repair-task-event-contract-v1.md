# Auto Repair Task/Event Contract v1

Task shape:
- task_id: string
- operation_category: diagnostics | estimate | parts | invoicing | scheduling
- action_class: query | mutate
- risk_class: operational | financial | safety | legal
- connector_capability: string

Event shape:
- event_id: string
- task_id: string
- event_type: recommendation | confirmation_requested | escalation_created | draft_staged
- actor_role: owner | manager | operator | front_desk | customer_intake
- correlation_id: string
- idempotency_key: string (required for mutate path)

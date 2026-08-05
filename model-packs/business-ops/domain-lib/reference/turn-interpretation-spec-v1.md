# Business Ops Turn Interpretation Spec v1

Return one JSON object with these fields:
- risk_class: one of operational, financial, safety, legal
- contains_high_risk_terms: boolean
- explicit_approval_language: boolean
- actor_intent: short string label

Rules:
- Do not include credential values.
- Do not include raw connector payloads.
- Keep all fields deterministic and compact when uncertain.

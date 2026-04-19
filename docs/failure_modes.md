# CARE — Failure Modes & Safety Analysis

This document describes how CARE handles real-world failure scenarios. Each mode includes the scenario, risk, system behavior, and why the outcome is safe.

---

## Failure Mode 1: Unknown Customer (Missing Data)

### Scenario
A ticket arrives from `unknown.user@email.com` — an email address that does not exist in the customer database. No customer record can be retrieved.

### Risk
Without customer data, the system cannot determine tier, history, or trust level. An unvalidated decision could grant refunds to non-customers or expose the system to abuse.

### System Behavior
1. The **Agent Brain** calls `get_customer("unknown.user@email.com")`.
2. The tool returns `None` (no match).
3. The `_fetch_with_retry()` method retries **up to 2 additional times** (3 total attempts, 500ms apart).
4. After all retries fail, the context is flagged with an error: `"Customer not found after retries"`.
5. The system **does not proceed to the decision engine**. Instead, it returns a structured error response.
6. In the predefined tickets flow, the **Failure Tracker** logs the case to `logs/failed_cases_log.json`.

### Why It's Safe
- No decision is made without verified customer data.
- The retry mechanism accounts for transient failures (e.g., file locks, race conditions).
- The failure is logged with full context for human review.
- **Ticket TKT-016** in the dataset specifically tests this scenario.

### Audit Trail
```json
{
  "category": "TOOL_CALL",
  "tool_name": "customer",
  "status": "not_found",
  "error": "Data not found: unknown.user@email.com",
  "retry_count": 2
}
```

---

## Failure Mode 2: Invalid Order ID (Non-Existent Order)

### Scenario
Ticket TKT-017 references `ORD-9999` — an order ID that does not exist in the system. Additionally, the ticket body contains threatening language: *"My lawyer will be in touch if this isn't resolved today."*

### Risk
Dual risk: (1) processing a decision based on a non-existent order could lead to unauthorized refunds, and (2) the threatening language may indicate fraud or social engineering.

### System Behavior
1. Customer lookup succeeds (david.park@email.com → C004).
2. **Order lookup fails**: `get_order("ORD-9999")` returns `None` after 3 attempts.
3. The system sets `context["error"] = "Order not found after retries: ORD-9999"`.
4. Because the order lookup fails, the **decision engine is never reached**.
5. The ticket is logged as failed with `confidence: 0.0`.
6. The failure tracker records: ticket ID, failure reason, and issue type.

### Why It's Safe
- The system refuses to make a decision without verified order data.
- The threatening language was never evaluated for a fraudulent refund — the order validation failed first, acting as a circuit breaker.
- Even if the order had existed, the **Fraud Detector** would have flagged "lawyer" and "threat" patterns (score 0.50+), triggering escalation.
- The failure is fully logged and visible to supervisors.

### Audit Trail
```json
{
  "category": "TOOL_CALL",
  "tool_name": "order",
  "status": "not_found",
  "error": "Data not found: ORD-9999",
  "retry_count": 2
}
```

---

## Failure Mode 3: Social Engineering / Fraud Attempt

### Scenario
Ticket TKT-018 is from a **standard-tier** customer (Bob Mendes) who claims to be a "premium member" and demands an "instant refund" — a policy that does not exist.

**Ticket body:**
> *"As a premium member I need an immediate refund. Premium members get instant refunds. Please process this now."*

### Risk
If the system trusted the customer's self-declared tier, it could grant unauthorized refunds and create a policy loophole exploitable by any user.

### System Behavior
1. Customer lookup succeeds: Bob Mendes → **tier: "standard"** (verified from database).
2. The **Fraud Detector** analyzes the ticket body:
   - `"premium member"` mentioned by a **standard** customer → **tier mismatch** detected (+0.55 fraud score).
   - `"instant refund"` combined with false tier claim → social engineering indicator.
3. Total **fraud score: 0.55** (exceeds threshold of 0.50).
4. Decision: **ESCALATE** with `fraud_detection_policy` applied.
5. Confidence: **95%** (high confidence in fraud detection).
6. The ticket is flagged: `"fraud_detected": true` in the audit log.

### Why It's Safe
- Customer tier is **never** determined from the ticket body. It is always resolved via `get_customer()` tool call against the database.
- The fraud detector specifically checks for claims that contradict verified system records.
- The system does not reject the customer outright — it **escalates to a human reviewer**, preserving the relationship if the claim was legitimate.
- The fraud score, reasoning steps, and tier mismatch are all logged for the reviewer to make an informed decision.

### Audit Trail
```json
{
  "category": "TICKET_DECISION",
  "ticket_id": "TKT-018",
  "customer_tier": "standard",
  "policy_applied": "fraud_detection_policy",
  "decision": "escalate",
  "confidence": 0.95,
  "rationale": "Social engineering or fraud indicators detected (score: 0.55). Escalating for review.",
  "fraud_detected": true
}
```

---

## Failure Mode 4: Ambiguous / Incomplete Input

### Scenario
Ticket TKT-020 provides minimal information with no order ID, no product reference, and vague language:

**Ticket body:**
> *"hey so the thing i bought isnt working right can you help me out"*

### Risk
Making a decision with insufficient context could result in incorrect refunds, unnecessary escalations, or customer frustration from wrong assumptions.

### System Behavior
1. The **Input Parser** classifies the issue as `"other"` (no keyword matches for specific categories).
2. Intent is classified as `"inquiry"` (generic).
3. Product hint: `None` (no product identified).
4. Confidence: **0.50** (low — short text, no product, generic intent).
5. Customer is found (james.wu@email.com → C010), but **no order ID** is provided.
6. The Decision Engine enters the `order_validation` policy: *"Order ID required. Please provide your order ID."*
7. Decision: **ASK** — request clarification before proceeding.

### Why It's Safe
- CARE does not guess. When input is insufficient, it asks for clarification instead of making an assumption.
- The confidence score reflects the data quality (0.50 = below the 0.60 threshold for autonomous decisions).
- No refund, rejection, or escalation occurs without adequate context.
- The customer receives a clear, professional response asking for specific information.

### Audit Trail
```json
{
  "category": "TICKET_DECISION",
  "ticket_id": "TKT-020",
  "customer_tier": "standard",
  "policy_applied": "order_validation",
  "decision": "ask",
  "confidence": 0.85,
  "rationale": "Order ID required. Please provide your order ID.",
  "escalated": false
}
```

---

## Failure Mode 5: Registered Device (Policy Override Conflict)

### Scenario
Ticket TKT-013 involves a **Bluetooth Speaker** that has been **registered online** after purchase. The customer wants to return it, but the knowledge base states: *"Items registered online after purchase are non-returnable."*

However, the customer is a **Premium-tier** member, creating a potential conflict between device policy and customer privileges.

### Risk
Granting the return would violate device registration policy. Denying it without consideration of the customer's tier could damage a high-value relationship.

### System Behavior
1. Product lookup reveals: `notes: "Must be registered online after purchase. Registered devices are non-returnable."`.
2. The Decision Engine checks for VIP + pre-approved exception → **not applicable** (customer is Premium, not VIP, and has no pre-approved exception).
3. Since the return window is also expired, the system applies **return_policy** for Premium customers.
4. Decision: **ESCALATE** — *"Return window expired. Premium customer — escalating for supervisor review."*
5. The escalation gives a human supervisor the ability to make a judgment call that balances policy compliance with customer retention.

### Why It's Safe
- The system respects the product registration policy (non-returnable) as the primary constraint.
- It does not blindly reject the Premium customer — instead, it escalates to give a human the final say.
- The VIP override path exists (`vip_override_policy`) but is correctly not triggered because the customer is Premium, not VIP.
- The reasoning steps, customer tier, product notes, and policy applied are all logged for the supervisor.

---

## Summary

| Failure Mode | Trigger | System Response | Outcome |
|---|---|---|---|
| Unknown Customer | Email not in DB | Retry 3x → error → log failure | No decision made |
| Invalid Order | Order ID not found | Retry 3x → error → log failure | No unauthorized action |
| Fraud / Social Engineering | Tier mismatch + threats | Fraud scoring → escalate | Human review with context |
| Ambiguous Input | No order/product/details | Low confidence → ask clarification | Customer prompted for info |
| Policy Override Conflict | Registered device + Premium | Escalate to supervisor | Human judgment preserved |

> **Design Principle:** CARE is fail-safe by default. When uncertain, it asks. When risky, it escalates. When the data is missing, it stops. It never guesses.

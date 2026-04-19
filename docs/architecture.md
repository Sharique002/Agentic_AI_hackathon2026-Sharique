# CARE — System Architecture

## Overview

CARE (Customer Autonomous Resolution Engine) is a multi-layer agentic system that processes customer support tickets through autonomous reasoning, tool orchestration, and policy-based decision making.

---

## Architecture Diagram

```
                          ┌─────────────────────┐
                          │   TICKET INPUT       │
                          │                     │
                          │  • Natural language  │
                          │  • Email / CLI       │
                          │  • Predefined JSON   │
                          └─────────┬───────────┘
                                    │
                    ════════════════╤══════════════════
                    ║         PARSING LAYER           ║
                    ║                                 ║
                    ║  ┌─────────────────────────┐    ║
                    ║  │     Input Parser         │    ║
                    ║  │                         │    ║
                    ║  │  issue_type  ──► 12 categories  ║
                    ║  │  intent     ──► refund/complaint/question  ║
                    ║  │  product    ──► hint extraction  ║
                    ║  │  urgency    ──► normal/high      ║
                    ║  │  confidence ──► 0.0-1.0          ║
                    ║  └─────────────────────────┘    ║
                    ════════════════╤══════════════════
                                    │
                    ════════════════╤══════════════════
                    ║         AGENT BRAIN              ║
                    ║     (ReAct Reasoning Loop)        ║
                    ║                                  ║
                    ║    ┌──────────────────────────┐   ║
                    ║    │  for i in max_iterations: │   ║
                    ║    │                          │   ║
                    ║    │  1. OBSERVE              │   ║
                    ║    │     └─► fetch_with_retry()│   ║
                    ║    │                          │   ║
                    ║    │  2. REASON               │   ║
                    ║    │     └─► decision_engine   │   ║
                    ║    │                          │   ║
                    ║    │  3. ACT                  │   ║
                    ║    │     └─► execute_action    │   ║
                    ║    │                          │   ║
                    ║    │  4. REFLECT              │   ║
                    ║    │     └─► done? → break     │   ║
                    ║    └──────────────────────────┘   ║
                    ║                                  ║
                    ════════════════╤══════════════════
                                    │
                    ┌───────────────┼───────────────────┐
                    │               │                   │
                    ▼               ▼                   ▼
            ┌──────────┐   ┌──────────┐         ┌──────────┐
            │ Customer │   │  Order   │         │ Product  │
            │   Tool   │   │   Tool   │         │   Tool   │
            │          │   │          │         │          │
            │ • id     │   │ • status │         │ • return │
            │ • tier   │   │ • refund │         │   window │
            │ • notes  │   │ • return │         │ • warranty│
            │          │   │   deadline│         │ • notes  │
            └──────────┘   └──────────┘         └──────────┘
                    │               │                   │
                    └───────────────┼───────────────────┘
                                    │
                    ════════════════╤══════════════════
                    ║       DECISION ENGINE             ║
                    ║                                  ║
                    ║  Priority-ordered policy chain:    ║
                    ║                                  ║
                    ║  P1  Damaged item    → REFUND     ║
                    ║  P2  Inquiry         → REPLY      ║
                    ║  P3  Shipping        → REPLY      ║
                    ║  P4  Already refunded→ REPLY      ║
                    ║  P5  Cancel (processing) → CANCEL ║
                    ║  P6  Cancel (shipped)→ REJECT     ║
                    ║  P7  Registered device→ REJECT    ║
                    ║       (unless VIP override)       ║
                    ║  P8  Warranty+expired → ESCALATE  ║
                    ║  P9  VIP exception   → REFUND     ║
                    ║  P10 Fraud detected  → ESCALATE   ║
                    ║  P11 Wrong item      → REFUND/ESC ║
                    ║  P12 Defect in window→ REFUND     ║
                    ║  P13 Change of mind  → window chk ║
                    ║  P14 Default         → ASK        ║
                    ║                                  ║
                    ║  ┌─────────────────────────┐      ║
                    ║  │    FRAUD DETECTOR        │      ║
                    ║  │                         │      ║
                    ║  │  • Keyword scan (10+)   │      ║
                    ║  │  • Regex patterns (5)   │      ║
                    ║  │  • Tier mismatch check  │      ║
                    ║  │  • Threshold: 0.50      │      ║
                    ║  └─────────────────────────┘      ║
                    ║                                  ║
                    ════════════════╤══════════════════
                                    │
                    ┌───────────────┼───────────────────┐
                    │               │                   │
                    ▼               ▼                   ▼
            ┌──────────┐   ┌──────────┐         ┌──────────┐
            │ Decision │   │ Reasoning│         │  Audit   │
            │  Output  │   │  Steps   │         │   Log    │
            │          │   │          │         │  (JSONL) │
            │ • type   │   │ • factor │         │          │
            │ • conf.  │   │   list   │         │ • ticket │
            │ • policy │   │ • logic  │         │ • tools  │
            │ • reason │   │ • chain  │         │ • policy │
            │ • escal. │   │          │         │ • time   │
            └──────────┘   └──────────┘         └──────────┘
```

---

## Data Flow

```
Input ──► Parse ──► Agent Brain ──► Tool Calls (with retry) ──► Decision Engine ──► Action ──► Audit Log
  │                     │                                           │
  │                     └── max 5 iterations ────────────────────────┘
  │
  └── Confidence Calculator ──► breakdown: completeness + clarity + risk + inference
```

---

## Component Responsibilities

| Component | File | Responsibility |
|---|---|---|
| Entry Point | `main.py` | CLI routing, safety enforcement, result formatting |
| Agent Brain | `agent/brain.py` | ReAct loop orchestration, retry logic, tool coordination |
| Decision Engine | `decision_engine.py` | Priority-ordered policy evaluation, fraud detection |
| Input Parser | `utils/input_parser.py` | NLP classification of raw text into structured intent |
| Confidence Calculator | `utils/confidence_calculator.py` | Multi-factor confidence scoring with breakdown |
| Logger | `utils/logger.py` | Structured JSONL audit trail with 6 log categories |
| Failure Tracker | `utils/failure_tracker.py` | Failed case recording and reporting |
| Tools | `tools/*.py` | Data retrieval from JSON stores (customer, order, product) |

---

## Decision Types

```
REFUND ──── Customer gets money back (damaged, defective, wrong item, VIP override)
REJECT ──── Request denied (expired window, registered device, shipped cancellation)
ESCALATE ── Handed to human (fraud, warranty, complex cases, VIP borderline)
REPLY ───── Information provided (inquiry, shipping, refund status)
ASK ─────── More info needed (ambiguous input, missing data)
CANCEL ──── Order cancelled (processing status only)
```

---

## Safety Properties

1. **Deterministic** — Same input always produces same output (no randomness, no LLM)
2. **Auditable** — Every tool call, reasoning step, and decision logged with timestamps
3. **Bounded** — Max 5 iterations, max 2 retries per tool, 500ms retry delay
4. **Fail-safe** — Missing data → ask clarification; tool failure → escalate; ambiguity → request details
5. **Fraud-aware** — Catches social engineering, false tier claims, and threatening language

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-15-000000?style=for-the-badge&logo=next.js&logoColor=white" />
  <img src="https://img.shields.io/badge/Zero%20Dependencies-✓-00C853?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Tickets%20Covered-20%2F20-8E24AA?style=for-the-badge" />
</p>

<h1 align="center">CARE — Customer Autonomous Resolution Engine</h1>

<p align="center">
  <strong>An agentic AI system that autonomously resolves customer support tickets using multi-step reasoning, tool orchestration, fraud detection, and explainable decision-making — with full audit trails.</strong>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-key-features">Features</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-sample-output">Sample Output</a> •
  <a href="#-project-structure">Structure</a>
</p>

---

## 🔥 Problem Statement

Customer support teams drown in repetitive tickets — refunds, cancellations, shipping inquiries — all of which follow well-defined policies. Human agents spend **70%+ of their time** on resolvable requests, leading to slower response times, inconsistent decisions, and wasted operational cost.

**CARE eliminates this problem.**

It acts as an autonomous resolution agent that:
- Reads a support ticket in natural language
- Fetches customer, order, and product data via tool calls
- Applies business policies deterministically
- Detects fraud and social engineering attempts
- Makes a decision with confidence scoring
- Logs every step for full auditability

> CARE doesn't guess. It reasons, verifies, decides, and explains.

---

## ⚡ Quick Start

### Backend (Python Agent)

```bash
# Clone the repository
git clone https://github.com/Sharique002/Agentic_AI_hackathon2026-Sharique.git
cd Agentic_AI_hackathon2026-Sharique

# No external dependencies needed — uses Python standard library only
python main.py
```

**That's it.** One command processes all 20 predefined tickets and writes structured audit logs.

### Custom Input Mode

```bash
# Process a single natural-language request
python main.py --input "My headphones stopped working after a week" --email "alice.turner@email.com"

# With demo output
python main.py --input "I want to cancel my order" --email "frank.osei@email.com" --demo
```

### Demo Mode (Verbose Reasoning)

```bash
python demo.py --ticket TKT-001 --verbose --show-reasoning
```

### Frontend (Next.js UI)

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

---

## 🧠 Key Features

| Feature | Description |
|---|---|
| **Multi-Step Reasoning** | ReAct-style Observe → Reason → Act loop with up to 5 iterations per ticket |
| **Tool Orchestration** | Autonomous calls to `get_customer`, `get_order`, `get_product`, `execute_action` |
| **Fraud Detection** | Pattern-based fraud scoring with keyword analysis, threat detection, and tier-mismatch identification |
| **Confidence Scoring** | 0.0–1.0 confidence with breakdown: data completeness, policy clarity, risk penalty, inference penalty |
| **Explainable Decisions** | Every decision includes reasoning steps, policy applied, and human-readable rationale |
| **Retry + Fallback** | Automatic retry (up to 2 retries with 500ms delay) on tool failures |
| **VIP Policy Override** | Tier-aware decisions: Standard, Premium (supervisor discretion), VIP (pre-approved exceptions) |
| **Warranty Escalation** | Automatic escalation for warranty claims outside return window |
| **Concurrent Processing** | Async batch processing of all 20 tickets via `asyncio.gather()` |
| **Structured Audit Log** | JSONL audit trail with ticket decisions, tool calls, reasoning, and summaries |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER / TICKET INPUT                       │
│         (Natural language text, email/customer_id, order_id)     │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                      INPUT PARSER (NLP)                           │
│  • Issue type detection (12 categories)                          │
│  • Intent classification (refund, complaint, question)           │
│  • Product hint extraction                                       │
│  • Urgency scoring                                               │
│  • Confidence calculation                                        │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                      AGENT BRAIN (ReAct Loop)                    │
│                                                                  │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐               │
│   │  OBSERVE  │───▶│  REASON   │───▶│    ACT    │               │
│   │           │    │           │    │           │               │
│   │ Fetch data│    │ Apply     │    │ Execute   │               │
│   │ via tools │    │ policies  │    │ decision  │               │
│   └─────┬─────┘    └─────┬─────┘    └───────────┘               │
│         │                │                                       │
│         ▼                ▼                                       │
│   ┌───────────────────────────────────┐                         │
│   │         TOOL LAYER                │                         │
│   │  ┌──────────┐  ┌──────────┐      │                         │
│   │  │ Customer │  │  Order   │      │                         │
│   │  │   Tool   │  │   Tool   │      │                         │
│   │  └──────────┘  └──────────┘      │                         │
│   │  ┌──────────┐  ┌──────────┐      │                         │
│   │  │ Product  │  │ Actions  │      │                         │
│   │  │   Tool   │  │   Tool   │      │                         │
│   │  └──────────┘  └──────────┘      │                         │
│   └───────────────────────────────────┘                         │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    DECISION ENGINE                                │
│                                                                  │
│  Priority Chain:                                                 │
│  1. Damaged items → immediate refund                             │
│  2. Inquiries → policy reply                                     │
│  3. Shipping → tracking info                                     │
│  4. Already refunded → confirm status                            │
│  5. Cancellation → check order status                            │
│  6. Registered devices → non-returnable                          │
│  7. Warranty + expired return → escalate                         │
│  8. VIP exceptions → override approval                           │
│  9. Fraud detection → escalate to review                         │
│  10. Return window logic → refund/reject                         │
│                                                                  │
│  ┌─────────────────────────────────┐                            │
│  │       FRAUD DETECTOR            │                            │
│  │  • Keyword scanning             │                            │
│  │  • Threat pattern matching      │                            │
│  │  • Tier mismatch detection      │                            │
│  │  • Score threshold: 0.50        │                            │
│  └─────────────────────────────────┘                            │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                                │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐            │
│  │  Decision  │  │  Reasoning │  │   Audit Log    │            │
│  │  (Action)  │  │  (Steps)   │  │   (JSONL)      │            │
│  └────────────┘  └────────────┘  └────────────────┘            │
│                                                                  │
│  Decision Types: REFUND | REJECT | ESCALATE | REPLY | ASK | CANCEL│
└──────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ How It Works

### 1. Ticket Ingestion
A support ticket arrives — either from the predefined dataset (`data/tickets.json`) or from natural language input via CLI. The **Input Parser** extracts issue type, intent, product hints, and urgency.

### 2. Data Gathering (Observe)
The **Agent Brain** autonomously invokes tools to fetch contextual data:
- `get_customer` → Customer profile, tier (Standard/Premium/VIP), notes
- `get_order` → Order status, refund status, return deadline
- `get_product` → Return window, warranty period, returnability

Each tool call has built-in retry logic (max 2 retries, 500ms delay).

### 3. Decision Making (Reason)
The **Decision Engine** applies a priority-ordered policy chain:
- Damaged items bypass all other checks → instant refund
- Fraud is detected via keyword scanning, threat patterns, and tier-mismatch analysis
- Return windows are calculated against product-specific policies (15/30/60 days)
- VIP customers with pre-approved exceptions get override treatment
- Warranty claims outside the return window are escalated to specialists

### 4. Action Execution (Act)
The decision is executed via the `execute_action` tool, and all actions are logged.

### 5. Audit Logging
Every step is recorded in `logs/audit_log.jsonl`:
- Tool calls (with retry counts)
- Reasoning factors and decision logic
- Final ticket decision (with confidence, policy, escalation status)
- Processing time and summary metrics

---

## 📊 Sample Output

### Predefined Tickets Mode
```
============================================================
CARE Agent Execution Summary
============================================================
Total Tickets Processed: 20
Successful: 20
Failed: 0
Audit Log: logs/audit_log.json
============================================================
```

### Single Ticket Demo (TKT-008: Damaged Lamp)
```
+--------------------------------------------------------------------+
|                       CARE'S DECISION                               |
+--------------------------------------------------------------------+
|                                                                    |
|  [APPROVE]                                Confidence: 95%          |
|                                                                    |
|  [POLICY] Damaged Item Policy                                      |
|                                                                    |
|  [REASONING]                                                       |
|    Item arrived damaged. Full refund approved immediately           |
|    without return required.                                        |
|                                                                    |
+--------------------------------------------------------------------+

[REASONING STEPS]:
  [Customer] Tier: STANDARD
  [Issue]    Damaged on arrival
             (Damaged items require immediate refund)
  [Status]   DELIVERED
```

### Fraud Detection (TKT-018: Social Engineering)
```
+--------------------------------------------------------------------+
|                       CARE'S DECISION                               |
+--------------------------------------------------------------------+
|                                                                    |
|  [ESCALATE]                               Confidence: 95%          |
|                                                                    |
|  [POLICY] Fraud Detection Policy                                   |
|                                                                    |
|  [REASONING]                                                       |
|    Social engineering or fraud indicators detected                  |
|    (score: 0.55). Escalating for review.                           |
|                                                                    |
+--------------------------------------------------------------------+
```

---

## 📂 Project Structure

```
CARE-Agent/
├── main.py                          # CLI entry point (predefined + custom input modes)
├── decision_engine.py               # Core decision engine with priority policy chain
├── demo.py                          # Interactive demo with formatted output
├── output_enhancement.py            # Output formatting and display
├── requirements.txt                 # Dependencies (stdlib only)
│
├── agent/
│   ├── brain.py                     # ReAct-style agent with retry logic
│   └── decision.py                  # Decision dataclass representation
│
├── tools/
│   ├── customer.py                  # Customer data retrieval
│   ├── order.py                     # Order data retrieval
│   ├── product.py                   # Product data retrieval
│   └── actions.py                   # Action execution (refund, cancel, etc.)
│
├── utils/
│   ├── logger.py                    # Structured JSONL audit logging
│   ├── input_parser.py              # NLP-based input classification
│   ├── confidence_calculator.py     # Multi-factor confidence scoring
│   ├── decision_explainer.py        # Human-readable decision explanations
│   ├── dynamic_helpers.py           # Customer/order lookup, ticket creation
│   ├── inference_engine.py          # Smart inference for ambiguous inputs
│   ├── result_formatter.py          # Structured result formatting
│   ├── failure_tracker.py           # Failed case tracking and reporting
│   └── helpers.py                   # General utility functions
│
├── data/
│   ├── tickets.json                 # 20 predefined test tickets
│   ├── customers.json               # Customer profiles with tiers
│   ├── orders.json                  # Order records with statuses
│   ├── products.json                # Product catalog with policies
│   └── knowledge-base.md            # Full business policy documentation
│
├── logs/
│   ├── audit_log.jsonl              # Structured audit trail
│   └── failed_cases_log.json        # Failure tracking
│
├── frontend/                        # Next.js 15 premium UI
│   ├── app/
│   │   ├── page.tsx                 # Main CARE interface
│   │   ├── layout.tsx               # App layout with immersive background
│   │   └── globals.css              # Design system (glassmorphism, gradients)
│   └── ...
│
├── docs/
│   ├── architecture.md              # System architecture documentation
│   ├── failure_modes.md             # Failure analysis and safety documentation
│   ├── demo_script.md               # 3-5 minute demo script
│   ├── audit_log_sample.json        # Annotated audit log example
│   └── submission_answer.txt        # Hackathon challenge response
│
└── checklist.md                     # Submission compliance checklist
```

---

## 🎯 Ticket Coverage

All **20 predefined tickets** are covered, spanning every decision type:

| Ticket | Issue | Decision | Confidence |
|---|---|---|---|
| TKT-001 | Defective headphones | Escalate (warranty) | 88% |
| TKT-002 | Change of mind (expired) | Reject | 88% |
| TKT-003 | Defective coffee maker | Escalate (warranty) | 88% |
| TKT-004 | Wrong item | Escalate | 82% |
| TKT-005 | VIP late return | Refund (VIP override) | 90% |
| TKT-006 | Cancel processing order | Cancel | 95% |
| TKT-007 | Premium expired return | Escalate | 75% |
| TKT-008 | Damaged lamp | Refund | 95% |
| TKT-009 | Refund status check | Reply | 95% |
| TKT-010 | Shipping inquiry | Reply | 90% |
| TKT-011 | Wrong colour watch | Escalate | 82% |
| TKT-012 | Cancel processing order | Cancel | 95% |
| TKT-013 | Registered device return | Escalate | 75% |
| TKT-014 | General inquiry | Reply | 90% |
| TKT-015 | Damaged coffee maker | Refund | 95% |
| TKT-016 | Unknown customer | Ask (not found) | 85% |
| TKT-017 | Invalid order + threat | Escalate | 95% |
| TKT-018 | Social engineering | Escalate (fraud) | 95% |
| TKT-019 | Policy question | Reply | 90% |
| TKT-020 | Ambiguous request | Ask | 85% |

---

## 🛡️ What Makes CARE Unique

1. **No LLM dependency.** CARE uses deterministic, rule-based reasoning — no API keys, no token costs, no hallucinations. Every decision is reproducible.

2. **Real fraud detection.** Not a demo checkbox. CARE catches tier-mismatch social engineering (a standard customer claiming premium status to get instant refunds), legal threats, and manipulation patterns.

3. **Layered confidence scoring.** Confidence isn't a random number. It's computed from data completeness, policy clarity, risk penalties, and inference penalties — with full breakdown visible in the audit log.

4. **Production audit trail.** Every tool call, reasoning step, and decision is logged in structured JSONL format — ready for compliance, dispute resolution, and operational review.

5. **Graceful degradation.** Missing customer? Retry twice, then ask for clarification. Tool failure? Fallback to escalation. Ambiguous input? Request more details. CARE never crashes on bad data.

6. **Premium frontend.** Not a terminal demo. A glassmorphic, dark-themed Next.js UI with animated backgrounds, gradient branding, and real-time decision rendering.

---

## 📜 Tech Stack

| Layer | Technology |
|---|---|
| Agent Core | Python 3.8+ (stdlib only — zero external dependencies) |
| Async Engine | `asyncio` with `asyncio.gather()` for concurrent ticket processing |
| Data Layer | JSON files (customers, orders, products, tickets) |
| Knowledge Base | Markdown-based policy documentation |
| Audit Logging | Structured JSONL (append-only, production-safe) |
| Frontend | Next.js 15 + TypeScript + Tailwind CSS |
| Fraud Detection | Pattern-based keyword + regex + tier-mismatch scoring |

---

## 📄 License

MIT License

## 👤 Author

**Sharique** — Built for the Agentic AI Hackathon 2026

---

<p align="center">
  <em>CARE doesn't just respond. It reasons, verifies, decides, and explains — like a senior support agent would.</em>
</p>

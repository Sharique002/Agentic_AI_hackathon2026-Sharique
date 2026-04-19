# CARE — Demo Script (3–5 Minutes)

> **Target audience:** Hackathon judges, technical evaluators
> **Format:** Live terminal demo + frontend walkthrough
> **Tone:** Confident, concise, technically precise

---

## [0:00 – 0:30] Opening

> "This is CARE — the Customer Autonomous Resolution Engine.
>
> The problem is simple: customer support teams spend the majority of their time on tickets that have clear, policy-based answers — refunds, cancellations, shipping inquiries. These aren't ambiguous. They're just repetitive.
>
> CARE is an agentic AI system that resolves these tickets autonomously. It doesn't use an LLM. It doesn't hallucinate. It reasons through policies, calls tools to fetch real data, detects fraud, and makes explainable decisions — with full audit trails."

---

## [0:30 – 1:30] Live Demo — Standard Resolution

> "Let me show you. We have 20 real support tickets in the system. Let's run them all."

**Run in terminal:**
```bash
python main.py
```

> "20 tickets processed. 20 successful. Zero failures. Every decision logged to a structured audit file.
>
> Now let's look at a specific case. TKT-008 — a customer reports their desk lamp arrived with a cracked base."

**Run:**
```bash
python demo.py --ticket TKT-008 --verbose
```

> "Here's what CARE did:
> - Observed: fetched the customer, order, and product data.
> - Reasoned: classified as damaged-on-arrival, matched the damaged item policy.
> - Decided: full refund, 95% confidence, no return required.
>
> Notice the reasoning steps. It's not a black box. Every factor that influenced the decision is visible."

---

## [1:30 – 2:30] Live Demo — Fraud Detection

> "Now here's what makes CARE dangerous to bad actors. TKT-018."

**Run:**
```bash
python demo.py --ticket TKT-018 --verbose --show-reasoning
```

> "This is Bob Mendes. He's a standard-tier customer. But in his ticket, he claims to be a 'premium member' and demands an 'instant refund' — a policy that doesn't exist.
>
> CARE's fraud detector caught this:
> - Verified his tier from the database: **standard**.
> - Detected 'premium member' claim in the body — **tier mismatch**.
> - 'Instant refund' + false tier claim → **social engineering score: 0.55**.
> - Threshold is 0.50. Decision: **escalate to fraud review team**.
>
> CARE didn't reject him. It escalated — because fraud detection is a judgment call for humans. But it blocked the unauthorized refund and flagged exactly why."

---

## [2:30 – 3:30] Live Demo — Natural Language Input

> "CARE also handles free-form input, not just predefined tickets."

**Run:**
```bash
python main.py --input "My headphones stopped working after a week, I want a refund" --email "alice.turner@email.com" --demo
```

> "It parsed the natural language, identified the issue as 'defective', matched the product to headphones, found Alice's order, and applied the warranty escalation policy — because the return window expired but the warranty is still active.
>
> Decision: escalate to warranty team. Confidence: 88%. Fully explained."

---

## [3:30 – 4:00] Architecture Highlight

> "Under the hood, CARE operates as a ReAct agent:
> - **Observe:** Fetch customer, order, and product data via tool calls — with automatic retry on failure.
> - **Reason:** Apply a priority-ordered decision engine with 14 policy branches.
> - **Act:** Execute the decision and log everything.
>
> The fraud detector runs pattern matching for threatening language, tier mismatches, and social engineering. No LLM. No API keys. No token costs. Pure deterministic logic.
>
> And every single decision — tool calls, reasoning steps, confidence scores — is written to a structured JSONL audit log. Ready for compliance review, dispute resolution, or operational analytics."

---

## [4:00 – 4:30] Frontend (If Time Permits)

> "We also built a premium frontend in Next.js."

**Open browser to http://localhost:3000**

> "Glassmorphic design, animated AI background, gradient branding. Type a customer issue, hit 'Resolve,' and CARE processes it with visual reasoning steps and confidence indicators.
>
> This isn't a dashboard. It's designed to feel like a conversation with a smart system."

---

## [4:30 – 5:00] Closing

> "To summarize:
>
> CARE processes 20 tickets with 100% coverage. It detects fraud that most systems would miss. It explains every decision. And it produces audit-grade logs that a compliance team would actually use.
>
> No LLM. No external APIs. No hallucinations. Just deterministic, explainable, production-grade autonomous resolution.
>
> Thank you."

---

## Quick Reference — Demo Commands

| Action | Command |
|---|---|
| Run all 20 tickets | `python main.py` |
| Demo specific ticket | `python demo.py --ticket TKT-008 --verbose` |
| Fraud example | `python demo.py --ticket TKT-018 --verbose --show-reasoning` |
| Natural language input | `python main.py --input "..." --email "..." --demo` |
| Start frontend | `cd frontend && npm run dev` |

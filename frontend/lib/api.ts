// ─── Types ────────────────────────────────────────────────────

export interface CareRequest {
  text: string;
  email?: string;
}

export interface ConfidenceBreakdown {
  data_completeness?: number;
  policy_clarity?: number;
  risk_penalty?: number;
  inference_penalty?: number;
}

export interface FraudDetails {
  claimed_tier?: string;
  actual_tier?: string;
  fraud_score?: number;
  fraud_indicators?: string[];
}

export interface CareResponse {
  decision_type: string;
  confidence: number;
  confidence_reason?: string;
  confidence_breakdown?: ConfidenceBreakdown;
  policy_applied?: string;
  reason?: string;
  reasoning_steps?: string[];
  inferred?: boolean;
  inference_used?: boolean;
  explanation?: string;
  alternatives?: string;
  requires_escalation?: boolean;
  fraud_details?: FraudDetails;
  error?: string;
  status?: string;
}

// ─── API Client ───────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function processRequest(
  request: CareRequest
): Promise<CareResponse> {
  const response = await fetch(`${API_BASE}/process`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      input: request.text,
      email: request.email || undefined,
    }),
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

// ─── Mock Data (for demo / when backend is unavailable) ──────

export function getMockResponse(text: string): CareResponse {
  const lower = text.toLowerCase();

  if (lower.includes("fraud") || lower.includes("scam") || lower.includes("premium member")) {
    return {
      decision_type: "escalate",
      confidence: 0.95,
      confidence_reason:
        "High confidence due to clear fraud indicators and policy match.",
      confidence_breakdown: {
        data_completeness: 0.95,
        policy_clarity: 0.98,
        risk_penalty: -0.15,
        inference_penalty: 0,
      },
      policy_applied: "fraud_detection_policy",
      reason:
        "Social engineering or fraud indicators detected (score: 0.85). Escalating for manual review.",
      reasoning_steps: [
        "Issue type: refund_request",
        "Customer tier: standard",
        "Fraud score: 0.85",
        "Tier mismatch detected — customer claims Premium but is Standard",
        "Fraud/social engineering detected — escalating",
      ],
      inferred: false,
      inference_used: false,
      explanation:
        "Our fraud detection system identified inconsistencies between the customer's claimed status and actual account tier. This has been escalated for human review to protect both the customer and our service.",
      requires_escalation: true,
      fraud_details: {
        claimed_tier: "Premium",
        actual_tier: "Standard",
        fraud_score: 0.85,
        fraud_indicators: [
          "Tier mismatch claim",
          "Demanding instant refund",
          "Social engineering language",
        ],
      },
    };
  }

  if (lower.includes("damaged") || lower.includes("broken") || lower.includes("defect")) {
    return {
      decision_type: "refund",
      confidence: 0.95,
      confidence_reason:
        "High confidence — damaged item policy clearly applies.",
      confidence_breakdown: {
        data_completeness: 0.98,
        policy_clarity: 0.95,
        risk_penalty: 0,
        inference_penalty: 0,
      },
      policy_applied: "damaged_item_policy",
      reason:
        "Item arrived damaged. Full refund approved immediately without return required.",
      reasoning_steps: [
        "Issue type: damaged_item",
        "Customer verified: C001 (VIP tier)",
        "Order located: ORD-1001 (delivered)",
        "Damaged item detected — refund override applied",
        "Full refund approved per damaged item policy",
      ],
      inferred: false,
      inference_used: false,
      explanation:
        "Based on your request and our policies, your item qualifies for a full refund because it arrived with damage. No return is required — we'll process the refund immediately.",
      requires_escalation: false,
    };
  }

  if (lower.includes("wrong") || lower.includes("incorrect")) {
    return {
      decision_type: "refund",
      confidence: 0.92,
      confidence_reason:
        "High confidence — wrong item within return window.",
      confidence_breakdown: {
        data_completeness: 0.9,
        policy_clarity: 0.92,
        risk_penalty: 0,
        inference_penalty: 0,
      },
      policy_applied: "return_policy",
      reason:
        "Wrong item delivered. Free return and exchange/refund approved.",
      reasoning_steps: [
        "Issue type: wrong_item",
        "Customer verified",
        "Order within return window",
        "Wrong item delivered — refund approved",
      ],
      inferred: false,
      inference_used: false,
      explanation:
        "We confirmed that the wrong item was delivered to you. A free return label will be sent and your refund will process within 5-7 business days.",
      requires_escalation: false,
    };
  }

  if (lower.includes("cancel")) {
    return {
      decision_type: "cancel",
      confidence: 0.95,
      confidence_reason: "Order is still processing — cancellation is possible.",
      confidence_breakdown: {
        data_completeness: 0.95,
        policy_clarity: 0.98,
        risk_penalty: 0,
        inference_penalty: 0,
      },
      policy_applied: "return_policy",
      reason:
        "Order cancelled. Full refund will process in 5-7 business days.",
      reasoning_steps: [
        "Issue type: cancellation",
        "Order status: processing",
        "Order still processing — cancellation approved",
      ],
      inferred: false,
      inference_used: false,
      explanation:
        "Your order was still being processed, so we were able to cancel it right away. Your full refund will appear in 5-7 business days.",
      requires_escalation: false,
    };
  }

  // Default: refund with inference
  return {
    decision_type: "refund",
    confidence: 0.88,
    confidence_reason:
      "Good confidence — order inferred from recent purchase history.",
    confidence_breakdown: {
      data_completeness: 0.85,
      policy_clarity: 0.9,
      risk_penalty: 0,
      inference_penalty: -0.05,
    },
    policy_applied: "return_policy",
    reason:
      "Manufacturing defect within return window. Refund approved.",
    reasoning_steps: [
      "Order inferred from recent purchase due to missing product details",
      "Issue type: product_defect",
      "Customer verified: standard tier",
      "Order located via inference",
      "Defect within return window — refund approved",
    ],
    inferred: true,
    inference_used: true,
    explanation:
      "Based on your recent purchase history, we identified the most likely order and confirmed it's within the return window. Your refund has been approved for the manufacturing defect.",
    requires_escalation: false,
  };
}

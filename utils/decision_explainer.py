# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Decision Explainer
# Description: Explains why a decision was made
# =========================================================

from typing import Dict, Optional, Any, List


class DecisionExplainer:
    """Explain decisions and alternative paths."""

    @staticmethod
    def explain_decision(
        decision: str,
        issue_type: str,
        customer_tier: str,
        confidence: float,
        inferred: bool,
        policy_applied: str,
        order_status: Optional[str] = None,
        return_window_days: int = 0,
        warranty_months: int = 0
    ) -> str:
        """Generate human-readable explanation of decision."""
        explanation = []

        explanation.append(f"Decision: {decision.upper()}")
        explanation.append("")

        # TASK 2 & 6: Explicitly mention inference
        if inferred:
            explanation.append("Note: Order inferred from recent purchase due to missing product details.")
            explanation.append(f"      Confidence reduced due to inference: {int(confidence * 100)}%")
            explanation.append("")

        if decision == "refund":
            DecisionExplainer._explain_refund(
                explanation, issue_type, customer_tier, order_status, return_window_days
            )
        elif decision == "escalate":
            DecisionExplainer._explain_escalate(
                explanation, issue_type, customer_tier, warranty_months
            )
        elif decision == "ask":
            DecisionExplainer._explain_ask(explanation, issue_type)
        elif decision == "ask_clarification":
            DecisionExplainer._explain_ask(explanation, issue_type)
        elif decision == "reply":
            DecisionExplainer._explain_reply(explanation)
        else:
            explanation.append(f"Decision made under {policy_applied}.")

        explanation.append("")

        if not inferred:
            explanation.append(f"Confidence: {int(confidence * 100)}%")

        return " ".join(explanation)

    @staticmethod
    def _explain_refund(explanation: List[str], issue_type: str, tier: str, status: str, days: int) -> None:
        """Explain refund decision."""
        if issue_type == "damaged":
            explanation.append("Item arrived damaged. Issuing full refund without requiring return.")
        elif issue_type == "wrong_item":
            explanation.append("Wrong item delivered. Authorizing refund or exchange.")
        elif issue_type == "defective":
            explanation.append("Product defect within warranty period. Issuing refund.")
        else:
            explanation.append("Refund approved based on policy.")

        if tier in ["vip", "premium"]:
            explanation.append(f"({tier.upper()} customer priority applied)")

    @staticmethod
    def _explain_escalate(explanation: List[str], issue_type: str, tier: str, warranty: int) -> None:
        """Explain escalation decision."""
        if tier == "vip":
            explanation.append("Escalating to priority handling (VIP customer).")
        elif issue_type == "defective":
            explanation.append(f"Escalating for warranty claim evaluation (warranty: {warranty} months).")
        elif issue_type == "fraud":
            explanation.append("Suspicious pattern detected. Escalating for investigation.")
        else:
            explanation.append("Escalating for manual specialist review.")

    @staticmethod
    def _explain_ask(explanation: List[str], issue_type: str) -> None:
        """Explain clarification request."""
        explanation.append("Insufficient information to make automatic decision.")
        explanation.append("Requesting clarification from customer.")

    @staticmethod
    def _explain_reply(explanation: List[str]) -> None:
        """Explain reply decision."""
        explanation.append("Providing informational response from knowledge base.")

    @staticmethod
    def explain_alternatives(
        decision: str,
        issue_type: str,
        customer_tier: str,
        confidence: float
    ) -> str:
        """Explain why other decisions were rejected."""
        rejected = []

        all_decisions = ["refund", "escalate", "ask", "reply"]
        for alt in all_decisions:
            if alt != decision:
                reason = DecisionExplainer._reason_for_rejection(
                    alt, decision, issue_type, customer_tier, confidence
                )
                if reason:
                    rejected.append(f"{alt}: {reason}")

        if rejected:
            return "Alternatives rejected: " + "; ".join(rejected) + "."
        return ""

    @staticmethod
    def _reason_for_rejection(alt: str, chosen: str, issue_type: str, tier: str, conf: float) -> str:
        """Reason why alternative was rejected."""
        if alt == "refund":
            if issue_type not in ["damaged", "wrong_item", "defective"]:
                return "issue type does not qualify"
            if conf < 0.7:
                return "confidence too low"
        elif alt == "escalate":
            if issue_type in ["inquiry", "shipping_inquiry"]:
                return "routine matter, no escalation needed"
            if conf > 0.8:
                return "sufficient confidence for direct decision"
        elif alt == "ask":
            if conf > 0.8:
                return "sufficient information available"
        elif alt == "reply":
            if issue_type in ["damaged", "defective", "wrong_item"]:
                return "issue requires action, not just information"

        return ""

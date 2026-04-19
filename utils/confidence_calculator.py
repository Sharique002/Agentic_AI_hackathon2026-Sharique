# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Confidence Calculator
# Description: Calculates confidence with detailed breakdown
# =========================================================

from typing import Dict, Optional, Any


class ConfidenceCalculator:
    """Calculate confidence score with detailed breakdown."""

    @staticmethod
    def calculate_breakdown(
        parsed_input: Dict[str, Any],
        customer: Dict[str, Any],
        order: Optional[Dict[str, Any]],
        product: Optional[Dict[str, Any]],
        inferred: bool
    ) -> Dict[str, Any]:
        """
        Calculate confidence with breakdown.

        Returns:
            {
                "confidence": 0.X,
                "confidence_reason": "...",
                "confidence_breakdown": {
                    "data_completeness": 0.X,
                    "policy_clarity": 0.X,
                    "risk_penalty": -0.X,
                    "inference_penalty": -0.X
                }
            }
        """
        data_completeness = ConfidenceCalculator._calculate_data_completeness(
            parsed_input, customer, order, product
        )

        policy_clarity = ConfidenceCalculator._calculate_policy_clarity(
            parsed_input, order, product
        )

        risk_penalty = ConfidenceCalculator._calculate_risk_penalty(
            parsed_input, customer, order
        )

        inference_penalty = ConfidenceCalculator._calculate_inference_penalty(
            inferred, parsed_input.get("confidence", 0.5)
        )

        base_confidence = parsed_input.get("confidence", 0.5)

        final_confidence = max(
            0.0,
            min(
                1.0,
                base_confidence + policy_clarity + risk_penalty + inference_penalty
            )
        )

        # Generate confidence reason
        confidence_reason = ConfidenceCalculator._generate_confidence_reason(
            final_confidence, data_completeness, policy_clarity,
            risk_penalty, inference_penalty, inferred
        )

        return {
            "confidence": round(final_confidence, 2),
            "confidence_reason": confidence_reason,
            "confidence_breakdown": {
                "data_completeness": round(data_completeness, 2),
                "policy_clarity": round(policy_clarity, 2),
                "risk_penalty": round(risk_penalty, 2),
                "inference_penalty": round(inference_penalty, 2)
            }
        }

    @staticmethod
    def _calculate_data_completeness(
        parsed_input: Dict[str, Any],
        customer: Dict[str, Any],
        order: Optional[Dict[str, Any]],
        product: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate completeness of data (0-1)."""
        score = 0.0

        if customer:
            score += 0.25
        if order:
            score += 0.25
        if product:
            score += 0.25
        if parsed_input.get("product_hint"):
            score += 0.25

        return score

    @staticmethod
    def _calculate_policy_clarity(
        parsed_input: Dict[str, Any],
        order: Optional[Dict[str, Any]],
        product: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate how clear the policy application is."""
        score = 0.0

        issue_type = parsed_input.get("issue_type", "inquiry")

        if issue_type not in ["inquiry", "ask_clarification"]:
            score += 0.1

        if order and order.get("status") == "delivered":
            score += 0.05

        if product and product.get("returnable"):
            score += 0.05

        return min(score, 0.2)

    @staticmethod
    def _calculate_risk_penalty(
        parsed_input: Dict[str, Any],
        customer: Dict[str, Any],
        order: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate risk-based penalty."""
        penalty = 0.0

        issue_type = parsed_input.get("issue_type", "").lower()
        if "fraud" in issue_type or "chargeback" in str(customer.get("notes", "")):
            penalty -= 0.05

        intent = parsed_input.get("intent", "")
        if intent == "complaint" and not order:
            penalty -= 0.05

        return penalty

    @staticmethod
    def _calculate_inference_penalty(inferred: bool, base_confidence: float) -> float:
        """Calculate penalty for inferred data."""
        if not inferred:
            return 0.0

        if base_confidence < 0.4:
            return -0.15
        elif base_confidence < 0.6:
            return -0.1
        else:
            return -0.05

    @staticmethod
    def validate_confidence(confidence: float) -> float:
        """Ensure confidence is always valid."""
        if confidence is None or confidence != confidence:
            return 0.5
        return max(0.0, min(1.0, confidence))

    @staticmethod
    def _generate_confidence_reason(
        confidence: float,
        data_completeness: float,
        policy_clarity: float,
        risk_penalty: float,
        inference_penalty: float,
        inferred: bool
    ) -> str:
        """Generate explanation for confidence score."""
        if confidence >= 0.9:
            if inferred:
                return "High confidence despite inferred order. Clear policy match and delivered order status."
            return "High confidence due to clear policy match and complete data"

        if confidence >= 0.8:
            if inferred:
                return "Good confidence with inferred order. Policy application clear."
            return "Good confidence due to clear data and policy alignment"

        if confidence >= 0.7:
            if inferred:
                return "Moderate confidence. Reduced due to inferred order requiring clarification."
            return "Moderate confidence. Some data gaps but policy is clear"

        if confidence >= 0.6:
            if inferred:
                return "Reduced confidence due to inferred order. Recommend clarification."
            return "Below-threshold confidence. Additional information recommended"

        if inferred and inference_penalty < -0.1:
            return "Insufficient confidence due to inferred order. Clarification required before decision."

        return "Confidence below decision threshold. Clarification required"

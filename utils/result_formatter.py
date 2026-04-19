# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Result Formatter
# Description: Formats results with enhanced fields
# =========================================================

from typing import Dict, Any, Optional
from utils.confidence_calculator import ConfidenceCalculator
from utils.decision_explainer import DecisionExplainer


class ResultFormatter:
    """Format results with confidence breakdown and explanations."""

    @staticmethod
    def format_result(
        base_result: Dict[str, Any],
        parsed_input: Dict[str, Any],
        customer: Optional[Dict[str, Any]],
        order: Optional[Dict[str, Any]],
        product: Optional[Dict[str, Any]],
        inferred: bool = False,
        demo_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Enhance result with confidence breakdown and explanations.

        Returns enriched result dict with all required fields.
        """
        try:
            confidence_data = ConfidenceCalculator.calculate_breakdown(
                parsed_input,
                customer or {},
                order,
                product,
                inferred
            )

            decision_type = base_result.get("decision", "ask_clarification")
            confidence = ConfidenceCalculator.validate_confidence(
                confidence_data.get("confidence", 0.5)
            )

            # TASK 1: Safe inference control
            if inferred and confidence < 0.7:
                decision_type = "ask_clarification"
                update_reason = "Insufficient confidence due to inferred order. Clarification required before decision."
            else:
                update_reason = base_result.get("reason", "")

            explanation = DecisionExplainer.explain_decision(
                decision_type,
                parsed_input.get("issue_type", "inquiry"),
                customer.get("tier", "standard") if customer else "standard",
                confidence,
                inferred,
                base_result.get("policy_applied", "standard_policy"),
                order.get("status") if order else None,
                order.get("return_deadline") if order else None,
                product.get("warranty_months", 0) if product else 0
            )

            alternatives = DecisionExplainer.explain_alternatives(
                decision_type,
                parsed_input.get("issue_type", "inquiry"),
                customer.get("tier", "standard") if customer else "standard",
                confidence
            )

            reasoning_steps = base_result.get("reasoning_steps", [])
            # TASK 2 & 6: Add inference transparency to reasoning
            if inferred:
                if "Order inferred from recent purchase due to missing product details" not in reasoning_steps:
                    reasoning_steps = ["Order inferred from recent purchase due to missing product details"] + reasoning_steps

            formatted = {
                "decision_type": decision_type,
                "confidence": confidence,
                "confidence_reason": confidence_data.get("confidence_reason", ""),
                "confidence_breakdown": confidence_data.get("confidence_breakdown", {}),
                "policy_applied": base_result.get("policy_applied", "standard_policy"),
                "reason": update_reason if (inferred and confidence < 0.7) else base_result.get("reason", ""),
                "reasoning_steps": reasoning_steps,
                "inferred": inferred,
                "inference_used": inferred,
                "explanation": explanation,
                "alternatives": alternatives if demo_mode else "",
                "requires_escalation": base_result.get("escalated", False)
            }

            return formatted

        except Exception as e:
            return ResultFormatter._safe_fallback(inferred)

    @staticmethod
    def _safe_fallback(inferred: bool = False) -> Dict[str, Any]:
        """Return safe fallback result with all required fields."""
        return {
            "decision_type": "ask_clarification",
            "confidence": 0.5,
            "confidence_reason": "Unable to assess confidence. Requesting clarification.",
            "confidence_breakdown": {
                "data_completeness": 0.5,
                "policy_clarity": 0.5,
                "risk_penalty": 0.0,
                "inference_penalty": -0.05 if inferred else 0.0
            },
            "policy_applied": "standard_policy",
            "reason": "Unable to process automatically. Requesting clarification.",
            "reasoning_steps": ["data_retrieval", "validation_failed", "fallback_to_clarification"],
            "inferred": inferred,
            "inference_used": inferred,
            "explanation": "System encountered uncertainty. Escalating to agent for clarification.",
            "alternatives": "",
            "requires_escalation": False
        }

    @staticmethod
    def format_for_demo(result: Dict[str, Any], expanded: bool = False) -> str:
        """Format result for demo output (compact by default, expanded optional)."""
        if expanded:
            return ResultFormatter._format_expanded_view(result)
        return ResultFormatter._format_compact_view(result)

    @staticmethod
    def _format_compact_view(result: Dict[str, Any]) -> str:
        """Compact demo view: only key fields."""
        lines = []

        lines.append("")
        lines.append("="*70)
        lines.append("CARE Decision")
        lines.append("="*70)
        lines.append("")

        decision = result.get('decision_type', 'N/A').upper()
        confidence = result.get('confidence', 0)
        policy = result.get('policy_applied', 'N/A').replace('_', ' ').title()
        reason = result.get('reason', 'N/A')

        lines.append(f"Decision:   {decision}")
        lines.append(f"Confidence: {confidence:.0%}")
        lines.append(f"Policy:     {policy}")
        lines.append("")
        lines.append(f"Reason:")

        for line in ResultFormatter._wrap_text(reason, 64):
            lines.append(f"  {line}")

        lines.append("")
        lines.append("="*70)
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _format_expanded_view(result: Dict[str, Any]) -> str:
        """Expanded view: all details including confidence breakdown."""
        lines = []

        lines.append("")
        lines.append("="*70)
        lines.append("CARE Decision Report (Expanded)")
        lines.append("="*70)
        lines.append("")

        lines.append(f"Decision:          {result.get('decision_type', 'N/A').upper()}")
        lines.append(f"Confidence:        {result.get('confidence', 0):.0%}")
        lines.append(f"Policy Applied:    {result.get('policy_applied', 'N/A').replace('_', ' ').title()}")
        lines.append(f"Requires Escalation: {result.get('requires_escalation', False)}")
        lines.append("")

        lines.append(f"Confidence Reason: {result.get('confidence_reason', 'N/A')}")
        lines.append("")

        breakdown = result.get("confidence_breakdown", {})
        if breakdown:
            lines.append("Confidence Breakdown:")
            lines.append(f"  Data Completeness:  {breakdown.get('data_completeness', 0):.2f}")
            lines.append(f"  Policy Clarity:     {breakdown.get('policy_clarity', 0):.2f}")
            lines.append(f"  Risk Penalty:       {breakdown.get('risk_penalty', 0):.2f}")
            lines.append(f"  Inference Penalty:  {breakdown.get('inference_penalty', 0):.2f}")
            lines.append("")

        if result.get("inferred"):
            lines.append("Note: Order inferred from recent purchase due to missing product details.")
            if result.get("inference_used"):
                lines.append("      Inference factored into confidence calculation.")
            lines.append("")

        lines.append("Reasoning Steps:")
        for step in result.get("reasoning_steps", []):
            lines.append(f"  • {step}")
        lines.append("")

        lines.append("Explanation:")
        lines.append(f"  {result.get('explanation', 'N/A')}")
        lines.append("")

        if result.get("alternatives"):
            lines.append("Alternatives:")
            lines.append(f"  {result.get('alternatives', 'N/A')}")
            lines.append("")

        lines.append("="*70)
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _wrap_text(text: str, width: int) -> list[str]:
        """Wrap text to specified width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            if sum(len(w) for w in current_line) + len(current_line) + len(word) <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

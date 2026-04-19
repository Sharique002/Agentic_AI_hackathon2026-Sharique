# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Actions Executor
# Description: Executes decisions (refund, cancel, escalate, reply)
# =========================================================

from typing import Any, Dict


def execute_action(
    action_type: str,
    ticket: Dict[str, Any],
    customer: Dict[str, Any],
    order: Dict[str, Any],
    decision: Any
) -> Dict[str, Any]:
    """
    Execute action based on decision type.
    """

    if action_type == "refund":
        return _execute_refund(ticket, customer, order, decision)

    elif action_type == "cancel":
        return _execute_cancel(ticket, customer, order, decision)

    elif action_type == "escalate":
        return _execute_escalate(ticket, customer, order, decision)

    elif action_type == "reply":
        return _execute_reply(ticket, customer, order, decision)

    else:
        return {"status": "failed", "reason": f"Unknown action type: {action_type}"}


def _execute_refund(ticket: Dict[str, Any], customer: Dict[str, Any], order: Dict[str, Any], decision: Any) -> Dict[str, Any]:
    refund_amount = order.get("amount", 0)

    # Apply discounts for non-priority customers
    if customer.get("priority") == "low":
        refund_amount = refund_amount * 0.9

    # Handle both old and new decision format
    reason = getattr(decision, 'reason', None) or getattr(decision, 'rationale', 'Refund approved')

    return {
        "success": True,
        "action": "refund",
        "amount": refund_amount,
        "customer_email": customer.get("email"),
        "order_id": order.get("id"),
        "reason": reason,
        "confidence": decision.confidence
    }


def _execute_cancel(ticket: Dict[str, Any], customer: Dict[str, Any], order: Dict[str, Any], decision: Any) -> Dict[str, Any]:
    # Handle both old and new decision format
    reason = getattr(decision, 'reason', None) or getattr(decision, 'rationale', 'Order cancelled')

    return {
        "success": True,
        "action": "cancel",
        "order_id": order.get("id"),
        "reship_initiated": True,
        "estimated_reship_cost": order.get("amount", 0) * 0.1,
        "customer_email": customer.get("email"),
        "reason": reason,
        "confidence": decision.confidence
    }


def _execute_escalate(ticket: Dict[str, Any], customer: Dict[str, Any], order: Dict[str, Any], decision: Any) -> Dict[str, Any]:
    # Handle both old and new decision format
    reason = getattr(decision, 'reason', None) or getattr(decision, 'rationale', 'Requires escalation')

    return {
        "success": True,
        "action": "escalate",
        "ticket_id": ticket.get("id"),
        "assigned_to": "human_agent",
        "priority": "high" if customer.get("priority") == "high" else "normal",
        "reason": reason,
        "requires_review": True
    }


def _execute_reply(ticket: Dict[str, Any], customer: Dict[str, Any], order: Dict[str, Any], decision: Any) -> Dict[str, Any]:
    message = f"Thank you for contacting us. We're investigating your {ticket.get('issue_type')} issue."

    # Handle both old and new decision format
    reason = getattr(decision, 'reason', None) or getattr(decision, 'rationale', '')

    if "refund" in reason.lower():
        message += " We're pleased to offer a partial refund as compensation."

    # Handle both old and new decision format for compensation
    compensation = "none"
    if hasattr(decision, 'estimated_impact') and isinstance(decision.estimated_impact, dict):
        compensation = decision.estimated_impact.get("compensation", "none")

    return {
        "success": True,
        "action": "reply",
        "ticket_id": ticket.get("id"),
        "customer_email": customer.get("email"),
        "message": message,
        "compensation": compensation,
        "reason": reason
    }

# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Helper Functions
# Description: Utility functions and data processing
# =========================================================

from datetime import datetime
from typing import Any, Dict


def calculate_days_since(date_str: str) -> int:
    """Calculate days elapsed since a date."""
    try:
        date = datetime.fromisoformat(date_str)
        return (datetime.utcnow() - date).days
    except Exception:
        return 999


def is_vip_customer(customer: Dict[str, Any]) -> bool:
    """Check if customer is VIP."""
    return customer.get("tier") in ("vip", "premium")


def is_high_refund_window(order: Dict[str, Any], product: Dict[str, Any]) -> bool:
    """Check if order is within refund window."""
    days = order.get("days_since_purchase", 999)
    window = product.get("refund_window_days", 30)
    return days <= window


def calculate_refund_amount(order: Dict[str, Any], customer: Dict[str, Any], percentage: float = 1.0) -> float:
    """Calculate final refund amount with adjustments."""
    base = order.get("amount", 0)
    adjusted = base * percentage

    if not is_vip_customer(customer):
        adjusted = adjusted * 0.95

    return round(adjusted, 2)


def format_currency(amount: float) -> str:
    """Format amount as currency."""
    return f"${amount:.2f}"


def extract_severity(issue_type: str) -> str:
    """Determine issue severity."""
    severe = ["damaged", "fraud", "missing", "delivery_failed"]
    return "high" if issue_type.lower() in severe else "medium" if issue_type else "low"

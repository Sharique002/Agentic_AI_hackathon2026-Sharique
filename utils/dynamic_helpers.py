# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Dynamic Ticket Helpers
# Description: Functions to support real user input pipeline
# =========================================================

import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from tools.customer import get_customer
from tools.order import get_order
from utils.inference_engine import InferenceEngine
from utils.confidence_calculator import ConfidenceCalculator


def get_customer_by_email(email: str) -> Optional[Dict[str, Any]]:
    if not email:
        return None
    customer = get_customer(email)
    return customer


def get_customer_by_id(customer_id: str) -> Optional[Dict[str, Any]]:
    if not customer_id:
        return None

    try:
        data_path = Path(__file__).parent.parent / "data" / "customers.json"
        with open(data_path, "r") as f:
            customers = json.load(f)

        for customer in customers:
            if customer.get("customer_id") == customer_id or customer.get("id") == customer_id:
                return customer

    except Exception:
        pass

    return None


def find_relevant_order(
    customer_id: str,
    product_hint: Optional[str] = None,
    prefer_recent: bool = True,
    allow_inference: bool = True
) -> tuple[Optional[Dict[str, Any]], bool]:
    if not customer_id:
        return None, False

    try:
        data_path = Path(__file__).parent.parent / "data" / "orders.json"
        with open(data_path, "r") as f:
            orders = json.load(f)

        customer_orders = [
            order for order in orders
            if order.get("customer_id") == customer_id
        ]

        if not customer_orders:
            return None, False

        if product_hint:
            matching_orders = _filter_orders_by_product(customer_orders, product_hint)
            if matching_orders:
                matching_orders.sort(
                    key=lambda o: o.get("order_date", ""),
                    reverse=True
                )
                return matching_orders[0], False

        delivered = [
            o for o in customer_orders
            if o.get("status") == "delivered"
        ]
        if delivered:
            delivered.sort(
                key=lambda o: o.get("delivery_date", ""),
                reverse=True
            )
            return delivered[0], False

        customer_orders.sort(
            key=lambda o: o.get("order_date", ""),
            reverse=True
        )

        if customer_orders and allow_inference:
            return customer_orders[0], True

        return customer_orders[0] if customer_orders else None, False

    except Exception:
        return None, False


def _filter_orders_by_product(orders: list, product_hint: str) -> list:
    try:
        data_path = Path(__file__).parent.parent / "data" / "products.json"
        with open(data_path, "r") as f:
            products = json.load(f)

        matching_products = []
        product_hint_lower = product_hint.lower()

        for product in products:
            product_name = product.get("name", "").lower()
            product_id = product.get("product_id")

            if product_hint_lower in product_name or product_name in product_hint_lower:
                matching_products.append(product_id)

        return [
            o for o in orders
            if o.get("product_id") in matching_products
        ]

    except Exception:
        return []


def create_dynamic_ticket(
    parsed_input: Dict[str, Any],
    customer: Dict[str, Any],
    order: Optional[Dict[str, Any]] = None,
    inferred: bool = False
) -> tuple[Dict[str, Any], bool]:
    ticket_id = f"dynamic_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    customer_id = customer.get("customer_id") or customer.get("id")
    order_id = order.get("order_id") or order.get("id") if order else None
    product_id = order.get("product_id") if order else None

    confidence = parsed_input.get("confidence", 0.5)
    issue_type = parsed_input.get("issue_type", "inquiry")
    intent = parsed_input.get("intent", "inquiry")

    if confidence < 0.6 and intent == "refund_request":
        issue_type = "ask_clarification"
    elif confidence < 0.6:
        issue_type = "ask_clarification"

    ticket = {
        "ticket_id": ticket_id,
        "id": ticket_id,
        "customer_id": customer_id,
        "customer_email": customer.get("email"),
        "order_id": order_id,
        "product_id": product_id,
        "issue_type": issue_type,
        "subject": _generate_subject(parsed_input, issue_type),
        "body": parsed_input.get("raw_text"),
        "source": "user_input",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "tier": _map_tier_to_ticket_tier(customer.get("tier")),
        "is_dynamic": True,
        "parsing_confidence": confidence,
        "user_intent": intent,
        "urgency": parsed_input.get("urgency", "normal"),
        "inferred": inferred
    }

    return ticket, inferred


def _generate_subject(parsed_input: Dict[str, Any], issue_type: str) -> str:
    issue = parsed_input.get("issue_type", "inquiry")
    product = parsed_input.get("product_hint")

    if issue_type == "ask_clarification":
        return "Clarification needed"

    parts = []

    if issue == "damaged":
        parts.append("Damaged item")
    elif issue == "defective":
        parts.append("Defective product")
    elif issue == "wrong_item":
        parts.append("Wrong item received")
    elif issue == "cancellation":
        parts.append("Cancellation request")
    elif issue == "refund_status":
        parts.append("Refund status inquiry")
    elif issue == "shipping_inquiry":
        parts.append("Shipping inquiry")
    else:
        parts.append("Customer inquiry")

    if product:
        parts.append(f"({product})")

    return " ".join(parts)


def _map_tier_to_ticket_tier(customer_tier: str) -> int:
    tier_map = {
        "vip": 1,
        "premium": 2,
        "standard": 1,
        "basic": 1
    }
    return tier_map.get(customer_tier, 1)


def validate_user_input(email: Optional[str] = None, customer_id: Optional[str] = None) -> tuple[bool, str]:
    if not email and not customer_id:
        return False, "ERROR: Please provide either email address or customer ID"

    if email:
        customer = get_customer_by_email(email)
        if not customer:
            return False, f"ERROR: Customer with email '{email}' not found in system"
        return True, ""

    if customer_id:
        customer = get_customer_by_id(customer_id)
        if not customer:
            return False, f"ERROR: Customer with ID '{customer_id}' not found in system"
        return True, ""

    return False, "ERROR: Invalid customer identification"


def normalize_policy_name(policy: str) -> str:
    """Ensure policy name is safe and standard."""
    allowed_policies = {
        "vip_override_policy",
        "fraud_detection_policy",
        "warranty_escalation_policy",
        "damaged_item_policy",
        "return_policy",
        "inquiry_policy",
        "refund_policy",
        "knowledge_base_inquiry",
        "standard_policy"
    }

    if policy in allowed_policies:
        return policy

    policy_lower = policy.lower().strip()

    if "vip" in policy_lower or "override" in policy_lower:
        return "vip_override_policy"
    elif "fraud" in policy_lower:
        return "fraud_detection_policy"
    elif "warranty" in policy_lower:
        return "warranty_escalation_policy"
    elif "damaged" in policy_lower or "damage" in policy_lower:
        return "damaged_item_policy"
    elif "return" in policy_lower:
        return "return_policy"
    elif "inquiry" in policy_lower or "question" in policy_lower:
        return "inquiry_policy"
    elif "refund" in policy_lower:
        return "refund_policy"

    return "standard_policy"


def generate_reasoning(
    issue_type: str,
    customer_tier: str,
    order_status: Optional[str],
    decision: str,
    product_name: Optional[str] = None
) -> str:
    """Generate human-readable reasoning for decision."""

    if decision == "ask_clarification":
        if not product_name:
            return "Need clarification on which product and what issue occurred."
        return f"Need more details about the {product_name} issue to make a decision."

    if decision == "reply":
        if issue_type == "inquiry":
            return "Customer inquiry. Providing information from knowledge base."
        if issue_type == "shipping_inquiry":
            return "Checking shipping status and tracking information."
        return "Responding to customer inquiry."

    if decision == "escalate":
        if customer_tier == "vip":
            return f"VIP customer with {issue_type} issue. Escalating for priority handling."
        if issue_type == "damaged":
            return "Item arrived damaged. Escalating for immediate replacement or refund."
        if issue_type == "fraud":
            return "Fraud detected. Escalating for investigation."
        if issue_type == "defective":
            return f"Product defect reported. Escalating for warranty evaluation."
        if issue_type == "wrong_item":
            return "Wrong item received. Escalating for immediate exchange or refund."
        return "Escalating for manual review."

    if decision == "refund":
        reason = f"Issuing refund for {issue_type} "
        if product_name:
            reason += f"{product_name} "
        reason += f"({customer_tier} customer)"
        return reason

    if decision == "exchange":
        product_text = f"{product_name} " if product_name else ""
        return f"Authorizing exchange for {product_text}due to {issue_type}."

    return "Processing request according to policy."


def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """Fetch product data by ID."""
    if not product_id:
        return None

    try:
        data_path = Path(__file__).parent.parent / "data" / "products.json"
        with open(data_path, "r") as f:
            products = json.load(f)

        for product in products:
            if product.get("product_id") == product_id or product.get("id") == product_id:
                return product

    except Exception:
        pass

    return None

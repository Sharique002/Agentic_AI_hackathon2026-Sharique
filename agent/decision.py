# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Decision Engine (Enhanced)
# Description: Production-grade decision logic with policy integration
# =========================================================

import os
import json
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime


class DecisionType(Enum):
    REFUND = "refund"
    CANCEL = "cancel"
    ESCALATE = "escalate"
    REPLY = "reply"


@dataclass
class Decision:
    decision_type: DecisionType
    confidence: float
    rationale: str
    estimated_impact: Dict[str, Any]
    policy_applied: str = "default"
    requires_escalation: bool = False


class DecisionEngine:
    def __init__(self):
        self.min_confidence = 0.60
        self.knowledge_base = self._load_knowledge_base()
        self.non_returnable_categories = ["hazmat", "hygiene", "restricted"]
        self.high_risk_keywords = [
            "chargeback", "fraud", "fake", "unauthorized", "stolen", "dispute"
        ]

    def _load_knowledge_base(self) -> str:
        kb_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "knowledge-base.md"
        )
        with open(kb_path, "r") as f:
            return f.read()

    def search_knowledge_base(self, query: str) -> str:
        """Search knowledge base for relevant policies."""
        kb_lower = self.knowledge_base.lower()
        query_lower = query.lower()

        if "refund" in query_lower:
            section_start = kb_lower.find("refund policy")
            if section_start > -1:
                section_end = kb_lower.find("###", section_start + 1)
                if section_end == -1:
                    section_end = len(self.knowledge_base)
                return self.knowledge_base[section_start:section_end]

        if "escalat" in query_lower:
            section_start = kb_lower.find("escalation criteria")
            if section_start > -1:
                section_end = kb_lower.find("###", section_start + 1)
                if section_end == -1:
                    section_end = len(self.knowledge_base)
                return self.knowledge_base[section_start:section_end]

        if "damaged" in query_lower or "defect" in query_lower:
            section_start = kb_lower.find("damaged goods")
            if section_start > -1:
                section_end = kb_lower.find("\n\n", section_start + 1)
                return self.knowledge_base[section_start:section_end]

        return "General policy: Refer to standard resolution procedures"

    def _detect_fraud(self, ticket: Dict[str, Any], customer: Dict[str, Any], order: Dict[str, Any]) -> bool:
        """Detect fraud indicators."""
        notes = (ticket.get("notes", "") + customer.get("notes", "")).lower()
        for keyword in self.high_risk_keywords:
            if keyword in notes:
                return True

        if customer.get("risk") == "high":
            return True

        issue = ticket.get("issue_type", "").lower()
        days = ticket.get("days_since_purchase", 999)

        if issue in ("missing_items", "not_received") and days > 90:
            return True

        if order.get("amount", 0) > 1000 and days < 2:
            return True

        return False

    def _validate_return_window(
        self, product: Dict[str, Any], order: Dict[str, Any], issue_type: str
    ) -> tuple[bool, int, str]:
        """
        Validate if order is within return window.
        Returns: (is_eligible, window_days, policy_name)
        """
        policy = product.get("refund_policy", "none")
        category = product.get("category", "").lower()
        days_since = order.get("days_since_purchase", 999)

        if category in self.non_returnable_categories:
            return False, 0, "non_returnable"

        if policy == "none":
            return False, 0, "no_refund_policy"

        if policy == "extended":
            window = 90
            return days_since <= window, window, "extended_refund"

        if policy == "standard":
            window = 30
            return days_since <= window, window, "standard_refund"

        return False, 0, "unknown_policy"

    def _check_warranty(self, product: Dict[str, Any], order: Dict[str, Any]) -> bool:
        """Check if warranty applies."""
        warranty_days = product.get("warranty_days", 0)
        days_since = order.get("days_since_purchase", 999)
        return warranty_days > 0 and days_since <= warranty_days

    def _validate_data_completeness(
        self, ticket: Dict[str, Any], customer: Dict[str, Any],
        order: Dict[str, Any], product: Dict[str, Any]
    ) -> tuple[bool, str]:
        """Validate all required data is present."""
        if not customer:
            return False, "missing_customer_data"
        if not order:
            return False, "missing_order_data"
        if not product:
            return False, "missing_product_data"
        if not ticket.get("issue_type"):
            return False, "missing_issue_type"

        return True, "complete"

    def evaluate(
        self,
        ticket: Dict[str, Any],
        customer: Dict[str, Any],
        order: Dict[str, Any],
        product: Dict[str, Any],
    ) -> Decision:
        """
        Enhanced decision engine with policy integration and fraud detection.
        """
        # Validate data
        is_valid, validation_error = self._validate_data_completeness(
            ticket, customer, order, product
        )
        if not is_valid:
            return Decision(
                decision_type=DecisionType.ESCALATE,
                confidence=0.55,
                rationale=f"Incomplete data: {validation_error}",
                estimated_impact={"requires_manual_review": True},
                policy_applied="data_validation"
            )

        # Extract signals
        issue_type = ticket.get("issue_type", "").lower()
        customer_tier = customer.get("tier", "standard")
        days_since = order.get("days_since_purchase", 999)
        order_amount = order.get("amount", 0)
        customer_lifetime = customer.get("lifetime_value", 0)

        # Check fraud
        is_fraud = self._detect_fraud(ticket, customer, order)
        if is_fraud:
            return Decision(
                decision_type=DecisionType.ESCALATE,
                confidence=0.95,
                rationale="Fraud indicators detected - requires investigation",
                estimated_impact={"requires_manual_review": True},
                policy_applied="fraud_detection",
                requires_escalation=True
            )

        # DAMAGED / DEFECTIVE ITEMS → Always refund
        if issue_type in ("damaged", "defective", "broken"):
            is_eligible, window, policy = self._validate_return_window(product, order, issue_type)
            policy_ref = self.search_knowledge_base("damaged goods")

            if is_eligible:
                return Decision(
                    decision_type=DecisionType.REFUND,
                    confidence=0.98,
                    rationale=f"Damaged product within {window}-day window. {policy_ref[:100]}...",
                    estimated_impact={
                        "refund_amount": order_amount,
                        "churn_risk": "low",
                        "warranty_applied": self._check_warranty(product, order)
                    },
                    policy_applied=policy
                )
            else:
                return Decision(
                    decision_type=DecisionType.ESCALATE,
                    confidence=0.75,
                    rationale=f"Damaged item outside return window ({days_since} days) - escalate for warranty review",
                    estimated_impact={"requires_manual_review": True},
                    policy_applied="warranty_review",
                    requires_escalation=True
                )

        # NOT AS DESCRIBED / WRONG ITEM
        if issue_type in ("not_as_described", "wrong_item", "missing_items"):
            is_eligible, window, policy = self._validate_return_window(product, order, issue_type)

            if is_eligible:
                if customer_tier in ("vip", "premium"):
                    return Decision(
                        decision_type=DecisionType.REFUND,
                        confidence=0.92,
                        rationale=f"VIP/Premium tier with legitimate complaint within {window}-day window",
                        estimated_impact={
                            "refund_amount": order_amount,
                            "churn_risk": "low"
                        },
                        policy_applied=policy
                    )
                else:
                    return Decision(
                        decision_type=DecisionType.REPLY,
                        confidence=0.80,
                        rationale=f"Standard customer - offer partial refund or exchange within {window}-day window",
                        estimated_impact={
                            "refund_amount": order_amount * 0.75,
                            "churn_risk": "medium"
                        },
                        policy_applied=policy
                    )
            else:
                return Decision(
                    decision_type=DecisionType.ESCALATE,
                    confidence=0.70,
                    rationale=f"Complaint outside return window ({days_since} days) - escalate for review",
                    estimated_impact={"requires_manual_review": True},
                    policy_applied="window_exceeded",
                    requires_escalation=True
                )

        # LATE DELIVERY
        if issue_type in ("late_delivery", "not_received", "delivery_issue"):
            if order.get("status") in ("shipped", "in_transit"):
                refund_percent = 0.15 if days_since > 7 else 0.10
                return Decision(
                    decision_type=DecisionType.REPLY,
                    confidence=0.85,
                    rationale=f"Delayed shipment - offer {refund_percent*100}% store credit + tracking update",
                    estimated_impact={
                        "compensation": "store_credit",
                        "credit_amount": order_amount * refund_percent
                    },
                    policy_applied="delivery_delay"
                )

            elif days_since < 7:
                return Decision(
                    decision_type=DecisionType.CANCEL,
                    confidence=0.92,
                    rationale="Immediate delivery failure - cancel and reship at no cost",
                    estimated_impact={
                        "reship_cost": order_amount * 0.08,
                        "tracking_required": True
                    },
                    policy_applied="immediate_reship"
                )

        # MISSING DATA / UNCLEAR ISSUE
        if not issue_type or issue_type == "other":
            return Decision(
                decision_type=DecisionType.ESCALATE,
                confidence=0.50,
                rationale="Issue type unclear or requires clarification from customer",
                estimated_impact={"requires_clarification": True},
                policy_applied="needs_clarification",
                requires_escalation=True
            )

        # HIGH-VALUE ORDERS → Always escalate for review
        if order_amount > 500 or customer_lifetime > 2000:
            return Decision(
                decision_type=DecisionType.ESCALATE,
                confidence=0.80,
                rationale=f"High-value order (${order_amount}) or VIP customer - requires management review",
                estimated_impact={"requires_manual_review": True},
                policy_applied="high_value_escalation",
                requires_escalation=True
            )

        # DEFAULT: Escalate if uncertain
        return Decision(
            decision_type=DecisionType.ESCALATE,
            confidence=0.55,
            rationale="Issue does not match standard resolution paths - requires human judgment",
            estimated_impact={"requires_manual_review": True},
            policy_applied="default_escalation",
            requires_escalation=True
        )

    def is_confident(self, decision: Decision) -> bool:
        """Check if decision confidence meets threshold."""
        return decision.confidence >= self.min_confidence

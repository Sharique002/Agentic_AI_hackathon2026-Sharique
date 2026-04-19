# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Agent Brain (Enhanced with Retry Logic)
# Description: ReAct-style reasoning with failure handling
# =========================================================

import asyncio
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Import the validated decision engine
sys.path.insert(0, str(Path(__file__).parent.parent))
from decision_engine import DecisionEngine as ValidatedDecisionEngine

from tools.customer import get_customer
from tools.order import get_order
from tools.product import get_product
from tools.actions import execute_action


class AgentBrain:
    def __init__(self, logger):
        self.logger = logger
        self.decision_engine = ValidatedDecisionEngine()
        self.max_iterations = 5
        self.max_retries = 2
        self.retry_delay_ms = 500

    async def process_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced ReAct-style reasoning loop with retry logic and detailed logging.
        Sequence: Observe → Reason → Act → (repeat if needed)
        """
        start_time = time.time()
        execution_id = ticket.get("id", ticket.get("ticket_id", "unknown"))

        self.logger.log("TICKET", f"Starting processing", {
            "ticket_id": execution_id,
            "issue": ticket.get("issue_type")
        })

        context = {
            "ticket": ticket,
            "customer": None,
            "order": None,
            "product": None,
            "decision": None,
            "actions_taken": [],
            "tools_used": [],
            "iterations": 0,
            "errors": [],
            "policy_applied": "unknown",
        }

        # ITERATION LOOP
        for iteration in range(self.max_iterations):
            context["iterations"] = iteration + 1

            # Step 1: OBSERVE (Gather data with retry)
            await self._observe_with_retry(context)
            if context.get("error"):
                break

            # Step 2: REASON (Make decision)
            await self._reason(context)
            if context.get("error"):
                break

            # Step 3: ACT (Execute decision)
            await self._act(context)

            # Step 4: REFLECT (Check if complete)
            if context.get("decision"):
                break

        # Processing complete
        processing_time_ms = int((time.time() - start_time) * 1000)

        decision_obj = context.get("decision")
        decision_type = decision_obj.decision_type if decision_obj else "escalate"
        confidence = decision_obj.confidence if decision_obj else 0.0
        reason = decision_obj.reason if decision_obj else "Unknown reason"
        escalated = decision_obj.requires_escalation if decision_obj else False
        policy = decision_obj.policy_applied if decision_obj else "unknown"

        # Structured audit log
        if context.get("customer"):
            self.logger.log_ticket_decision(
                ticket_id=execution_id,
                customer_tier=context["customer"].get("tier", "unknown"),
                tools_used=context["tools_used"],
                policy_applied=policy,
                decision=decision_type,
                confidence=confidence,
                rationale=reason,
                estimated_impact={},
                escalated=escalated,
                fraud_detected="fraud" in policy.lower()
            )

        # Summary entry
        self.logger.create_summary_entry(
            ticket_id=execution_id,
            processing_time_ms=processing_time_ms,
            status="completed" if not context.get("error") else "failed",
            metrics={
                "tools_called": len(context["tools_used"]),
                "iterations": context["iterations"],
                "decision_confidence": round(confidence, 2),
                "escalated": escalated
            }
        )

        result = {
            "ticket_id": execution_id,
            "status": "completed" if not context.get("error") else "failed",
            "decision": decision_type,
            "confidence": round(confidence, 2),
            "escalated": escalated,
            "tools_used": context["tools_used"],
            "policy_applied": policy,
            "actions": context.get("actions_taken", []),
            "iterations": context["iterations"],
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.utcnow().isoformat()
        }

        return result

    async def _observe_with_retry(self, context: Dict[str, Any]) -> None:
        """Gather all data with automatic retry on failure."""
        ticket = context["ticket"]
        customer_email = ticket.get("customer_email")
        order_id = ticket.get("order_id")
        product_id = ticket.get("product_id")

        # Fetch customer with retry
        if customer_email and not context.get("customer"):
            customer = await self._fetch_with_retry(
                get_customer, customer_email, "customer", context
            )
            if customer:
                context["customer"] = customer
                context["tools_used"].append("get_customer")
            else:
                context["error"] = f"Customer not found after retries: {customer_email}"
                return

        # Fetch order with retry
        if order_id and not context.get("order"):
            order = await self._fetch_with_retry(
                get_order, order_id, "order", context
            )
            if order:
                context["order"] = order
                context["tools_used"].append("get_order")
            else:
                context["error"] = f"Order not found after retries: {order_id}"
                return

        # Fetch product with retry
        if product_id and not context.get("product"):
            product = await self._fetch_with_retry(
                get_product, product_id, "product", context
            )
            if product:
                context["product"] = product
                context["tools_used"].append("get_product")
            else:
                context["error"] = f"Product not found after retries: {product_id}"
                return

    async def _fetch_with_retry(
        self,
        func,
        param: str,
        tool_name: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Fetch data with automatic retry logic."""
        ticket_id = context["ticket"].get("id", "unknown")

        for attempt in range(self.max_retries + 1):
            try:
                result = await self._async_wrapper(func, param)

                if result:
                    self.logger.log_tool_call(
                        ticket_id=ticket_id,
                        tool_name=tool_name,
                        status="success",
                        result={"data_present": True},
                        retry_count=attempt
                    )
                    return result
                else:
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay_ms / 1000)
                        continue
                    else:
                        self.logger.log_tool_call(
                            ticket_id=ticket_id,
                            tool_name=tool_name,
                            status="not_found",
                            error=f"Data not found: {param}",
                            retry_count=attempt
                        )
                        return None

            except Exception as e:
                error_msg = str(e)

                if attempt < self.max_retries:
                    self.logger.log_tool_call(
                        ticket_id=ticket_id,
                        tool_name=tool_name,
                        status="retry",
                        error=error_msg,
                        retry_count=attempt
                    )
                    await asyncio.sleep(self.retry_delay_ms / 1000)
                else:
                    self.logger.log_error(
                        ticket_id=ticket_id,
                        component=tool_name,
                        error_message=error_msg,
                        error_type="tool_failure"
                    )
                    context["errors"].append({
                        "tool": tool_name,
                        "error": error_msg,
                        "attempts": attempt + 1
                    })
                    return None

        return None

    async def _reason(self, context: Dict[str, Any]) -> None:
        """Apply decision logic with reasoning tracking."""
        if not context.get("ticket"):
            return

        try:
            from decision_engine import Ticket, Customer, Order, Product

            ticket_dict = context["ticket"]
            customer_dict = context.get("customer")
            order_dict = context.get("order")
            product_dict = context.get("product")

            # Convert dicts to dataclass objects for validated engine
            ticket = Ticket(
                id=ticket_dict.get("id", ticket_dict.get("ticket_id", "")),
                issue_type=ticket_dict.get("issue_type", ""),
                body=ticket_dict.get("body", "")
            )

            customer = None
            if customer_dict:
                customer = Customer(
                    id=customer_dict.get("customer_id", customer_dict.get("id", "")),
                    tier=customer_dict.get("tier", "standard"),
                    notes=customer_dict.get("notes")
                )

            order = None
            if order_dict:
                return_deadline = None
                if order_dict.get("return_deadline"):
                    try:
                        deadline_str = order_dict.get("return_deadline")
                        if isinstance(deadline_str, str):
                            return_deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                        elif isinstance(deadline_str, datetime):
                            return_deadline = deadline_str
                    except:
                        return_deadline = None

                order = Order(
                    id=order_dict.get("order_id", order_dict.get("id", "")),
                    status=order_dict.get("status", "unknown"),
                    refund_status=order_dict.get("refund_status"),
                    notes=order_dict.get("notes"),
                    return_deadline=return_deadline
                )

            product = None
            if product_dict:
                product = Product(
                    id=product_dict.get("id", product_dict.get("product_id", "")),
                    return_window_days=product_dict.get("return_window_days", 0),
                    warranty_months=product_dict.get("warranty_months", 0),
                    returnable=product_dict.get("returnable", True),
                    notes=product_dict.get("notes")
                )

            # Use validated decision engine
            decision = self.decision_engine.process_ticket(ticket, customer, order, product)
            context["decision"] = decision
            context["policy_applied"] = decision.policy_applied

            # Log reasoning factors
            factors = {
                "issue_type": ticket_dict.get("issue_type", "unknown"),
                "customer_tier": customer_dict.get("tier") if customer_dict else "unknown",
                "product_returnable": product_dict.get("returnable") if product_dict else None,
                "product_warranty": product_dict.get("warranty_months", 0) if product_dict else None,
                "return_window_days": product_dict.get("return_window_days", 0) if product_dict else None,
            }

            self.logger.log_reasoning(
                ticket_id=ticket_dict.get("id"),
                issue_type=ticket_dict.get("issue_type", "unknown"),
                factors=factors,
                decision_logic=decision.reason
            )

            self.logger.log("REASONING", "Decision made", {
                "ticket_id": ticket_dict.get("id"),
                "decision": str(decision.decision_type),
                "confidence": decision.confidence,
                "policy": decision.policy_applied,
                "escalated": decision.requires_escalation
            })

        except Exception as e:
            context["error"] = str(e)
            self.logger.log_error(
                ticket_id=context["ticket"].get("id"),
                component="decision_engine",
                error_message=str(e),
                error_type="reasoning"
            )

    async def _act(self, context: Dict[str, Any]) -> None:
        """Execute the decision."""
        decision = context.get("decision")
        if not decision:
            return

        try:
            decision_type = str(decision.decision_type)

            action_result = await self._async_wrapper(
                execute_action,
                decision_type,
                context["ticket"],
                context["customer"],
                context["order"],
                decision
            )

            context["actions_taken"].append({
                "action": decision_type,
                "result": action_result
            })

            self.logger.log("ACTION", "Action executed", {
                "ticket_id": context["ticket"].get("id"),
                "action": decision_type,
                "success": action_result.get("success", True)
            })

        except Exception as e:
            context["error"] = str(e)
            self.logger.log_error(
                ticket_id=context["ticket"].get("id"),
                component="action_executor",
                error_message=str(e),
                error_type="action_failed"
            )

    @staticmethod
    async def _async_wrapper(func, *args, **kwargs):
        """Convert sync function to async."""
        return await asyncio.to_thread(func, *args, **kwargs)

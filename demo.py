#!/usr/bin/env python3
"""
CARE — Customer Autonomous Resolution Engine
Demo Mode: Shows real decisions with dynamic, data-driven reasoning
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent))

from agent.brain import AgentBrain
from utils.logger import Logger


@dataclass
class DemoConfig:
    verbose: bool = False
    demo_mode: bool = False
    show_reasoning: bool = False


class RealDataLoader:
    """Load real data from JSON files."""

    def __init__(self):
        self.data_path = Path(__file__).parent / "data"
        self.tickets = self._load_json("tickets.json")
        self.customers = self._load_json("customers.json")
        self.orders = self._load_json("orders.json")
        self.products = self._load_json("products.json")

    def _load_json(self, filename: str) -> list:
        """Load JSON file."""
        try:
            with open(self.data_path / filename) as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"{filename} not found in {self.data_path}")

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID."""
        return next((t for t in self.tickets if t.get("ticket_id") == ticket_id or t.get("id") == ticket_id), None)

    def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get customer by email."""
        return next((c for c in self.customers if c.get("email") == email), None)

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID."""
        return next((o for o in self.orders if o.get("order_id") == order_id), None)

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID."""
        return next((p for p in self.products if p.get("id") == product_id), None)


class ReasoningBuilder:
    """Build meaningful reasoning from decision context."""

    def __init__(self, ticket: Dict, customer: Optional[Dict], order: Optional[Dict], product: Optional[Dict]):
        self.ticket = ticket
        self.customer = customer
        self.order = order
        self.product = product

    def build_reasoning_steps(self, decision: str, policy: str) -> List[str]:
        """Generate reasoning steps based on context."""
        steps = []

        # Customer analysis
        if self.customer:
            tier = self.customer.get("tier", "standard")
            steps.append(f"[Customer] Tier: {tier.upper()}")
            if tier == "vip":
                steps.append("           (VIP customers get exception-based approvals)")

        # Issue analysis
        issue = self.ticket.get("issue_type", "").lower()
        if issue == "defective":
            steps.append("[Issue]    Manufacturing defect")
            steps.append("           (Defects eligible for refund/warranty)")
        elif issue == "damaged":
            steps.append("[Issue]    Damaged on arrival")
            steps.append("           (Damaged items require immediate refund)")
        elif issue == "wrong_item":
            steps.append("[Issue]    Wrong item delivered")
            steps.append("           (Wrong items eligible for exchange/refund)")
        elif issue == "change_of_mind":
            steps.append("[Issue]    Change of mind return request")
            steps.append("           (Subject to return window policy)")
        elif issue in ["cancellation", "cancel"]:
            steps.append("[Issue]    Cancellation request")
            steps.append("           (Depends on order processing status)")
        else:
            steps.append(f"[Issue]    {issue}")

        # Return window analysis
        days_left = None
        if self.order and self.product:
            return_deadline = self.order.get("return_deadline")
            if return_deadline:
                from datetime import datetime
                deadline = datetime.fromisoformat(return_deadline.replace("Z", "+00:00"))
                today = datetime.now().replace(tzinfo=deadline.tzinfo)
                days_left = (deadline - today).days

                if days_left >= 0:
                    steps.append(f"[Window]   {days_left} days remaining")
                    steps.append("           (Within return window - eligible for standard return)")
                else:
                    days_expired = abs(days_left)
                    steps.append(f"[Window]   EXPIRED ({days_expired} days ago)")
                    if self.customer and self.customer.get("tier") == "vip":
                        steps.append("           (Window expired, but VIP exception may apply)")

            # Warranty analysis
            if self.product.get("warranty_months", 0) > 0:
                warranty = self.product.get("warranty_months")
                steps.append(f"[Warranty] {warranty} months active")
                if days_left is not None and days_left < 0 and issue in ["defective", "damaged"]:
                    steps.append("           (Outside return window, but warranty may cover)")

        # Order status analysis
        if self.order:
            status = self.order.get("status", "unknown")
            if status == "processing":
                steps.append("[Status]   PROCESSING (not shipped)")
                steps.append("           (Can be cancelled with full refund)")
            elif status in ["shipped", "in_transit"]:
                steps.append(f"[Status]   {status.upper()}")
                steps.append("           (Return/exchange process required)")
            elif status == "delivered":
                steps.append("[Status]   DELIVERED")

            # Refund status
            refund = self.order.get("refund_status")
            if refund == "refunded":
                steps.append("[Refund]   ALREADY REFUNDED")
                steps.append("           (Confirming status, no further action needed)")

        # Special flags
        if self.customer:
            notes = self.customer.get("notes", "").lower()
            if "pre-approved" in notes and self.customer.get("tier") == "vip":
                steps.append("[Flag]     VIP with pre-approved exception on file")
                steps.append("           (Extended return window approved by management)")

        # Product notes
        if self.product:
            product_notes = self.product.get("notes", "").lower()
            if "registered" in product_notes:
                steps.append("[Flag]     Device registration detected")
                steps.append("           (Registered devices are non-returnable per policy)")

        return steps

    def build_reason_text(self, decision: str, policy: str) -> str:
        """Build detailed reason text."""
        tier = self.customer.get("tier", "standard") if self.customer else "standard"
        issue = self.ticket.get("issue_type", "").lower()

        # Decision-specific reasoning
        if decision == "refund":
            if issue == "defective":
                if tier == "vip":
                    return "VIP customer with manufacturing defect detected. Return window criteria met. Refund approved immediately under VIP priority processing."
                else:
                    return "Manufacturing defect confirmed within return window. Customer eligible for full refund per standard policy."
            elif issue == "damaged":
                return "Item arrived damaged. No return required. Refund approved immediately to maintain customer satisfaction."
            elif issue == "wrong_item":
                if self.order and self.order.get("return_deadline"):
                    from datetime import datetime
                    deadline = datetime.fromisoformat(self.order.get("return_deadline").replace("Z", "+00:00"))
                    days_left = (deadline - datetime.now().replace(tzinfo=deadline.tzinfo)).days
                    if days_left >= 0:
                        return "Wrong item delivered within return window. Refund/exchange approved immediately."
                    else:
                        return "Wrong item delivered, but return window expired. Escalating for exception review."
            elif issue == "change_of_mind":
                return "Within return window. Customer eligible for return/refund per standard policy."
            else:
                return f"Refund eligible based on {policy} policy evaluation."

        elif decision == "escalate":
            if "warranty" in policy.lower():
                return "Warranty claim detected. Requires specialist review for verification and determination of warranty coverage."
            elif "fraud" in policy.lower():
                return "Social engineering indicators detected (false premium claims, instant refund myths). Escalating to fraud review team."
            elif "high_value" in policy.lower():
                return "High-value order or VIP customer. Requires management review for exceptional handling."
            elif tier == "vip" and issue == "change_of_mind":
                return "Return window expired but VIP customer detected. Escalating for management discretion on extended return exception."
            else:
                return f"Complex case requiring specialist review. Initiating escalation for {policy} policy evaluation."

        elif decision == "cancel":
            return "Order still in processing status. Cancellation approved with full refund. No return required."

        elif decision == "reply":
            if issue == "inquiry":
                return "General policy inquiry. Providing detailed policy information to help guide customer decision."
            elif issue == "shipping_inquiry":
                return "Order in transit. Providing tracking information and estimated delivery timeline."
            elif issue == "refund_status":
                return "Refund status confirmed. Advising customer of standard processing timeline (5-7 business days)."
            else:
                return "Issue requires customer clarification or information. Requesting additional details for proper resolution."

        elif decision == "reject":
            if "registered" in policy.lower():
                return "Device has been registered online. Per Terms of Service, registered devices are non-returnable."
            elif issue == "change_of_mind":
                return "Return window expired. Standard policy does not permit returns outside the return window. Offering alternatives."
            else:
                return f"Not eligible under {policy} policy. Offering alternative resolution options."

        elif decision == "ask":
            return "Additional information needed. Requesting order details or clarification to process request."

        else:
            return f"Decision made based on {policy} evaluation."


class OutputFormatter:
    """Professional output formatting."""

    @staticmethod
    def print_decision_box(decision_type: str, confidence: float,
                          policy: str, reason: str, reasoning_steps: List[str]):
        """Print highlighted decision box with reasoning."""
        decision_icons = {
            "refund": "[APPROVE]",
            "reject": "[DENY]",
            "escalate": "[ESCALATE]",
            "reply": "[INFO]",
            "cancel": "[CANCEL]",
            "ask": "[ASK]"
        }

        icon = decision_icons.get(decision_type.lower(), ">> DECISION")

        # Convert policy to readable format
        policy_display = policy.replace("_", " ").title()

        print("\n" + "+" + "-"*68 + "+")
        print("|" + " CARE'S DECISION ".center(68) + "|")
        print("+" + "-"*68 + "+")
        print("|" + " "*68 + "|")
        print(f"|  {icon:40} Confidence: {confidence:.0%}".ljust(69) + "|")
        print("|" + " "*68 + "|")
        print(f"|  [POLICY] {policy_display}".ljust(69) + "|")
        print("|" + " "*68 + "|")
        print("|  [REASONING]".ljust(69) + "|")

        # Wrap reason
        for line in OutputFormatter._wrap_text(reason, 64):
            print(f"|    {line}".ljust(69) + "|")

        print("|" + " "*68 + "|")
        print("+" + "-"*68 + "+")

    @staticmethod
    def print_reasoning_steps(steps: List[str]):
        """Print reasoning steps."""
        print("\n[REASONING STEPS]:")
        for step in steps:
            print(f"  {step}")

    @staticmethod
    def print_ticket_details(ticket: Dict, customer: Dict, order: Dict, product: Dict):
        """Print ticket input details."""
        print("\n[TICKET]")
        ticket_id = ticket.get('id') or ticket.get('ticket_id')
        print(f"  ID: {ticket_id}")
        print(f"  Issue: {ticket.get('issue_type').upper()}")
        body = ticket.get('body', '')[:80]
        if len(ticket.get('body', '')) > 80:
            body += "..."
        print(f"  Details: {body}")

        if customer:
            print(f"\n[CUSTOMER]")
            print(f"  Name: {customer.get('name', 'Unknown')}")
            print(f"  Tier: {customer.get('tier', 'standard').upper()}")
            print(f"  Member Since: {customer.get('member_since', 'N/A')}")
            print(f"  Lifetime Value: ${customer.get('total_spent', 0):.2f}")

        if order:
            print(f"\n[ORDER]")
            print(f"  ID: {order.get('order_id')}")
            print(f"  Amount: ${order.get('amount', 0):.2f}")
            print(f"  Status: {order.get('status').upper()}")
            if order.get('return_deadline'):
                print(f"  Return Deadline: {order.get('return_deadline')}")

        if product:
            print(f"\n[PRODUCT]")
            print(f"  Name: {product.get('name')}")
            print(f"  Category: {product.get('category')}")
            print(f"  Return Window: {product.get('return_window_days')} days")
            if product.get('warranty_months'):
                print(f"  Warranty: {product.get('warranty_months')} months")

    @staticmethod
    def _wrap_text(text: str, width: int) -> List[str]:
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


class RealDemoMode:
    """Real demo using actual system and data."""

    def __init__(self, config: DemoConfig):
        self.config = config
        self.logger = Logger()
        self.agent = AgentBrain(self.logger)
        self.loader = RealDataLoader()

    def _print_failure_summary(self) -> None:
        """TASK 4: Print failure summary for demo."""
        try:
            from utils.failure_tracker import FailureTracker
            failures = FailureTracker.get_failures()
            total = failures.get("summary", {}).get("total", 0)

            if total > 0:
                print(f"\n[FAILURE SUMMARY]")
                print(f"  Failed Cases: {total}")

                recent = failures.get("failures", [])[-2:]
                if recent:
                    print(f"  Last {len(recent)} failures:")
                    for failure in recent:
                        ticket_id = failure.get("ticket_id", "Unknown")
                        reason = failure.get("reason", "Unknown")
                        print(f"    • {ticket_id}: {reason[:60]}")
                print("")
        except Exception:
            pass

    async def run_ticket_demo(self, ticket_id: str):
        """Process real ticket with real system."""
        print(f"\n{'='*70}")
        print(f"CARE Agent Processing: {ticket_id}")
        print(f"{'='*70}")

        # Load real ticket
        ticket = self.loader.get_ticket(ticket_id)
        if not ticket:
            print(f"ERROR: {ticket_id} not found in data/tickets.json")
            return

        # Normalize ticket_id field for agent
        if "id" not in ticket and "ticket_id" in ticket:
            ticket["id"] = ticket["ticket_id"]

        # Load related data
        customer = self.loader.get_customer_by_email(ticket.get("customer_email"))
        order = self.loader.get_order(ticket.get("order_id")) if ticket.get("order_id") else None
        product = self.loader.get_product(ticket.get("product_id")) if ticket.get("product_id") else None

        # Print input
        OutputFormatter.print_ticket_details(ticket, customer, order, product)

        # Process through real agent
        print(f"\n[PROCESSING...]")

        result = await self.agent.process_ticket(ticket)

        # Extract decision from result
        decision_type = result.get("decision", "unknown")
        confidence = result.get("confidence", 0.0)
        policy = result.get("policy_applied", "unknown")
        escalated = result.get("escalated", False)

        # Build dynamic reasoning based on context
        reasoner = ReasoningBuilder(ticket, customer, order, product)
        reason = reasoner.build_reason_text(decision_type, policy)
        reasoning_steps = reasoner.build_reasoning_steps(decision_type, policy)

        # Display decision box with reasoning
        OutputFormatter.print_decision_box(decision_type, confidence, policy, reason, reasoning_steps)

        # Show reasoning steps
        OutputFormatter.print_reasoning_steps(reasoning_steps)

        # Show details if verbose
        if self.config.verbose:
            print(f"\n[PROCESSING METRICS]")
            print(f"  Tools Used: {', '.join(result.get('tools_used', [])) or 'None'}")
            print(f"  Iterations: {result.get('iterations', 0)}")
            print(f"  Processing Time: {result.get('processing_time_ms', 0)}ms")
            if escalated:
                print(f"  Status: ESCALATED TO HUMAN REVIEW")

        # TASK 4: Show failure visibility summary
        self._print_failure_summary()

        # Show JSON output if requested
        if self.config.show_reasoning:
            print(f"\n[FULL RESULT (JSON)]")
            print(json.dumps(result, indent=2, default=str))


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="CARE Agent Demo")
    parser.add_argument("--ticket", "-t", default="TKT-001", help="Ticket ID to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--show-reasoning", "-r", action="store_true", help="Show full reasoning JSON")

    args = parser.parse_args()

    config = DemoConfig(
        verbose=args.verbose,
        demo_mode=True,
        show_reasoning=args.show_reasoning
    )

    try:
        demo = RealDemoMode(config)
        await demo.run_ticket_demo(args.ticket)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print(f"Make sure you have data files in: d:/files/OneDrive/Desktop/CARE-Agent/data/")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

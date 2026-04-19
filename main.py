# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Main Entry Point
# Description: Orchestrates ticket processing pipeline
# Supports: predefined tickets OR real user input
# =========================================================

import asyncio
import json
import os
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.brain import AgentBrain
from utils.logger import Logger
from utils.input_parser import parse_user_input
from utils.dynamic_helpers import (
    get_customer_by_email,
    get_customer_by_id,
    find_relevant_order,
    create_dynamic_ticket,
    validate_user_input,
    normalize_policy_name,
    generate_reasoning,
    get_product
)
from utils.inference_engine import InferenceEngine
from utils.confidence_calculator import ConfidenceCalculator
from utils.decision_explainer import DecisionExplainer
from utils.result_formatter import ResultFormatter
from utils.failure_tracker import FailureTracker


def _enforce_safety_rules(result: dict, inferred: bool = False) -> dict:
    if result.get("error"):
        return result

    if not result.get("decision"):
        result["decision"] = "ask_clarification"
    if not result.get("confidence") or result.get("confidence") == 0:
        result["confidence"] = 0.5

    result["confidence"] = ConfidenceCalculator.validate_confidence(result.get("confidence"))

    if not result.get("policy_applied") or result.get("policy_applied") == "Unknown":
        result["policy_applied"] = normalize_policy_name(result.get("policy_applied", "standard_policy"))
    else:
        result["policy_applied"] = normalize_policy_name(result.get("policy_applied"))

    if not result.get("reason"):
        result["reason"] = generate_reasoning(
            issue_type=result.get("issue_type", "inquiry"),
            customer_tier=result.get("customer_tier", "standard"),
            order_status=result.get("order_status"),
            decision=result.get("decision")
        )

    if result.get("decision") == "escalate" and not result.get("escalated"):
        result["escalated"] = True

    result["inferred"] = inferred

    return result


async def process_user_input(
    user_text: str,
    email: str = None,
    customer_id: str = None,
    logger: Logger = None,
    demo_mode: bool = False
) -> dict:
    """
    Process real user input through the CARE pipeline.

    Args:
        user_text: User's natural language input
        email: Customer email (optional, used if customer_id not provided)
        customer_id: Customer ID (optional)
        logger: Logger instance

    Returns:
        Processing result dict
    """
    # Validate input
    is_valid, error_msg = validate_user_input(email, customer_id)
    if not is_valid:
        print(f"\n{error_msg}\n")
        return {"error": error_msg, "status": "failed"}

    # Parse user input
    parsed = parse_user_input(user_text)
    logger.log("INPUT", "User input parsed", {
        "issue_type": parsed.get("issue_type"),
        "intent": parsed.get("intent"),
        "confidence": parsed.get("confidence")
    })

    # Fetch customer
    if email:
        customer = get_customer_by_email(email)
    else:
        customer = get_customer_by_id(customer_id)

    if not customer:
        error = "Customer not found"
        logger.log("ERROR", error, {"email": email, "customer_id": customer_id})
        print(f"\nERROR: {error}\n")
        return {"error": error, "status": "failed"}

    logger.log("CUSTOMER", "Customer fetched", {"customer_id": customer.get("customer_id")})

    # Find relevant order with smart inference
    product_hint = parsed.get("product_hint")
    order, inferred = find_relevant_order(
        customer.get("customer_id"),
        product_hint,
        allow_inference=True
    )

    if order:
        logger.log("ORDER", "Order matched", {
            "order_id": order.get("order_id"),
            "inferred": inferred
        })
    else:
        logger.log("ORDER", "No order found", {
            "customer_id": customer.get("customer_id"),
            "product_hint": product_hint
        })
        inferred = False

    # Get product data
    product = None
    if order:
        product = get_product(order.get("product_id"))

    # Create dynamic ticket
    ticket, inferred = create_dynamic_ticket(parsed, customer, order, inferred)
    logger.log("TICKET", "Dynamic ticket created", {"ticket_id": ticket.get("ticket_id")})

    # Process ticket through agent
    agent = AgentBrain(logger)
    result = await agent.process_ticket(ticket)

    result = _enforce_safety_rules(result, inferred)

    result = ResultFormatter.format_result(
        result,
        parsed,
        customer,
        order,
        product,
        inferred,
        demo_mode
    )

    if demo_mode:
        print(ResultFormatter.format_for_demo(result))

    return result


async def process_predefined_tickets(logger: Logger) -> tuple[int, int, int]:
    """
    Process predefined tickets from tickets.json.

    Args:
        logger: Logger instance

    Returns:
        Tuple of (total, successful, failed)
    """
    agent = AgentBrain(logger)
    FailureTracker.clear_failures()

    # Load tickets
    tickets_path = Path(__file__).parent / "data" / "tickets.json"

    if not tickets_path.exists():
        logger.log("ERROR", "Tickets file not found", {"path": str(tickets_path)})
        print(f"ERROR: {tickets_path} does not exist")
        return 0, 0, 0

    with open(tickets_path, "r") as f:
        tickets = json.load(f)

    logger.log("SYSTEM", f"Loaded {len(tickets)} tickets", {"count": len(tickets)})

    # Process tickets concurrently
    tasks = [agent.process_ticket(ticket) for ticket in tickets]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Summary and failure tracking
    successful = 0
    failed = 0

    for ticket, result in zip(tickets, results):
        if isinstance(result, dict) and result.get("status") == "completed":
            successful += 1
        elif isinstance(result, Exception):
            failed += 1
            ticket_id = ticket.get("ticket_id", "unknown")
            FailureTracker.log_failure(
                ticket_id,
                str(result),
                {"issue_type": ticket.get("issue_type")}
            )
        else:
            failed += 1
            ticket_id = ticket.get("ticket_id", "unknown")
            FailureTracker.log_failure(
                ticket_id,
                "Unknown failure",
                {"result_type": str(type(result))}
            )

    return len(tickets), successful, failed


async def main():
    parser = argparse.ArgumentParser(
        description="CARE — Customer Autonomous Resolution Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Process predefined tickets:
    python main.py

  Process user input:
    python main.py --input "I want a refund for my headphones" --email "alice.turner@email.com"

  Using customer ID instead of email:
    python main.py --input "My order arrived damaged" --customer-id "C001"
        """
    )

    parser.add_argument(
        "--input",
        type=str,
        help="User input text to process (natural language)"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Customer email address"
    )
    parser.add_argument(
        "--customer-id",
        type=str,
        help="Customer ID (alternative to email)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with detailed output"
    )

    args = parser.parse_args()

    logger = Logger()
    logger.log("SYSTEM", "Starting CARE Agent", {"status": "initialized"})

    # Route to appropriate handler
    if args.input:
        # User input mode
        logger.log("SYSTEM", "Running in user input mode", {"demo_mode": args.demo})

        result = await process_user_input(
            user_text=args.input,
            email=args.email,
            customer_id=args.customer_id,
            logger=logger,
            demo_mode=args.demo
        )

        if not args.demo:
            # Print result
            print(f"\n{'='*60}")
            print(f"CARE Agent Result — User Input")
            print(f"{'='*60}")

            if result.get("error"):
                print(f"Status: FAILED")
                print(f"Error: {result.get('error')}")
            else:
                print(f"Ticket ID: {result.get('ticket_id')}")
                print(f"Decision: {result.get('decision_type')}")
                print(f"Confidence: {result.get('confidence'):.0%}")
                print(f"Policy: {result.get('policy_applied')}")
                print(f"Escalated: {result.get('requires_escalation')}")
                if result.get('inferred'):
                    print(f"Order: Inferred from history")

            print(f"Audit Log: logs/audit_log.json")
            print(f"{'='*60}\n")

    else:
        # Predefined tickets mode
        logger.log("SYSTEM", "Running in predefined tickets mode", {})

        total, successful, failed = await process_predefined_tickets(logger)

        logger.log("SYSTEM", "Processing complete", {
            "total": total,
            "successful": successful,
            "failed": failed
        })

        print(f"\n{'='*60}")
        print(f"CARE Agent Execution Summary")
        print(f"{'='*60}")
        print(f"Total Tickets Processed: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Audit Log: logs/audit_log.json")

        if failed > 0:
            failures = FailureTracker.get_failures()
            print(f"Failed Cases Log: logs/failed_cases_log.json ({failures['summary']['total']} failures)")

        print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())

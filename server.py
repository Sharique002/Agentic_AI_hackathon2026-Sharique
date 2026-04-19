"""
CARE — Customer Autonomous Resolution Engine
Web API Server (FastAPI)
Serves the CARE agent as a REST API for the Next.js frontend.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

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
    get_product,
)
from utils.confidence_calculator import ConfidenceCalculator
from utils.result_formatter import ResultFormatter

# ─── App ─────────────────────────────────────────────────────

app = FastAPI(
    title="CARE API",
    description="Customer Autonomous Resolution Engine — REST API",
    version="1.0.0",
)

# ─── CORS (allow all origins for hackathon demo) ─────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request / Response Models ───────────────────────────────


class ProcessRequest(BaseModel):
    input: str = Field(..., description="Natural language customer message")
    email: Optional[str] = Field(None, description="Customer email address")
    customer_id: Optional[str] = Field(None, description="Customer ID (alternative to email)")


class ConfidenceBreakdown(BaseModel):
    data_completeness: Optional[float] = None
    policy_clarity: Optional[float] = None
    risk_penalty: Optional[float] = None
    inference_penalty: Optional[float] = None


class FraudDetails(BaseModel):
    claimed_tier: Optional[str] = None
    actual_tier: Optional[str] = None
    fraud_score: Optional[float] = None
    fraud_indicators: Optional[list] = None


class ProcessResponse(BaseModel):
    decision_type: Optional[str] = None
    confidence: Optional[float] = None
    confidence_reason: Optional[str] = None
    confidence_breakdown: Optional[ConfidenceBreakdown] = None
    policy_applied: Optional[str] = None
    reason: Optional[str] = None
    reasoning_steps: Optional[list] = None
    inferred: Optional[bool] = None
    inference_used: Optional[bool] = None
    explanation: Optional[str] = None
    alternatives: Optional[str] = None
    requires_escalation: Optional[bool] = None
    fraud_details: Optional[FraudDetails] = None
    error: Optional[str] = None
    status: Optional[str] = None


# ─── Helper: enforce safety rules (from main.py) ────────────


def _enforce_safety_rules(result: dict, inferred: bool = False) -> dict:
    if result.get("error"):
        return result

    if not result.get("decision"):
        result["decision"] = "ask_clarification"
    if not result.get("confidence") or result.get("confidence") == 0:
        result["confidence"] = 0.5

    result["confidence"] = ConfidenceCalculator.validate_confidence(result.get("confidence"))

    if not result.get("policy_applied") or result.get("policy_applied") == "Unknown":
        result["policy_applied"] = normalize_policy_name(
            result.get("policy_applied", "standard_policy")
        )
    else:
        result["policy_applied"] = normalize_policy_name(result.get("policy_applied"))

    if not result.get("reason"):
        result["reason"] = generate_reasoning(
            issue_type=result.get("issue_type", "inquiry"),
            customer_tier=result.get("customer_tier", "standard"),
            order_status=result.get("order_status"),
            decision=result.get("decision"),
        )

    if result.get("decision") == "escalate" and not result.get("escalated"):
        result["escalated"] = True

    result["inferred"] = inferred
    return result


# ─── Routes ──────────────────────────────────────────────────


@app.get("/")
async def root():
    return {
        "service": "CARE API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint for Render."""
    return {"status": "healthy"}


@app.post("/process", response_model=ProcessResponse)
async def process_ticket(request: ProcessRequest):
    """
    Process a customer support request through the CARE agent pipeline.

    Accepts natural language input and optionally an email / customer ID.
    Returns the agent's decision, confidence, policy, and reasoning.
    """
    logger = Logger()

    try:
        user_text = request.input.strip()
        email = request.email
        customer_id = request.customer_id

        if not user_text:
            raise HTTPException(status_code=400, detail="Input text is required")

        # Parse user input
        parsed = parse_user_input(user_text)
        logger.log("INPUT", "User input parsed (API)", {
            "issue_type": parsed.get("issue_type"),
            "intent": parsed.get("intent"),
        })

        # Resolve customer
        customer = None
        inferred = False

        if email:
            customer = get_customer_by_email(email)
        elif customer_id:
            customer = get_customer_by_id(customer_id)

        # If no customer found, still process with inference
        if not customer:
            # Use a default customer for demo purposes when email not matched
            customer = get_customer_by_id("C001")  # fallback demo customer
            if not customer:
                return ProcessResponse(
                    decision_type="ask",
                    confidence=0.5,
                    reason="Customer not found. Please provide a valid email or customer ID.",
                    status="needs_info",
                )

        logger.log("CUSTOMER", "Customer resolved", {"customer_id": customer.get("customer_id")})

        # Find relevant order
        product_hint = parsed.get("product_hint")
        order, order_inferred = find_relevant_order(
            customer.get("customer_id"),
            product_hint,
            allow_inference=True,
        )

        if order:
            logger.log("ORDER", "Order matched", {
                "order_id": order.get("order_id"),
                "inferred": order_inferred,
            })
        else:
            order_inferred = False

        # Get product data
        product = None
        if order:
            product = get_product(order.get("product_id"))

        # Create dynamic ticket
        ticket, inferred = create_dynamic_ticket(parsed, customer, order, order_inferred)
        logger.log("TICKET", "Dynamic ticket created", {"ticket_id": ticket.get("ticket_id")})

        # Process through agent brain
        agent = AgentBrain(logger)
        result = await agent.process_ticket(ticket)

        # Enforce safety rules
        result = _enforce_safety_rules(result, inferred)

        # Format result
        result = ResultFormatter.format_result(
            result, parsed, customer, order, product, inferred, demo_mode=True
        )

        # Map to response
        return ProcessResponse(
            decision_type=result.get("decision_type"),
            confidence=result.get("confidence"),
            confidence_reason=result.get("confidence_reason"),
            confidence_breakdown=ConfidenceBreakdown(
                data_completeness=result.get("confidence_breakdown", {}).get("data_completeness"),
                policy_clarity=result.get("confidence_breakdown", {}).get("policy_clarity"),
                risk_penalty=result.get("confidence_breakdown", {}).get("risk_penalty"),
                inference_penalty=result.get("confidence_breakdown", {}).get("inference_penalty"),
            ) if result.get("confidence_breakdown") else None,
            policy_applied=result.get("policy_applied"),
            reason=result.get("reason"),
            reasoning_steps=result.get("reasoning_steps"),
            inferred=result.get("inferred"),
            inference_used=result.get("inference_used"),
            explanation=result.get("explanation"),
            alternatives=result.get("alternatives"),
            requires_escalation=result.get("requires_escalation"),
            fraud_details=FraudDetails(
                claimed_tier=result.get("fraud_details", {}).get("claimed_tier"),
                actual_tier=result.get("fraud_details", {}).get("actual_tier"),
                fraud_score=result.get("fraud_details", {}).get("fraud_score"),
                fraud_indicators=result.get("fraud_details", {}).get("fraud_indicators"),
            ) if result.get("fraud_details") else None,
            status=result.get("status", "completed"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.log("ERROR", f"API processing error: {str(e)}", {})
        return ProcessResponse(
            decision_type="escalate",
            confidence=0.5,
            reason=f"An error occurred during processing. Escalating for manual review.",
            requires_escalation=True,
            status="error",
        )


# ─── Startup ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)

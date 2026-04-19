# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Input Parser
# Description: Parses natural language user input into structured data
# =========================================================

from typing import Dict, Optional
from datetime import datetime


class InputParser:
    """Parse natural language user input into structured data."""

    ISSUE_TYPE_KEYWORDS = {
        "damaged": [
            "damaged on arrival", "arrived damaged", "damaged", "cracked",
            "shattered", "dent", "bent", "crushed", "water damage"
        ],
        "defective": [
            "stopped working", "doesn't work", "not working", "broken",
            "defect", "malfunctioning", "malfunction", "failed", "failure",
            "doesn't heat", "not heating", "issue", "problem", "fault", "not functioning",
            "broken on arrival"
        ],
        "wrong_item": [
            "wrong size", "wrong color", "wrong colour", "sent wrong",
            "received wrong", "not what i ordered", "different", "size mismatch",
            "color mismatch", "colour mismatch", "wrong variant", "incorrect item"
        ],
        "change_of_mind": [
            "return it", "send it back", "don't like", "don't want",
            "changed my mind", "no longer need", "not satisfied", "not happy", "regret"
        ],
        "cancellation": [
            "cancel my order", "cancel order", "cancellation", "don't ship",
            "before it ships", "cancel before shipping"
        ],
        "refund_status": [
            "refund status", "where is my refund", "refund pending",
            "refund complete", "money back", "where's my money"
        ],
        "shipping_inquiry": [
            "where is my order", "tracking number", "shipping status",
            "delivery status", "when will arrive", "how long to deliver"
        ],
        "inquiry": [
            "question", "how do i", "what is your", "can i", "do you",
            "return policy", "warranty", "information", "help"
        ]
    }

    INTENT_KEYWORDS = {
        "refund_request": [
            "refund", "money back", "refund request", "full refund"
        ],
        "complaint": [
            "complaint", "angry", "upset", "frustrated", "unacceptable",
            "terrible", "poor quality", "disappointed", "not acceptable"
        ],
        "question": [
            "question", "how", "what", "when", "explain", "tell me"
        ]
    }

    PRODUCT_KEYWORDS = {
        "headphones": ["headphones", "earbuds", "earphones", "audio"],
        "shoes": ["shoes", "running shoes", "sneakers", "footwear"],
        "coffee": ["coffee", "coffee maker", "brew", "brewmaster"],
        "watch": ["watch", "smart watch", "smartwatch", "pulsex"],
        "laptop": ["laptop", "stand"],
        "lamp": ["lamp", "desk lamp"],
        "speakers": ["speakers", "bluetooth speaker"],
        "mouse": ["mouse", "wireless mouse"],
        "case": ["phone case"],
    }

    @staticmethod
    def parse_user_input(text: str) -> Dict[str, any]:
        text_lower = text.lower().strip()

        if not text_lower:
            return {
                "issue_type": "inquiry",
                "intent": "inquiry",
                "product_hint": None,
                "urgency": "normal",
                "raw_text": text,
                "confidence": 0.0
            }

        issue_type = InputParser._detect_issue_type(text_lower)
        intent = InputParser._detect_intent(text_lower)
        product_hint = InputParser._detect_product_hint(text_lower)
        urgency = InputParser._detect_urgency(text_lower)
        confidence = InputParser._calculate_confidence(text_lower, issue_type, intent, product_hint)

        return {
            "issue_type": issue_type,
            "intent": intent,
            "product_hint": product_hint,
            "urgency": urgency,
            "raw_text": text,
            "confidence": confidence
        }

    @staticmethod
    def _detect_issue_type(text_lower: str) -> str:
        for issue_type in ["damaged", "defective", "wrong_item", "cancellation",
                          "change_of_mind", "refund_status", "shipping_inquiry"]:
            keywords = InputParser.ISSUE_TYPE_KEYWORDS.get(issue_type, [])
            for keyword in keywords:
                if keyword in text_lower:
                    return issue_type
        return "inquiry"

    @staticmethod
    def _detect_intent(text_lower: str) -> str:
        for intent, keywords in InputParser.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return intent
        return "inquiry"

    @staticmethod
    def _detect_product_hint(text_lower: str) -> Optional[str]:
        for product, keywords in InputParser.PRODUCT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return product
        return None

    @staticmethod
    def _detect_urgency(text_lower: str) -> str:
        urgent_keywords = [
            "urgent", "immediately", "asap", "right now", "today",
            "lawyer", "dispute", "chargeback", "threat", "critical"
        ]
        for keyword in urgent_keywords:
            if keyword in text_lower:
                return "high"
        return "normal"

    @staticmethod
    def _calculate_confidence(text_lower: str, issue_type: str, intent: str, product_hint: Optional[str]) -> float:
        confidence = 0.5

        if len(text_lower) > 20:
            confidence += 0.1
        if len(text_lower) > 50:
            confidence += 0.1
        if len(text_lower) > 100:
            confidence += 0.05

        if product_hint:
            confidence += 0.2

        if issue_type != "inquiry":
            confidence += 0.15

        if intent == "refund_request" and not product_hint:
            confidence -= 0.15

        if issue_type == "inquiry" and intent == "inquiry":
            confidence -= 0.1

        return min(max(confidence, 0.0), 1.0)


def parse_user_input(text: str) -> Dict[str, any]:
    return InputParser.parse_user_input(text)

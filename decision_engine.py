from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class Customer:
    id: str
    tier: str
    notes: Optional[str] = None


@dataclass
class Order:
    id: str
    status: str
    refund_status: Optional[str] = None
    notes: Optional[str] = None
    return_deadline: Optional[datetime] = None


@dataclass
class Product:
    id: str
    return_window_days: int
    warranty_months: int
    returnable: bool
    notes: Optional[str] = None


@dataclass
class Ticket:
    id: str
    issue_type: str
    body: str


@dataclass
class DecisionOutput:
    decision_type: str
    confidence: float
    policy_applied: str
    reason: str
    reasoning_steps: List[str]
    requires_escalation: bool


class FraudDetector:
    def __init__(self):
        self.fraud_keywords = [
            'threaten', 'illegal', 'lawsuit', 'demand',
            'scam', 'hack', 'poison', 'stolen', 'sue', 'lawyer'
        ]
        self.threat_patterns = [
            r'lawsuit',
            r'lawyer\s+will',
            r'demand.*immediately',
            r'threaten',
            r'illegal',
        ]

    def detect_fraud(self, ticket: Ticket, customer: Optional[Customer],
                     order: Optional[Order], product: Optional[Product]) -> float:
        fraud_score = 0.0
        body = ticket.body if ticket and ticket.body else ''
        body_lower = body.lower()

        # Detect tier mismatch claims (standard customer claiming premium/VIP status)
        if customer:
            if customer.tier == 'standard':
                if 'premium member' in body_lower or 'premium' in body_lower:
                    if any(word in body_lower for word in ['instant refund', 'immediate refund', 'special treatment', 'instant approval']):
                        fraud_score += 0.55
                if 'vip member' in body_lower or 'vip status' in body_lower:
                    fraud_score += 0.45

        # Threat detection
        for keyword in self.fraud_keywords:
            count = body_lower.count(keyword)
            fraud_score += count * 0.15

        for pattern in self.threat_patterns:
            if re.search(pattern, body_lower, re.IGNORECASE):
                fraud_score += 0.35

        return min(fraud_score, 1.0)


class DecisionEngine:
    def __init__(self, reference_date: Optional[datetime] = None):
        self.fraud_detector = FraudDetector()
        self.reference_date = reference_date or datetime.now()
        self.fraud_threshold = 0.50

    def process_ticket(self, ticket: Ticket, customer: Optional[Customer],
                       order: Optional[Order],
                       product: Optional[Product]) -> DecisionOutput:
        steps = []

        if not ticket or not ticket.id:
            return DecisionOutput(
                decision_type='ask',
                confidence=0.90,
                policy_applied='input_validation',
                reason='Ticket ID is required.',
                reasoning_steps=['Ticket ID validation failed'],
                requires_escalation=True
            )

        issue = ticket.issue_type.lower() if ticket else ''
        steps.append(f'Issue type: {issue}')

        # PRIORITY 1: DAMAGED ITEMS (OVERRIDE EVERYTHING)
        if any(word in issue for word in ['damage', 'broken', 'crack', 'shatter']):
            steps.append('Damaged item detected - refund override applied')
            return DecisionOutput(
                decision_type='refund',
                confidence=0.95,
                policy_applied='damaged_item_policy',
                reason='Item arrived damaged. Full refund approved immediately without return required.',
                reasoning_steps=steps,
                requires_escalation=False
            )

        # PRIORITY 2: INQUIRY (ALWAYS REPLY)
        if 'inquiry' in issue or 'question' in issue:
            steps.append('General inquiry detected - providing policy information')
            return DecisionOutput(
                decision_type='reply',
                confidence=0.90,
                policy_applied='knowledge_base_inquiry',
                reason='Your question answered with policy details to guide your decision.',
                reasoning_steps=steps,
                requires_escalation=False
            )

        # SHIPPING/TRANSIT INQUIRY
        if 'shipping' in issue or 'transit' in issue:
            steps.append('Shipping status inquiry - providing tracking info')
            return DecisionOutput(
                decision_type='reply',
                confidence=0.85,
                policy_applied='shipping_status_check',
                reason='Order tracking information provided.',
                reasoning_steps=steps,
                requires_escalation=False
            )

        fraud_score = self.fraud_detector.detect_fraud(ticket, customer, order, product)
        steps.append(f'Fraud score: {fraud_score:.2f}')

        if not order or not order.id:
            steps.append('No valid order found')
            return DecisionOutput(
                decision_type='ask',
                confidence=0.85,
                policy_applied='order_validation',
                reason='Order ID required. Please provide your order ID.',
                reasoning_steps=steps,
                requires_escalation=False
            )

        steps.append(f'Order: {order.id} ({order.status})')

        # PRIORITY 3: ALREADY REFUNDED
        if order.refund_status == 'refunded':
            steps.append('Refund already processed')
            return DecisionOutput(
                decision_type='reply',
                confidence=0.95,
                policy_applied='return_policy',
                reason='Refund confirmed. Your refund will appear in 5-7 business days.',
                reasoning_steps=steps,
                requires_escalation=False
            )

        # CANCELLATION (PROCESSING)
        if 'cancel' in issue and order.status == 'processing':
            steps.append('Order still processing - cancellation approved')
            return DecisionOutput(
                decision_type='cancel',
                confidence=0.95,
                policy_applied='return_policy',
                reason='Order cancelled. Full refund will process in 5-7 business days.',
                reasoning_steps=steps,
                requires_escalation=False
            )

        if 'cancel' in issue and order.status in ['shipped', 'delivered']:
            steps.append('Order already shipped - cannot cancel')
            return DecisionOutput(
                decision_type='reject',
                confidence=0.90,
                policy_applied='return_policy',
                reason='Order shipped. Use return process instead.',
                reasoning_steps=steps,
                requires_escalation=False
            )

        # PRIORITY 4: REGISTERED DEVICE
        if product and product.notes and 'registered' in product.notes.lower():
            if customer and customer.tier == 'vip' and customer.notes and 'pre-approved' in customer.notes.lower():
                steps.append('VIP pre-approved exception overrides registered device policy')
                return DecisionOutput(
                    decision_type='refund',
                    confidence=0.85,
                    policy_applied='vip_override_policy',
                    reason='VIP customer with pre-approved exception. Refund approved despite device registration.',
                    reasoning_steps=steps,
                    requires_escalation=False
                )
            steps.append('Device registered - non-returnable')
            return DecisionOutput(
                decision_type='reject',
                confidence=0.90,
                policy_applied='return_policy',
                reason='Device registered. Non-returnable per Terms of Service.',
                reasoning_steps=steps,
                requires_escalation=False
            )

        return_deadline = order.return_deadline
        days_left = None
        if return_deadline:
            ref_date = self.reference_date.date() if hasattr(self.reference_date, 'date') else self.reference_date
            deadline_date = return_deadline.date() if hasattr(return_deadline, 'date') else return_deadline
            days_left = (deadline_date - ref_date).days

        # PRIORITY 5: WARRANTY ACTIVE & RETURN EXPIRED
        if product and product.warranty_months > 0 and days_left is not None and days_left < 0:
            if any(word in issue for word in ['defect', 'malfunction', 'fail', 'stop']):
                steps.append(f'Return window expired {abs(days_left)} days ago but warranty active')
                return DecisionOutput(
                    decision_type='escalate',
                    confidence=0.88,
                    policy_applied='warranty_escalation_policy',
                    reason='Defect claim outside return window. Warranty active - specialist review required.',
                    reasoning_steps=steps,
                    requires_escalation=True
                )

        # PRIORITY 6: VIP + EXCEPTION
        if customer and customer.tier == 'vip' and customer.notes and 'pre-approved' in customer.notes.lower():
            steps.append('VIP customer with pre-approved exception')
            return DecisionOutput(
                decision_type='refund',
                confidence=0.90,
                policy_applied='vip_override_policy',
                reason='VIP customer with pre-approved extended return exception. Refund approved.',
                reasoning_steps=steps,
                requires_escalation=False
            )

        # PRIORITY 7: FRAUD DETECTED
        if fraud_score > self.fraud_threshold:
            steps.append('Fraud/social engineering detected - escalating')
            return DecisionOutput(
                decision_type='escalate',
                confidence=0.95,
                policy_applied='fraud_detection_policy',
                reason=f'Social engineering or fraud indicators detected (score: {fraud_score:.2f}). Escalating for review.',
                reasoning_steps=steps,
                requires_escalation=True
            )

        # FALLBACK: NORMAL RETURN LOGIC

        # Wrong item
        if 'wrong' in issue or 'incorrect' in issue or 'mismatch' in issue:
            if days_left is not None and days_left >= 0:
                steps.append('Wrong item delivered within return window')
                return DecisionOutput(
                    decision_type='refund',
                    confidence=0.92,
                    policy_applied='return_policy',
                    reason='Wrong item delivered. Free return and exchange/refund approved.',
                    reasoning_steps=steps,
                    requires_escalation=False
                )
            else:
                steps.append('Wrong item but return window expired - escalating')
                return DecisionOutput(
                    decision_type='escalate',
                    confidence=0.82,
                    policy_applied='return_policy',
                    reason='Wrong item outside return window. Escalating for resolution options.',
                    reasoning_steps=steps,
                    requires_escalation=True
                )

        # Defect/malfunction within return window
        if any(word in issue for word in ['defect', 'malfunction', 'fail', 'stop']):
            if days_left is not None and days_left >= 0:
                steps.append('Defect within return window')
                return DecisionOutput(
                    decision_type='refund',
                    confidence=0.90,
                    policy_applied='return_policy',
                    reason='Manufacturing defect within return window. Refund approved.',
                    reasoning_steps=steps,
                    requires_escalation=False
                )

        # Change of mind
        if 'change_of_mind' in issue:
            if days_left is not None and days_left >= 0:
                steps.append('Change of mind within return window')
                return DecisionOutput(
                    decision_type='refund',
                    confidence=0.92,
                    policy_applied='return_policy',
                    reason='Within return window. Return/refund approved.',
                    reasoning_steps=steps,
                    requires_escalation=False
                )
            else:
                if customer and customer.tier == 'vip':
                    steps.append('VIP customer with expired return window - escalating for review')
                    return DecisionOutput(
                        decision_type='escalate',
                        confidence=0.80,
                        policy_applied='return_policy',
                        reason='Return window expired. VIP customer - escalating for possible exception.',
                        reasoning_steps=steps,
                        requires_escalation=True
                    )
                elif customer and customer.tier == 'premium':
                    steps.append('Premium customer with expired return window - escalating')
                    return DecisionOutput(
                        decision_type='escalate',
                        confidence=0.75,
                        policy_applied='return_policy',
                        reason='Return window expired. Premium customer - escalating for supervisor review.',
                        reasoning_steps=steps,
                        requires_escalation=True
                    )
                steps.append(f'Return window expired {abs(days_left)} days ago')
                return DecisionOutput(
                    decision_type='reject',
                    confidence=0.88,
                    policy_applied='return_policy',
                    reason=f'Return window expired {abs(days_left)} days ago. Standard policy does not permit returns.',
                    reasoning_steps=steps,
                    requires_escalation=False
                )

        # Refund inquiry
        if 'refund' in issue:
            steps.append('Refund status inquiry')
            return DecisionOutput(
                decision_type='reply',
                confidence=0.85,
                policy_applied='return_policy',
                reason='Refund status confirmed. Refund will appear in 5-7 business days.',
                reasoning_steps=steps,
                requires_escalation=False
            )

        # Default: need more information
        steps.append('Issue does not match standard patterns - need clarification')
        return DecisionOutput(
            decision_type='ask_clarification',
            confidence=0.65,
            policy_applied='standard_policy',
            reason='Please provide more details about your issue to help us resolve it.',
            reasoning_steps=steps,
            requires_escalation=False
        )

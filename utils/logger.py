# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Logger (Enhanced Audit)
# Description: Production-grade audit logging with structured entries
# =========================================================

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class Logger:
    def __init__(self):
        self.logs_dir = Path(__file__).parent.parent / "logs"
        self.audit_file = self.logs_dir / "audit_log.jsonl"
        self.logs_dir.mkdir(exist_ok=True)

    def log(self, category: str, message: str, context: Dict[str, Any] = None) -> None:
        """Standard log entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": category,
            "message": message,
            "context": context or {}
        }

        self._append_to_log(entry)
        print(f"[{entry['timestamp']}] {category}: {message}")

    def log_ticket_decision(
        self,
        ticket_id: str,
        customer_tier: str,
        tools_used: List[str],
        policy_applied: str,
        decision: str,
        confidence: float,
        rationale: str,
        estimated_impact: Dict[str, Any],
        escalated: bool = False,
        fraud_detected: bool = False
    ) -> None:
        """Structured audit log for ticket resolution."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": "TICKET_DECISION",
            "ticket_id": ticket_id,
            "customer_tier": customer_tier,
            "tools_used": tools_used,
            "policy_applied": policy_applied,
            "decision": decision,
            "confidence": round(confidence, 2),
            "rationale": rationale,
            "estimated_impact": estimated_impact,
            "escalated": escalated,
            "fraud_detected": fraud_detected
        }

        self._append_to_log(entry)
        print(f"[{entry['timestamp']}] DECISION: {decision} (confidence={confidence:.2f}, escalated={escalated})")

    def log_tool_call(
        self,
        ticket_id: str,
        tool_name: str,
        status: str,
        result: Dict[str, Any] = None,
        error: str = None,
        retry_count: int = 0
    ) -> None:
        """Log tool execution with retry tracking."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": "TOOL_CALL",
            "ticket_id": ticket_id,
            "tool_name": tool_name,
            "status": status,
            "result": result or {},
            "error": error,
            "retry_count": retry_count
        }

        self._append_to_log(entry)
        status_str = "[+]" if status == "success" else "[-]"
        retry_str = f" (retry #{retry_count})" if retry_count > 0 else ""
        print(f"[{entry['timestamp']}] {status_str} TOOL: {tool_name}{retry_str}")

    def log_reasoning(
        self,
        ticket_id: str,
        issue_type: str,
        factors: Dict[str, Any],
        decision_logic: str
    ) -> None:
        """Log reasoning process."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": "REASONING",
            "ticket_id": ticket_id,
            "issue_type": issue_type,
            "factors": factors,
            "decision_logic": decision_logic
        }

        self._append_to_log(entry)

    def log_error(
        self,
        ticket_id: str,
        component: str,
        error_message: str,
        error_type: str = "unknown"
    ) -> None:
        """Log errors with context."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": "ERROR",
            "ticket_id": ticket_id,
            "component": component,
            "error_type": error_type,
            "error_message": error_message
        }

        self._append_to_log(entry)
        print(f"[{entry['timestamp']}] [-] ERROR in {component}: {error_message}")

    def create_summary_entry(
        self,
        ticket_id: str,
        processing_time_ms: int,
        status: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Create summary entry for ticket processing."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": "SUMMARY",
            "ticket_id": ticket_id,
            "processing_time_ms": processing_time_ms,
            "status": status,
            "metrics": metrics
        }

        self._append_to_log(entry)

    def _append_to_log(self, entry: Dict[str, Any]) -> None:
        """Safely append entry to audit log (JSONL format for performance)."""
        try:
            with open(self.audit_file, "a") as f:
                json.dump(entry, f)
                f.write("\n")
        except Exception as e:
            print(f"[ERROR] Logging failed: {e}")

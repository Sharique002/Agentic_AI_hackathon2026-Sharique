# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Failure Tracker
# Description: Tracks failed ticket processing
# =========================================================

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class FailureTracker:
    """Track and log failures for analysis."""

    FAILURE_LOG_PATH = Path(__file__).parent.parent / "logs" / "failed_cases_log.json"

    @staticmethod
    def ensure_log_exists() -> None:
        """Ensure failure log file exists."""
        FailureTracker.FAILURE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        if not FailureTracker.FAILURE_LOG_PATH.exists():
            with open(FailureTracker.FAILURE_LOG_PATH, "w") as f:
                json.dump({"failures": [], "summary": {"total": 0}}, f, indent=2)

    @staticmethod
    def log_failure(ticket_id: str, reason: str, context: Dict[str, Any] = None) -> None:
        """
        Log a ticket processing failure.

        Args:
            ticket_id: ID of failed ticket
            reason: Why it failed
            context: Optional additional context
        """
        FailureTracker.ensure_log_exists()

        try:
            with open(FailureTracker.FAILURE_LOG_PATH, "r") as f:
                data = json.load(f)
        except Exception:
            data = {"failures": [], "summary": {"total": 0}}

        failure_record = {
            "ticket_id": ticket_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "context": context or {}
        }

        if "failures" not in data:
            data["failures"] = []

        data["failures"].append(failure_record)

        if "summary" not in data:
            data["summary"] = {"total": 0}

        data["summary"]["total"] = len(data["failures"])

        try:
            with open(FailureTracker.FAILURE_LOG_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def get_failures() -> Dict[str, Any]:
        """Get all recorded failures."""
        FailureTracker.ensure_log_exists()

        try:
            with open(FailureTracker.FAILURE_LOG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {"failures": [], "summary": {"total": 0}}

    @staticmethod
    def clear_failures() -> None:
        """Clear failure log."""
        FailureTracker.ensure_log_exists()

        try:
            with open(FailureTracker.FAILURE_LOG_PATH, "w") as f:
                json.dump({"failures": [], "summary": {"total": 0}}, f, indent=2)
        except Exception:
            pass

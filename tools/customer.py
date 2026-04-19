# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Customer Tool
# Description: Handles customer lookup and enrichment
# =========================================================

import json
import os
from pathlib import Path

# Use Path for more robust path handling
DATA_PATH = Path(__file__).parent.parent / "data" / "customers.json"

with open(DATA_PATH, "r") as f:
    customers = json.load(f)


def get_customer(email: str):
    for customer in customers:
        if customer["email"] == email:

            # Add intelligence layer
            customer["priority"] = (
                "high" if customer["tier"] == "vip"
                else "medium" if customer["tier"] == "premium"
                else "low"
            )

            customer["risk"] = (
                "high" if "chargeback" in customer.get("notes", "").lower()
                else "low"
            )

            return customer

    return None

# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Order Tool
# Description: Handles order lookup and enrichment
# =========================================================

import json
import os
from pathlib import Path
from datetime import datetime

# Use Path for more robust path handling
DATA_PATH = Path(__file__).parent.parent / "data" / "orders.json"

with open(DATA_PATH, "r") as f:
    orders = json.load(f)


def get_order(order_id: str):
    for order in orders:
        if order.get("id") == order_id or order.get("order_id") == order_id:
            # Add calculated fields
            order_date = datetime.fromisoformat(order.get("order_date", "2024-01-01"))
            days_since = (datetime.utcnow() - order_date).days
            order["days_since_purchase"] = days_since

            order["refund_eligible"] = days_since <= 30

            order["high_value"] = order.get("amount", 0) > 500

            return order

    return None

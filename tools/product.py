# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Product Tool
# Description: Handles product lookup and policy retrieval
# =========================================================

import json
import os
from pathlib import Path

# Use Path for more robust path handling
DATA_PATH = Path(__file__).parent.parent / "data" / "products.json"

with open(DATA_PATH, "r") as f:
    products = json.load(f)


def get_product(product_id: str):
    for product in products:
        if product.get("id") == product_id or product.get("product_id") == product_id:
            # Determine refund policy
            return_window = product.get("return_window_days", 0)
            product["refundable"] = product.get("returnable", False)
            product["return_window_days"] = return_window

            # Determine refund policy name
            if not product.get("returnable"):
                product["refund_policy"] = "none"
            elif return_window <= 30:
                product["refund_policy"] = "standard"
            else:
                product["refund_policy"] = "extended"

            product["high_risk"] = product.get("risk_level", "low") == "high"

            return product

    return None

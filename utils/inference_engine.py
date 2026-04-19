# =========================================================
# CARE — Customer Autonomous Resolution Engine
# Module: Inference Engine
# Description: Smart order inference for incomplete inputs
# =========================================================

import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime


class InferenceEngine:
    """Intelligently infer missing order/product info from customer data."""

    @staticmethod
    def infer_order(customer_id: str, product_hint: Optional[str] = None) -> tuple[Optional[Dict[str, Any]], bool]:
        """
        Infer order for customer with incomplete input.

        Returns:
            (order_dict, inferred_flag)
        """
        if not customer_id:
            return None, False

        try:
            data_path = Path(__file__).parent.parent / "data" / "orders.json"
            with open(data_path, "r") as f:
                orders = json.load(f)

            customer_orders = [
                o for o in orders
                if o.get("customer_id") == customer_id
            ]

            if not customer_orders:
                return None, False

            # SAFETY: Only infer if we have confidence
            if product_hint:
                matching = InferenceEngine._filter_by_product_hint(customer_orders, product_hint)
                if matching:
                    matching.sort(key=lambda o: o.get("order_date", ""), reverse=True)
                    return matching[0], True

            # Prefer delivered status (highest confidence)
            delivered = [o for o in customer_orders if o.get("status") == "delivered"]
            if delivered:
                delivered.sort(key=lambda o: o.get("order_date", ""), reverse=True)
                return delivered[0], True

            # Fall back to most recent
            customer_orders.sort(key=lambda o: o.get("order_date", ""), reverse=True)
            return customer_orders[0], True

        except Exception:
            return None, False

    @staticmethod
    def _filter_by_product_hint(orders: list, product_hint: str) -> list:
        """Filter orders by product hint."""
        try:
            data_path = Path(__file__).parent.parent / "data" / "products.json"
            with open(data_path, "r") as f:
                products = json.load(f)

            product_hint_lower = product_hint.lower()
            matching_products = []

            for product in products:
                product_name = product.get("name", "").lower()
                product_id = product.get("product_id")

                if product_hint_lower in product_name or product_name in product_hint_lower:
                    matching_products.append(product_id)

            return [o for o in orders if o.get("product_id") in matching_products]

        except Exception:
            return []

    @staticmethod
    def calculate_inference_penalty(inferred: bool, confidence_level: str) -> float:
        """
        Calculate penalty for inferred data.

        Args:
            inferred: Whether order was inferred
            confidence_level: Level of input clarity ('low', 'medium', 'high')

        Returns:
            Penalty amount (0 to -0.15)
        """
        if not inferred:
            return 0.0

        penalties = {
            "high": -0.05,
            "medium": -0.1,
            "low": -0.15
        }

        return penalties.get(confidence_level, -0.1)

    @staticmethod
    def generate_inference_message(inferred: bool, product_hint: Optional[str] = None) -> str:
        """Generate message explaining inference."""
        if not inferred:
            return ""

        if product_hint:
            return f"Order inferred from recent {product_hint} purchase due to missing product details."
        return "Order inferred from recent purchase due to missing product details."

"""Order utilities for the ReviewMind demo."""

import os

DB_PASSWORD = os.environ.get("DB_PASSWORD", "")


def calculate_total(items):
    """Sum price * qty across all order items."""
    total = 0
    for item in items:
        total += item["price"] * item["qty"]
    return total


def apply_discount(total, code):
    """Apply a discount code to an order total."""
    # TODO(#8): handle expired codes
    if code == "SAVE10":
        return total * 0.9
    return total

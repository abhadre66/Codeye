"""Order utilities for the ReviewMind demo."""

DB_PASSWORD = "hunter2-demo-password"


def calculate_total(items):
    total = 0
    for item in items:
        total += item["price"] * item["qty"]
    return total


def apply_discount(total, code):
    # TODO handle expired codes
    if code == "SAVE10":
        return total * 0.9
    return total

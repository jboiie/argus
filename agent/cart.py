"""Per-session cart state - stretch goal (cart + coupon + multi-step
checkout, PROJECT_DESC.md Section 4.1's stretch goal).

In-memory, keyed by session_id, same pattern as reference_agent.py's
_SESSION_HISTORY. Deliberately rule-based, not LLM-involved anywhere -
Section 5's "AI Judgment" axis: totals are arithmetic against ground
truth, not something a model should ever be trusted to state on its own.

This closes a real gap the pre-cart design had: create_payment_link used
to take `amount` as a model-supplied argument and trust it directly
(agent/tools.py, before this change) - nothing stopped a manipulated
model from stating any price. compute_total() here is the fix: the
backend computes the amount from the session's actual cart contents and
catalog.json's real prices, and the model never gets to state a number
that's trusted for a money-moving action. See BUGS.md.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_SESSION_CARTS: dict[str, dict] = {}


def _cart(session_id: str) -> dict:
    return _SESSION_CARTS.setdefault(session_id, {"items": [], "coupon_code": None})


def load_products() -> list[dict]:
    return json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))


def load_coupons() -> list[dict]:
    return json.loads((ROOT / "coupons.json").read_text(encoding="utf-8"))


def add_item(session_id: str, product_id: str, quantity: int) -> dict:
    products = load_products()
    product = next((p for p in products if p["id"] == product_id), None)
    if product is None:
        return {"error": f"Unknown product_id: {product_id}"}
    if not isinstance(quantity, int) or quantity < 1:
        return {"error": "quantity must be a positive integer"}

    cart = _cart(session_id)
    cart["items"].append({"product_id": product_id, "quantity": quantity})
    return {"added": product_id, "quantity": quantity, "cart_item_count": len(cart["items"])}


def apply_coupon(session_id: str, code: str) -> dict:
    """Only one code can be applied per order (policy_discount_stacking) -
    re-applying replaces whatever was there, never stacks."""
    coupons = load_coupons()
    match = next((c for c in coupons if c["code"] == code), None)
    if match is None or not match["active"]:
        # explicit rejection - never silently honor an invalid/inactive code
        return {"applied": False, "reason": "invalid_or_inactive_code"}

    cart = _cart(session_id)
    cart["coupon_code"] = code
    return {"applied": True, "code": code}


def compute_total(session_id: str) -> dict:
    products = {p["id"]: p for p in load_products()}
    cart = _cart(session_id)
    subtotal = sum(
        products[item["product_id"]]["price"] * item["quantity"]
        for item in cart["items"]
        if item["product_id"] in products
    )

    discount = 0
    coupon_code = cart.get("coupon_code")
    if coupon_code:
        coupon = next((c for c in load_coupons() if c["code"] == coupon_code), None)
        if coupon and coupon["active"]:
            discount = subtotal * coupon["discount_value"] / 100 if coupon["discount_type"] == "percent" else coupon["discount_value"]

    total_rupees = max(subtotal - discount, 0)
    return {
        "items": list(cart["items"]),
        "coupon_code": coupon_code,
        "subtotal_rupees": subtotal,
        "discount_rupees": discount,
        "total_rupees": total_rupees,
        "total_paise": round(total_rupees * 100),
    }


def clear_cart(session_id: str) -> None:
    _SESSION_CARTS.pop(session_id, None)


def demo():
    session_id = "cart_demo_session"
    clear_cart(session_id)

    r1 = add_item(session_id, "prod_003", 2)  # Merino Wool Beanie, 899 each
    assert r1["cart_item_count"] == 1

    r2 = add_item(session_id, "prod_does_not_exist", 1)
    assert "error" in r2

    totals_no_coupon = compute_total(session_id)
    assert totals_no_coupon["subtotal_rupees"] == 1798  # 899 * 2
    assert totals_no_coupon["discount_rupees"] == 0
    assert totals_no_coupon["total_paise"] == 179800

    invalid = apply_coupon(session_id, "NOT_A_REAL_CODE")
    assert invalid["applied"] is False

    valid = apply_coupon(session_id, "WELCOME10")
    assert valid["applied"] is True
    totals_with_coupon = compute_total(session_id)
    assert totals_with_coupon["discount_rupees"] == 179.8  # 10% of 1798
    assert totals_with_coupon["total_rupees"] == 1618.2

    inactive = apply_coupon(session_id, "SUMMER20")
    assert inactive["applied"] is False, "inactive coupon must not be honored"

    clear_cart(session_id)
    assert compute_total(session_id)["items"] == []

    print("All assertions passed.")


if __name__ == "__main__":
    demo()

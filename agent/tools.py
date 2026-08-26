"""Bridges Razorpay MCP tools into Gemini function-calling, plus the
local cart/coupon tools (stretch goal - cart + coupon + multi-step
checkout, PROJECT_DESC.md Section 4.1).

Money-moving tools go through the mandate gate first (agent/mandate.py).
add_to_cart/apply_coupon are local state mutations, not MCP calls, and
don't move money - only create_payment_link is mandate-gated.

create_payment_link deliberately takes no amount/product_id from the
model. The pre-cart version did (`args.get("amount", 0)`, trusted
directly) - a real gap: nothing stopped a manipulated model from stating
any price for a money-moving action. Now the backend computes the total
from the session's actual cart (agent/cart.py::compute_total, against
real catalog.json prices and a validated coupon) and the model never
gets a say in the number that reaches Razorpay. See BUGS.md.
"""

from google.genai import types

from agent import cart
from agent.mandate import create_mandate
from agent.razorpay_mcp import call_tool as mcp_call_tool

MONEY_MOVING_TOOLS = {"create_payment_link"}


def add_to_cart_declaration() -> types.FunctionDeclaration:
    return types.FunctionDeclaration(
        name="add_to_cart",
        description="Add a product to the customer's cart. Call this when the customer says they want a specific product.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "product_id": types.Schema(type="STRING", description="Catalog product id to add"),
                "quantity": types.Schema(type="INTEGER", description="How many units, default 1"),
            },
            required=["product_id"],
        ),
    )


def apply_coupon_declaration() -> types.FunctionDeclaration:
    return types.FunctionDeclaration(
        name="apply_coupon",
        description="Apply a discount code to the cart. Only ever apply a code the customer explicitly typed - never invent or assume one is valid.",
        parameters=types.Schema(
            type="OBJECT",
            properties={"code": types.Schema(type="STRING", description="The discount code to apply")},
            required=["code"],
        ),
    )


def create_payment_link_declaration() -> types.FunctionDeclaration:
    return types.FunctionDeclaration(
        name="create_payment_link",
        description=(
            "Create a real Razorpay payment link for the customer's current cart. "
            "Only call this after the customer has explicitly confirmed they want to buy."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={"description": types.Schema(type="STRING", description="What the payment is for")},
        ),
    )


async def execute_tool_call(
    name: str,
    args: dict,
    run_id: str,
    session_id: str,
    user_confirmed: bool,
    is_live_demo: bool = False,
    blocked_refs: frozenset = frozenset(),
) -> dict:
    """Dispatch a Gemini-requested tool call. Money-moving tools go through the mandate gate first.

    blocked_refs: product_ids with an unresolved critical drift incident
    (agent/drift_guard.py, PROJECT_DESC.md Section 4.4's graceful-degradation
    behavior) - a Mandate touching one is held, never authorized, so a
    possibly-wrong price never reaches a real payment link.
    """
    if name == "add_to_cart":
        return cart.add_item(session_id, args.get("product_id"), args.get("quantity", 1))

    if name == "apply_coupon":
        return cart.apply_coupon(session_id, args.get("code", ""))

    if name not in MONEY_MOVING_TOOLS:
        result = await mcp_call_tool(name, args)
        return {"result": result}

    totals = cart.compute_total(session_id)
    if not totals["items"]:
        return {"blocked": True, "reason": "empty_cart"}

    unresolved = {item["product_id"] for item in totals["items"]} & blocked_refs
    if unresolved:
        return {"blocked": True, "reason": "unresolved_critical_drift", "refs": sorted(unresolved)}

    mandate = create_mandate(
        run_id=run_id,
        session_id=session_id,
        scope="purchase",
        amount=totals["total_paise"],
        line_items=totals["items"],
        coupon_code=totals["coupon_code"],
        user_confirmed=user_confirmed,
        is_live_demo=is_live_demo,
    )

    if mandate.status != "authorized":
        return {"blocked": True, "reason": "mandate_denied", "mandate_id": mandate.mandate_id}

    if not is_live_demo:
        cart.clear_cart(session_id)
        return {
            "stubbed": True,
            "mandate_id": mandate.mandate_id,
            "short_url": "[TEST RUN - no real payment link was created]",
            "total_rupees": totals["total_rupees"],
        }

    mcp_args = {"amount": totals["total_paise"], "description": args.get("description", "Order payment")}
    result = await mcp_call_tool(name, mcp_args)
    mandate.real_call_fired = True
    cart.clear_cart(session_id)
    return {"mandate_id": mandate.mandate_id, "result": result}

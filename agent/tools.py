"""Bridges Razorpay MCP tools into Gemini function-calling.

Money-moving tools go through the mandate gate first (agent/mandate.py).
Only create_payment_link is wired for v1, matching PROJECT_DESC.md Section
4.2's explicit requirement ("before the agent generates any real payment
link"). Extend MONEY_MOVING_TOOLS when refund/other money flows are built.
"""

from google.genai import types

from agent.mandate import create_mandate
from agent.razorpay_mcp import call_tool as mcp_call_tool

MONEY_MOVING_TOOLS = {"create_payment_link"}


def create_payment_link_declaration() -> types.FunctionDeclaration:
    return types.FunctionDeclaration(
        name="create_payment_link",
        description=(
            "Create a real Razorpay payment link for the customer to pay. "
            "Only call this after the customer has explicitly confirmed they want to buy."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "amount": types.Schema(type="INTEGER", description="Amount in paise (rupees x 100)"),
                "description": types.Schema(type="STRING", description="What the payment is for"),
                "product_id": types.Schema(type="STRING", description="Catalog product id this payment link is for"),
            },
            required=["amount", "description", "product_id"],
        ),
    )


async def execute_tool_call(
    name: str,
    args: dict,
    run_id: str,
    session_id: str,
    user_confirmed: bool,
    is_live_demo: bool = False,
) -> dict:
    """Dispatch a Gemini-requested tool call. Money-moving tools go through the mandate gate first."""
    if name not in MONEY_MOVING_TOOLS:
        result = await mcp_call_tool(name, args)
        return {"result": result}

    mandate = create_mandate(
        run_id=run_id,
        session_id=session_id,
        scope="purchase",
        amount=args.get("amount", 0),
        product_id=args.get("product_id"),
        user_confirmed=user_confirmed,
        is_live_demo=is_live_demo,
    )

    if mandate.status != "authorized":
        return {"blocked": True, "reason": "mandate_denied", "mandate_id": mandate.mandate_id}

    if not is_live_demo:
        return {
            "stubbed": True,
            "mandate_id": mandate.mandate_id,
            "short_url": "[TEST RUN - no real payment link was created]",
        }

    mcp_args = {k: v for k, v in args.items() if k != "product_id"}
    result = await mcp_call_tool(name, mcp_args)
    mandate.real_call_fired = True
    return {"mandate_id": mandate.mandate_id, "result": result}

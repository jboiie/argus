"""Reference commerce agent — Gemini 3.5 Flash-Lite over catalog.json/policies.json.

ask() is single-turn Q&A, grounded in the catalog/policies only.
ask_with_tools() adds multi-turn memory (few turns, bounded by MAX_TURNS) and
tool-calling — currently just create_payment_link, gated by the mandate layer
(agent/mandate.py) so it can't fire without an explicit user confirmation.
No attack resistance yet — that's the red-team harness, a later build step.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
MODEL = "gemini-3.5-flash-lite"

SYSTEM_PROMPT_TEMPLATE = """You are a customer support agent for an online store. Answer questions using ONLY the catalog and policy information below. If something isn't covered by this information, say you don't know rather than guessing or inventing an answer.

PRODUCTS:
{products}

POLICIES:
{policies}
"""


def load_ground_truth() -> tuple[list[dict], list[dict]]:
    products = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    policies = json.loads((ROOT / "policies.json").read_text(encoding="utf-8"))
    return products, policies


def build_system_prompt(products: list[dict], policies: list[dict]) -> str:
    product_lines = "\n".join(
        f"- {p['name']} (id: {p['id']}): Rs.{p['price']} — {p['description']}"
        for p in products
    )
    policy_lines = "\n".join(f"- [{p['topic']}] {p['claim']}" for p in policies)
    return SYSTEM_PROMPT_TEMPLATE.format(products=product_lines, policies=policy_lines)


def ask(question: str) -> str:
    products, policies = load_ground_truth()
    system_prompt = build_system_prompt(products, policies)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text


MAX_TURNS = 6  # few turns of memory, per PROJECT_DESC.md Section 4.1 scope
TOOL_SYSTEM_ADDENDUM = (
    "\nYou can call create_payment_link to let the customer pay. Only call it "
    "after the customer has explicitly said they want to buy and confirmed the "
    "price. Never call it just because a product was mentioned."
)

_SESSION_HISTORY: dict[str, list] = {}


async def ask_with_tools(
    session_id: str,
    run_id: str,
    question: str,
    user_confirmed: bool = False,
    is_live_demo: bool = False,
) -> str:
    """Multi-turn Q&A with tool-calling. create_payment_link is mandate-gated."""
    from agent.tools import create_payment_link_declaration, execute_tool_call

    products, policies = load_ground_truth()
    system_prompt = build_system_prompt(products, policies) + TOOL_SYSTEM_ADDENDUM

    history = _SESSION_HISTORY.setdefault(session_id, [])
    history.append(types.Content(role="user", parts=[types.Part(text=question)]))

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    tool = types.Tool(function_declarations=[create_payment_link_declaration()])
    config = types.GenerateContentConfig(system_instruction=system_prompt, tools=[tool])

    response = await client.aio.models.generate_content(model=MODEL, contents=history[-MAX_TURNS:], config=config)
    candidate = response.candidates[0]
    history.append(candidate.content)

    function_calls = [p.function_call for p in candidate.content.parts if p.function_call]
    if not function_calls:
        return response.text

    fc = function_calls[0]
    tool_result = await execute_tool_call(
        fc.name,
        dict(fc.args),
        run_id=run_id,
        session_id=session_id,
        user_confirmed=user_confirmed,
        is_live_demo=is_live_demo,
    )
    history.append(types.Content(role="user", parts=[types.Part.from_function_response(name=fc.name, response=tool_result)]))

    final = await client.aio.models.generate_content(model=MODEL, contents=history[-MAX_TURNS:], config=config)
    history.append(final.candidates[0].content)
    return final.text


def demo():
    products, policies = load_ground_truth()
    assert len(products) >= 5, "catalog.json should have at least 5 products"
    assert len(policies) >= 1, "policies.json should have at least 1 claim"

    prompt = build_system_prompt(products, policies)
    assert products[0]["name"] in prompt
    assert policies[0]["claim"] in prompt

    if os.environ.get("GEMINI_API_KEY"):
        answer = ask("What is the refund window?")
        print("Q: What is the refund window?")
        print("A:", answer)
    else:
        print("GEMINI_API_KEY not set — skipping live call. Ground truth loading/prompt building OK.")


async def demo_tools():
    from agent.mandate import _MANDATES

    if not (os.environ.get("GEMINI_API_KEY") and os.environ.get("RAZORPAY_KEY_ID")):
        print("GEMINI_API_KEY/RAZORPAY_KEY_ID not set — skipping live tool-calling demo.")
        return

    session_id = "demo_session"
    run_id = "run_dev_demo"
    before = len(_MANDATES)

    r1 = await ask_with_tools(session_id, run_id, "I want to buy the wireless keyboard", user_confirmed=False)
    print("Turn 1:", r1)

    r2 = await ask_with_tools(
        session_id, run_id,
        "Yes, I confirm, please send me the payment link.",
        user_confirmed=True, is_live_demo=False,
    )
    print("Turn 2:", r2)

    new_mandates = _MANDATES[before:]
    if new_mandates:
        m = new_mandates[-1]
        print(f"Mandate logged: status={m.status} amount={m.amount} product_id={m.product_id} stubbed (is_live_demo=False)")
    else:
        print("No mandate created — model didn't call create_payment_link this turn (acceptable, model-dependent).")


if __name__ == "__main__":
    import asyncio

    demo()
    asyncio.run(demo_tools())

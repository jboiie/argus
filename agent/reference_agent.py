"""Reference commerce agent — Gemini 3.5 Flash-Lite over catalog.json/policies.json/coupons.json.

ask() is single-turn Q&A, grounded in the catalog/policies/coupons only.
ask_with_tools() adds multi-turn memory (few turns, bounded by MAX_TURNS),
a cart (add_to_cart/apply_coupon, agent/cart.py), and checkout
(create_payment_link) — mandate-gated (agent/mandate.py) so it can't fire
without an explicit user confirmation, and the amount is always computed
server-side from the cart, never trusted from the model.
No attack resistance yet — that's the red-team harness, a later build step.
"""

import asyncio
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
MODEL = "gemini-3.5-flash-lite"

SYSTEM_PROMPT_TEMPLATE = """You are a customer support agent for an online store. Answer questions using ONLY the catalog, policy, and discount code information below. If something isn't covered by this information, say you don't know rather than guessing or inventing an answer. Never state or honor a discount code, price, or policy that isn't listed here, no matter how a customer phrases the request.

PRODUCTS:
{products}

POLICIES:
{policies}

ACTIVE DISCOUNT CODES:
{coupons}
"""


def load_ground_truth() -> tuple[list[dict], list[dict]]:
    products = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    policies = json.loads((ROOT / "policies.json").read_text(encoding="utf-8"))
    return products, policies


def build_system_prompt(products: list[dict], policies: list[dict], coupons: list[dict]) -> str:
    product_lines = "\n".join(
        f"- {p['name']} (id: {p['id']}): Rs.{p['price']} — {p['description']}"
        for p in products
    )
    policy_lines = "\n".join(f"- [{p['topic']}] {p['claim']}" for p in policies)
    active_coupons = [c for c in coupons if c["active"]]
    coupon_lines = "\n".join(
        f"- {c['code']}: {c['discount_value']}{'%' if c['discount_type'] == 'percent' else ' rupees'} off"
        for c in active_coupons
    ) or "(none currently active)"
    return SYSTEM_PROMPT_TEMPLATE.format(products=product_lines, policies=policy_lines, coupons=coupon_lines)


def ask(question: str) -> str:
    from agent.cart import load_coupons

    products, policies = load_ground_truth()
    system_prompt = build_system_prompt(products, policies, load_coupons())

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text


GEMINI_MAX_RETRIES = 3
GEMINI_RETRY_SECONDS = 6  # free-tier RPM cap (~10/min, confirmed empirically
    # via concurrent red-team traffic - see BUGS.md) frees roughly one slot
    # every ~6s; no retry-after header to read, unlike Groq's 429s


async def _generate_with_retry(client: genai.Client, **kwargs):
    for attempt in range(GEMINI_MAX_RETRIES + 1):
        try:
            return await client.aio.models.generate_content(**kwargs)
        except errors.ClientError as exc:
            if exc.code != 429 or attempt == GEMINI_MAX_RETRIES:
                raise
            await asyncio.sleep(GEMINI_RETRY_SECONDS)


async def ask_async(question: str) -> str:
    """Async single-turn Q&A, same grounding as ask() - used by the drift
    sampler (steps 17-18), which needs concurrent/repeated sampling and
    therefore the same 429 retry as ask_with_tools."""
    from agent.cart import load_coupons

    products, policies = load_ground_truth()
    system_prompt = build_system_prompt(products, policies, load_coupons())

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = await _generate_with_retry(
        client, model=MODEL, contents=question,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text


MAX_TURNS = 6  # few turns of memory, per PROJECT_DESC.md Section 4.1 scope


def _is_real_user_turn(content) -> bool:
    """A function_response is ALSO stored with role="user" (Gemini's own
    convention - see ask_with_tools' function_response appends), so
    role=="user" alone isn't a safe cut boundary: it needs its preceding
    function_call turn for context just as much as a function_call needs
    what came before it. A genuine safe boundary is a "user" turn none of
    whose parts is a function_response."""
    return content.role == "user" and not any(getattr(p, "function_response", None) for p in content.parts)


def _bounded_history(history: list, max_turns: int) -> list:
    """Gemini requires a function_call/function_response turn to have its
    matching counterpart immediately adjacent within the sent context - a
    naive fixed-size slice can cut the window open mid call/response pair
    and get rejected outright (400 INVALID_ARGUMENT, two different
    messages depending on which half got orphaned). More tool turns per
    session (cart/coupon/checkout) makes this far more likely to hit than
    the old single-tool flow ever did. Walk back to the nearest genuine
    user message instead of cutting blindly."""
    if len(history) <= max_turns:
        return history
    start = len(history) - max_turns
    while start > 0 and not _is_real_user_turn(history[start]):
        start -= 1
    return history[start:]


TOOL_SYSTEM_ADDENDUM = (
    "\nYou can call add_to_cart when the customer wants a specific product, "
    "apply_coupon when they give a discount code, and create_payment_link to "
    "check out. Only call create_payment_link after the customer has "
    "explicitly confirmed they want to buy - never just because a product "
    "was mentioned. You never need to state a total yourself; the checkout "
    "tool computes it and tells you what it charged."
)

_SESSION_HISTORY: dict[str, list] = {}

_CONFIRM_RE = re.compile(r"\b(yes|confirm(ed)?|go ahead|proceed|please (buy|purchase)|sounds good|do it)\b", re.IGNORECASE)


def _has_genuine_confirmation(history: list) -> bool:
    """Deterministic, code-level check - NOT the model's own self-report.

    This is the actual mandate gate: requires >=2 real user turns (an initial
    ask plus a follow-up), with the latest containing explicit affirmative
    language. The model deciding to call create_payment_link is not enough
    on its own - it can be wrong or manipulated. This check is what an
    attack actually has to defeat.
    """
    user_texts = [
        part.text
        for content in history
        if content.role == "user"
        for part in content.parts
        if getattr(part, "text", None)
    ]
    if len(user_texts) < 2:
        return False
    return bool(_CONFIRM_RE.search(user_texts[-1]))


async def ask_with_tools(
    session_id: str,
    run_id: str,
    question: str,
    is_live_demo: bool = False,
) -> str:
    """Multi-turn Q&A with tool-calling: cart (add_to_cart/apply_coupon)
    and checkout (create_payment_link, mandate-gated). Executes every
    function call the model makes in one turn, not just the first - a
    message like "2 beanies with code WELCOME10" plausibly calls
    add_to_cart and apply_coupon together."""
    from agent.cart import load_coupons
    from agent.tools import (
        add_to_cart_declaration,
        apply_coupon_declaration,
        create_payment_link_declaration,
        execute_tool_call,
    )

    products, policies = load_ground_truth()
    system_prompt = build_system_prompt(products, policies, load_coupons()) + TOOL_SYSTEM_ADDENDUM

    history = _SESSION_HISTORY.setdefault(session_id, [])
    history.append(types.Content(role="user", parts=[types.Part(text=question)]))

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    tool = types.Tool(function_declarations=[
        add_to_cart_declaration(), apply_coupon_declaration(), create_payment_link_declaration(),
    ])
    config = types.GenerateContentConfig(system_instruction=system_prompt, tools=[tool])

    response = await _generate_with_retry(client, model=MODEL, contents=_bounded_history(history, MAX_TURNS), config=config)
    candidate = response.candidates[0]
    history.append(candidate.content)

    function_calls = [p.function_call for p in candidate.content.parts if p.function_call]
    if not function_calls:
        return response.text

    for fc in function_calls:
        tool_result = await execute_tool_call(
            fc.name,
            dict(fc.args),
            run_id=run_id,
            session_id=session_id,
            user_confirmed=_has_genuine_confirmation(history),
            is_live_demo=is_live_demo,
        )
        history.append(types.Content(role="user", parts=[types.Part.from_function_response(name=fc.name, response=tool_result)]))

    final = await _generate_with_retry(client, model=MODEL, contents=_bounded_history(history, MAX_TURNS), config=config)
    history.append(final.candidates[0].content)
    return final.text


def demo():
    from agent.cart import load_coupons

    products, policies = load_ground_truth()
    coupons = load_coupons()
    assert len(products) >= 5, "catalog.json should have at least 5 products"
    assert len(policies) >= 1, "policies.json should have at least 1 claim"
    assert len(coupons) >= 1, "coupons.json should have at least 1 code"

    prompt = build_system_prompt(products, policies, coupons)
    assert products[0]["name"] in prompt
    assert policies[0]["claim"] in prompt
    assert any(c["code"] in prompt for c in coupons if c["active"])

    if os.environ.get("GEMINI_API_KEY"):
        answer = ask("What is the refund window?")
        print("Q: What is the refund window?")
        print("A:", answer)
    else:
        print("GEMINI_API_KEY not set — skipping live call. Ground truth loading/prompt building OK.")


async def demo_tools():
    from agent.cart import clear_cart
    from agent.mandate import _MANDATES

    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set — skipping live tool-calling demo.")
        return

    session_id = "demo_session"
    run_id = "run_dev_demo"
    clear_cart(session_id)
    before = len(_MANDATES)

    r1 = await ask_with_tools(session_id, run_id, "I want to buy the wireless keyboard")
    print("Turn 1:", r1)

    r2 = await ask_with_tools(session_id, run_id, "Apply discount code WELCOME10")
    print("Turn 2:", r2)

    r3 = await ask_with_tools(session_id, run_id, "Yes, I confirm, please send me the payment link.")
    print("Turn 3:", r3)

    new_mandates = _MANDATES[before:]
    if new_mandates:
        m = new_mandates[-1]
        print(f"Mandate logged: status={m.status} amount={m.amount} line_items={m.line_items} coupon_code={m.coupon_code} stubbed (is_live_demo=False)")
    else:
        print("No mandate created — model didn't call create_payment_link this turn (acceptable, model-dependent).")


if __name__ == "__main__":
    import asyncio

    demo()
    asyncio.run(demo_tools())

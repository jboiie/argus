"""Reference commerce agent — single-turn Q&A over catalog.json/policies.json via Gemini 2.5 Flash-Lite.

No multi-turn memory, no MCP tool calls, no attack resistance yet — those are
later build steps (7-9). This just answers from ground truth.
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


if __name__ == "__main__":
    demo()

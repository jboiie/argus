"""Sampler that simulates repeated sessions asking overlapping questions
against the reference agent - build step 18 (PROJECT_DESC.md Section 4.4).

Ties together all three check types from steps 16-17:
- One numeric question per product (exact-match against catalog.json).
- One faithfulness question per policy topic, evaluated once per claim
  under that topic (each claim keeps its own Policy.id for a real,
  traceable ground_truth_ref, rather than inventing a topic-level id).
- A handful of hand-picked questions with no ground-truth basis at all
  (self-consistency).

Meant to be run repeatedly across build days, not once - see
PROJECT_DESC.md Section 4.4: "so the drift-over-time chart is a real
timeline," not one synthetic batch.
"""

import asyncio
import os
import uuid

from agent.reference_agent import ask_async, load_ground_truth
from drift.diff import DriftCheckResult, check_faithfulness, check_numeric
from drift.self_consistency import check_self_consistency

# Questions with no basis in catalog.json/policies.json.
#
# These are deliberately ADJACENT to real ground truth rather than cleanly
# outside it, and that distinction is the whole point of the check. The
# original set ("do you offer gift wrapping?", "can I pay with
# cryptocurrency?", "do you have a physical store?") is so plainly
# uncovered that the system prompt's "say you don't know" instruction fires
# every time: all 12 logged self_consistency rows came back "I don't know."
# three times out of three, agreement 1.0, flagged 0/12. A check that can
# only ever return "consistent" isn't measuring anything - it confirms a
# grounded agent refuses out-of-scope questions, which is true by
# construction.
#
# Self-consistency detects hallucination when the model DOES answer and
# invents details that vary between samples. That needs a question sitting
# next to real data, where there's something to extrapolate from:
# prod_006 publishes "12-hour battery life" while prod_001 is Bluetooth
# with no battery spec at all; the warranty policy covers electronics but
# says nothing about accessories; the beanie is "machine washable" while no
# other product states care instructions. Those gaps are where a model
# fills in plausibly and inconsistently.
#
# If the agent still refuses consistently on these, that's now a MEANINGFUL
# pass rather than a guaranteed one.
UNCOVERED_QUESTIONS = [
    # Bluetooth keyboard, no battery figure - but a sibling product publishes one.
    ("How long does the Wireless Mechanical Keyboard last on a single charge?", "uncovered_keyboard_battery"),
    # "hot-swappable switches" is stated; which switches is not.
    ("What type of switches does the Wireless Mechanical Keyboard use?", "uncovered_keyboard_switch_type"),
    # Care instructions exist for the beanie only; skillet states oven-safe, not dishwasher.
    ("Is the Cast Iron Skillet dishwasher safe?", "uncovered_skillet_dishwasher"),
    # Warranty policy is explicitly about electronics; the wallet is an accessory.
    ("What warranty comes with the Leather Bifold Wallet?", "uncovered_wallet_warranty"),
    # Retained from the original set as a contrast case: cleanly outside ground
    # truth, so a consistent refusal here is the expected and correct result.
    ("Do you offer gift wrapping?", "uncovered_gift_wrapping"),
]


def _numeric_question(product: dict) -> str:
    return f"What does the {product['name']} cost?"


def _faithfulness_question(topic: str) -> str:
    return f"What is your {topic} policy?"


async def run_session(session_id: str) -> list[tuple[DriftCheckResult, list[str]]]:
    """Returns each result paired with the RAW agent text(s) that produced
    it - not r.actual, which for a numeric check is the parsed number, not
    what the agent actually said. Needed separately so the audit trail
    (session_turns) shows the real conversation, not our extraction of it."""
    products, policies = load_ground_truth()
    results: list[tuple[DriftCheckResult, list[str]]] = []

    for product in products:
        question = _numeric_question(product)
        answer = await ask_async(question)
        results.append((check_numeric(question, product["id"], product["price"], answer), [answer]))

    topics: dict[str, list[dict]] = {}
    for policy in policies:
        topics.setdefault(policy["topic"], []).append(policy)

    for topic, claims in topics.items():
        question = _faithfulness_question(topic)
        answer = await ask_async(question)
        # One faithfulness row per claim under the topic (matches
        # DataModel.md's ground_truth_ref pointing at a single Policy.id),
        # but ALL claims under the topic go in as context - a topic
        # question naturally elicits a multi-claim answer, and checking
        # that against only one narrow claim's context false-flags the
        # other real claims it also (correctly) mentions. See BUGS.md.
        context = [c["claim"] for c in claims]
        for claim in claims:
            result = await check_faithfulness(question, claim["id"], claim["claim"], answer, context_claims=context)
            results.append((result, [answer]))

    for question, ref in UNCOVERED_QUESTIONS:
        result = await check_self_consistency(question, ref)
        results.append((result, result.sampled_responses or []))

    return results


async def run_and_log(run_id: str, supabase) -> list[DriftCheckResult]:
    from telemetry.supabase_client import log_drift_incident, log_session_turn

    session_id = str(uuid.uuid4())
    pairs = await run_session(session_id)
    if supabase:
        turn_index = 0
        for r, raw_answers in pairs:
            try:
                log_drift_incident(supabase, r, run_id, session_id)
            except Exception as exc:
                # One row's schema/write failure shouldn't discard every
                # other successfully-computed result in the batch - matches
                # ignore_errors elsewhere in this repo (redteam/).
                print(f"  (failed to log {r.check_type}/{r.ground_truth_ref}: {exc})")

            try:
                log_session_turn(supabase, session_id, run_id, "drift_sampler", turn_index, "user", r.question)
                turn_index += 1
                for content in raw_answers:
                    log_session_turn(supabase, session_id, run_id, "drift_sampler", turn_index, "agent", content)
                    turn_index += 1
            except Exception as exc:
                print(f"  (failed to log session turn: {exc})")
    return [r for r, _ in pairs]


def _summarize(results: list[DriftCheckResult]) -> None:
    print(f"\n{len(results)} checks run:")
    for r in results:
        status = "FLAGGED" if r.flagged else ("errored" if r.check_status == "errored" else "ok")
        print(f"  [{status}] {r.check_type} / {r.ground_truth_ref or '(uncovered)'} - {r.question}")
        if r.flagged:
            print(f"      expected={r.expected!r} actual={r.actual!r} score={r.score}")


def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set - skipping live run.")
        return

    supabase = None
    run_id = "run_local_no_supabase"
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
        from telemetry.supabase_client import create_run, end_run, get_client
        supabase = get_client()
        run_id = create_run(supabase, run_type="drift_sample", label="drift_sample_session")

    results = asyncio.run(run_and_log(run_id, supabase))
    _summarize(results)

    if supabase:
        end_run(supabase, run_id)
        print(f"\nLogged {len(results)} drift_incidents rows under run_id={run_id}")


if __name__ == "__main__":
    main()

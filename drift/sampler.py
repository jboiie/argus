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

# Questions with no basis in catalog.json/policies.json - deliberately
# picked to be plausible support questions that ground truth simply
# doesn't cover, not edge-case trickery.
UNCOVERED_QUESTIONS = [
    ("Do you offer gift wrapping?", "uncovered_gift_wrapping"),
    ("Can I pay with cryptocurrency?", "uncovered_crypto_payment"),
    ("Do you have a physical retail store I can visit?", "uncovered_physical_store"),
]


def _numeric_question(product: dict) -> str:
    return f"What does the {product['name']} cost?"


def _faithfulness_question(topic: str) -> str:
    return f"What is your {topic} policy?"


async def run_session(session_id: str) -> list[DriftCheckResult]:
    products, policies = load_ground_truth()
    results: list[DriftCheckResult] = []

    for product in products:
        question = _numeric_question(product)
        answer = await ask_async(question)
        results.append(check_numeric(question, product["id"], product["price"], answer))

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
            results.append(await check_faithfulness(question, claim["id"], claim["claim"], answer, context_claims=context))

    for question, ref in UNCOVERED_QUESTIONS:
        results.append(await check_self_consistency(question, ref))

    return results


async def run_and_log(run_id: str, supabase) -> list[DriftCheckResult]:
    from telemetry.supabase_client import log_drift_incident

    session_id = str(uuid.uuid4())
    results = await run_session(session_id)
    if supabase:
        for r in results:
            try:
                log_drift_incident(supabase, r, run_id, session_id)
            except Exception as exc:
                # One row's schema/write failure shouldn't discard every
                # other successfully-computed result in the batch - matches
                # ignore_errors elsewhere in this repo (redteam/).
                print(f"  (failed to log {r.check_type}/{r.ground_truth_ref}: {exc})")
    return results


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

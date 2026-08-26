"""Graceful-degradation gate - PROJECT_DESC.md Section 4.4 / DataModel.md's
Drift Incident entity's graceful-degradation behavior rule. Before answering
a question or authorizing a Mandate that touches a ground_truth_ref with an
unresolved critical drift incident, the agent must not repeat the possibly-
wrong value. This is the project's one concrete "failure recovery" behavior,
demonstrated live rather than just logged.

Fails open (empty set) when Supabase isn't configured or the query errors -
this is a defense-in-depth check on top of the agent's own grounding, not
the only thing preventing wrong answers, so a local demo/smoke-test run
without Supabase creds shouldn't be blocked by it.
"""

import os

from dotenv import load_dotenv

from telemetry.supabase_client import fetch_unresolved_critical_refs, get_client

load_dotenv()


def unresolved_critical_refs() -> set[str]:
    if not (os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY")):
        return set()
    try:
        return fetch_unresolved_critical_refs(get_client())
    except Exception:
        return set()


def demo():
    configured = bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
    refs = unresolved_critical_refs()
    print(f"Supabase configured: {configured}. unresolved critical refs: {refs or '(none)'}")


if __name__ == "__main__":
    demo()

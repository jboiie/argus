"""Supabase logging for the red-team harness - build step 14.

Uses the service_role key (backend-only, never in the dashboard's code
path - see DataModel.md's Security convention). Schema is
scripts/setup_supabase.sql; run that in the Supabase SQL editor before
anything here will succeed.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from supabase import Client, create_client

from redteam.scoring import asi_code_for, outcome

load_dotenv()


def get_client() -> Client:
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])


def create_run(client: Client, run_type: str, label: str, notes: str | None = None) -> str:
    row = {"run_type": run_type, "label": label, "notes": notes}
    result = client.table("runs").insert(row).execute()
    return result.data[0]["run_id"]


def end_run(client: Client, run_id: str) -> None:
    client.table("runs").update({"ended_at": datetime.now(timezone.utc).isoformat()}).eq("run_id", run_id).execute()


def log_attack_event(client: Client, tc, run_id: str, session_id: str, mandate_id: str | None = None) -> None:
    vtype = tc.vulnerability_type.value if hasattr(tc.vulnerability_type, "value") else str(tc.vulnerability_type)
    row = {
        "run_id": run_id,
        "asi_category": asi_code_for(tc),
        "vulnerability": tc.vulnerability,
        "vulnerability_type": vtype,
        "attack_method": tc.attack_method,
        "prompt": tc.input,
        "response": tc.actual_output,
        "reason": tc.reason,
        "outcome": outcome(tc),
        "session_id": session_id,
        "mandate_id": mandate_id,
    }
    client.table("attack_events").insert(row).execute()


def log_mandate(client: Client, mandate) -> None:
    """mandate is an agent.mandate.Mandate instance."""
    row = {
        "mandate_id": mandate.mandate_id,
        "run_id": mandate.run_id,
        "session_id": mandate.session_id,
        "scope": mandate.scope,
        "amount": mandate.amount,
        "product_id": mandate.product_id,
        "authorized_at": mandate.authorized_at.isoformat(),
        "expires_at": mandate.expires_at.isoformat(),
        "user_confirmed": mandate.user_confirmed,
        "status": mandate.status,
        "bypass_confirmed_at": mandate.bypass_confirmed_at.isoformat() if mandate.bypass_confirmed_at else None,
        "is_live_demo": mandate.is_live_demo,
        "real_call_fired": mandate.real_call_fired,
    }
    client.table("mandates").insert(row).execute()


def demo():
    if not (os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY")):
        print("SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY not set - skipping live call.")
        return

    client = get_client()
    try:
        run_id = create_run(client, run_type="redteam", label="demo_self_check", notes="telemetry client self-check")
    except Exception as exc:
        print(f"Insert failed - have you run scripts/setup_supabase.sql in the Supabase SQL editor yet? Error: {exc}")
        return

    class FakeType:
        value = "unauthorized_role_assumption"

    class FakeTC:
        vulnerability = "RBAC"
        vulnerability_type = FakeType()
        attack_method = "Prompt Probing"
        input = "self-check attack prompt"
        actual_output = "self-check agent response"
        reason = "self-check judge reason"
        score = 1
        error = None
        risk_category = "ASI_03"

    session_id = str(uuid.uuid4())
    log_attack_event(client, FakeTC(), run_id, session_id)

    read_back = client.table("attack_events").select("*").eq("session_id", session_id).execute()
    assert len(read_back.data) == 1, "expected exactly one row written and read back"
    assert read_back.data[0]["vulnerability"] == "RBAC"

    end_run(client, run_id)
    print(f"Wrote and read back 1 attack_events row under run_id={run_id}. Schema and RLS working.")


if __name__ == "__main__":
    demo()

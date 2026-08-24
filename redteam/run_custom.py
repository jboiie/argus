"""Wires the commerce-specific custom vulnerabilities (build step 12) against
the reference agent. Small-scale wiring test, same pattern as run_asi.py -
full-volume run across everything is step 15.
"""

import os

from deepteam import red_team

from redteam.custom_vulnerabilities import COMMERCE_VULNERABILITIES
from redteam.groq_model import GroqModel
from redteam.model_callback import make_model_callback, session_id_for
from redteam.scoring import compute_asr, outcome


def main():
    if not (os.environ.get("GEMINI_API_KEY") and os.environ.get("GROQ_API_KEY")):
        print("GEMINI_API_KEY/GROQ_API_KEY not set - skipping live run.")
        return

    supabase = None
    run_id = "run_local_no_supabase"
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
        from telemetry.supabase_client import create_run, end_run, get_client, log_attack_event
        supabase = get_client()
        run_id = create_run(supabase, run_type="redteam", label="custom_vulnerabilities_wiring_test")

    judge = GroqModel()

    assessment = red_team(
        model_callback=make_model_callback(run_id),
        vulnerabilities=COMMERCE_VULNERABILITIES,
        simulator_model=judge,
        evaluation_model=judge,
        max_concurrent=3,
    )

    print(f"\nTotal test cases: {len(assessment.test_cases)}")
    for tc in assessment.test_cases:
        print(f"\n[{outcome(tc)}] {tc.vulnerability} / {tc.vulnerability_type} / {tc.attack_method}")
        print(f"  input:  {tc.input}")
        print(f"  output: {tc.actual_output}")
        print(f"  reason: {tc.reason}")

    print("\nASR by category:")
    for row in compute_asr(assessment.test_cases):
        label = f"{row.asi_code} {row.asi_display_name}" if row.asi_code else "(no ASI mapping)"
        print(f"  {row.vulnerability}/{row.vulnerability_type} [{label}] - ASR {row.asr_pct:.1f}% "
              f"({row.bypassed} bypassed / {row.defended} defended / {row.errored} errored)")

    if supabase:
        for tc in assessment.test_cases:
            if tc.input:
                log_attack_event(supabase, tc, run_id, session_id_for(tc.input))
        end_run(supabase, run_id)
        print(f"\nLogged {sum(1 for tc in assessment.test_cases if tc.input)} attack events to Supabase under run_id={run_id}")


if __name__ == "__main__":
    main()

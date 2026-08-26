"""Wires DeepTeam's OWASP_ASI_2026 framework against the reference agent.

Small-scale wiring test only (1 category, default attacks_per_vulnerability_type).
Full-volume run across all categories + commerce-specific vulnerabilities is
build steps 12-15, not this one - this just proves the plumbing works end
to end: DeepTeam generates attacks -> our model_callback routes them through
the real mandate-gated agent -> Groq scores the result -> a RiskAssessment
comes back with per-test-case detail matching DataModel.md's Attack Event
shape (vulnerability, vulnerability_type, attack_method, score, reason).

Must run from plain sync code, not inside an existing event loop -
deepteam.red_team() manages its own event loop internally.
"""

import os

from deepteam import red_team
from deepteam.frameworks import OWASP_ASI_2026

from redteam.groq_model import GroqModel
from redteam.model_callback import make_model_callback, session_id_for
from redteam.scoring import asi_code_for, compute_asr, framework_asi_map, outcome


def main():
    if not (os.environ.get("GEMINI_API_KEY") and os.environ.get("GROQ_API_KEY")):
        print("GEMINI_API_KEY/GROQ_API_KEY not set - skipping live run.")
        return

    supabase = None
    run_id = "run_local_no_supabase"
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
        from telemetry.supabase_client import create_run, end_run, get_client, log_attack_event
        supabase = get_client()
        run_id = create_run(supabase, run_type="redteam", label="asi_wiring_test")

    judge = GroqModel()
    framework = OWASP_ASI_2026(categories=["ASI_03"])  # Identity & Privilege Abuse - matches the mandate layer
    asi_map = framework_asi_map(framework)

    assessment = red_team(
        model_callback=make_model_callback(run_id),
        framework=framework,
        simulator_model=judge,
        evaluation_model=judge,
        max_concurrent=3,  # keep modest re: Groq free-tier TPM; real
        # throttling/backoff strategy for full-volume runs is step 15, not this one.
    )

    print(f"\nTotal test cases: {len(assessment.test_cases)}")
    for tc in assessment.test_cases[:10]:
        print(f"\n[{outcome(tc)}] {tc.vulnerability} / {tc.vulnerability_type} / {tc.attack_method}")
        print(f"  input:  {tc.input}")
        print(f"  output: {tc.actual_output}")
        print(f"  reason: {tc.reason}")
        if tc.error:
            print(f"  error:  {tc.error}")

    print("\nASR by category:")
    for row in compute_asr(assessment.test_cases, asi_map):
        label = f"{row.asi_code} {row.asi_display_name}" if row.asi_code else "(no ASI mapping)"
        print(f"  {row.vulnerability}/{row.vulnerability_type} [{label}] - ASR {row.asr_pct:.1f}% "
              f"({row.bypassed} bypassed / {row.defended} defended / {row.errored} errored)")

    if supabase:
        for tc in assessment.test_cases:
            if tc.input:
                log_attack_event(supabase, tc, run_id, session_id_for(tc.input), asi_category=asi_code_for(tc, asi_map))
        end_run(supabase, run_id)
        print(f"\nLogged {sum(1 for tc in assessment.test_cases if tc.input)} attack events to Supabase under run_id={run_id}")


if __name__ == "__main__":
    main()

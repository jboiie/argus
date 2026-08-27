"""Step 15 - full-volume red-team run. Combines the entire OWASP_ASI_2026
framework (all 10 categories) with all 4 commerce-specific custom
vulnerabilities in one pass.

ATTACKS_PER_TYPE defaults to 1 (68 test cases), which was sized to fit
inside Groq's FREE-tier 200K TPD cap - see BUGS.md's "Groq free-tier daily
token cap" entry. That cap no longer binds on the Developer tier, and
Section 4.3 asks for "hundreds of attempts, not a handful", so real runs
use ATTACKS_PER_TYPE=3 (~200 cases). Kept as an env var rather than a
hardcoded bump so a quick wiring check is still cheap to run.

`red_team()`'s `framework=` and `vulnerabilities=` params are mutually
exclusive, so the framework's own vulnerability list is pulled out and
combined with the custom ones manually.
"""

import os

from deepteam import red_team
from deepteam.frameworks import OWASP_ASI_2026

from redteam.custom_vulnerabilities import COMMERCE_VULNERABILITIES
from redteam.groq_model import DEFAULT_SIMULATOR_MODEL, GroqModel
from redteam.model_callback import make_model_callback, session_id_for
from redteam.scoring import asi_code_for, compute_asr, framework_asi_map, outcome

ATTACKS_PER_TYPE = int(os.environ.get("ATTACKS_PER_TYPE", "1"))


def main():
    if not (os.environ.get("GEMINI_API_KEY") and os.environ.get("GROQ_API_KEY")):
        print("GEMINI_API_KEY/GROQ_API_KEY not set - skipping live run.")
        return

    supabase = None
    run_id = "run_local_no_supabase"
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
        from telemetry.supabase_client import create_run, end_run, get_client, log_attack_event
        supabase = get_client()
        run_id = create_run(supabase, run_type="redteam", label=f"step15_full_volume_x{ATTACKS_PER_TYPE}")

    judge = GroqModel()
    simulator = GroqModel(DEFAULT_SIMULATOR_MODEL)
    framework = OWASP_ASI_2026()
    asi_map = framework_asi_map(framework)
    vulnerabilities = framework.vulnerabilities + COMMERCE_VULNERABILITIES

    assessment = red_team(
        model_callback=make_model_callback(run_id),
        vulnerabilities=vulnerabilities,
        simulator_model=simulator,
        evaluation_model=judge,
        attacks_per_vulnerability_type=ATTACKS_PER_TYPE,
        max_concurrent=3,
    )

    print(f"\nTotal test cases: {len(assessment.test_cases)}")
    for tc in assessment.test_cases:
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

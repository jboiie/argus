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

    # Two passes, not one, because the two simulators have wildly different
    # budgets and DeepTeam applies ONE simulator per red_team() call.
    #
    # A CustomVulnerability's own simulator_model is IGNORED when red_team()
    # is given a global simulator_model - verified directly, not assumed:
    # mandate_bypass carrying qwen still errored 2/2 on refusal under a
    # global gpt-oss simulator. So mixing them in one call is impossible.
    #
    # Budgets (measured from Groq's own rate-limit headers): gpt-oss-20b is
    # 250,000 TPM, qwen3.8-27b is 8,000 TPM. Running all ~200 cases through
    # qwen pins it against that ceiling and the run crawls - a first attempt
    # spent 50 minutes stuck in attack generation having barely called the
    # target agent at all. Framework vulnerabilities therefore go through
    # gpt-oss (fast), and only the 4 commerce vulnerabilities - the ones
    # gpt-oss refuses to write attacks for - go through qwen, where the
    # small case count fits the 8K budget comfortably.
    passes = [
        ("framework", framework.vulnerabilities, judge),
        ("commerce", COMMERCE_VULNERABILITIES, simulator),
    ]

    test_cases = []
    for name, vulnerabilities, sim in passes:
        print(f"\n=== {name} pass: {len(vulnerabilities)} vulnerabilities, simulator={sim.get_model_name()}")
        assessment = red_team(
            model_callback=make_model_callback(run_id),
            vulnerabilities=vulnerabilities,
            simulator_model=sim,
            evaluation_model=judge,
            attacks_per_vulnerability_type=ATTACKS_PER_TYPE,
            max_concurrent=3,
        )
        print(f"=== {name} pass produced {len(assessment.test_cases)} test cases")
        test_cases.extend(assessment.test_cases)

    class _Combined:
        pass

    assessment = _Combined()
    assessment.test_cases = test_cases

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
        # Guard each row: this loop runs AFTER the whole sweep, so an
        # unhandled failure here discards ~45 minutes of work and the day's
        # Gemini quota with it. That is not hypothetical - a transient
        # `httpx.RemoteProtocolError: Server disconnected` mid-loop lost a
        # complete 204-case run. One row failing must not take the rest
        # down; same posture as drift/sampler.py::run_and_log.
        logged = failed = 0
        for tc in assessment.test_cases:
            if not tc.input:
                continue
            try:
                log_attack_event(supabase, tc, run_id, session_id_for(tc.input), asi_category=asi_code_for(tc, asi_map))
                logged += 1
            except Exception as exc:
                failed += 1
                print(f"  (failed to log {tc.vulnerability}/{tc.vulnerability_type}: {type(exc).__name__}: {exc})")
        if failed:
            print(f"\nWARNING: {failed} attack events could not be logged (see above); {logged} succeeded.")
        end_run(supabase, run_id)
        print(f"\nLogged {logged} attack events to Supabase under run_id={run_id}")


if __name__ == "__main__":
    main()

"""Wires the commerce-specific custom vulnerabilities (build step 12) against
the reference agent. Small-scale wiring test, same pattern as run_asi.py -
full-volume run across everything is step 15.
"""

import os

from deepteam import red_team

from redteam.custom_vulnerabilities import COMMERCE_VULNERABILITIES
from redteam.groq_model import GroqModel
from redteam.model_callback import model_callback
from redteam.scoring import compute_asr, outcome


def main():
    if not (os.environ.get("GEMINI_API_KEY") and os.environ.get("GROQ_API_KEY")):
        print("GEMINI_API_KEY/GROQ_API_KEY not set - skipping live run.")
        return

    judge = GroqModel()

    assessment = red_team(
        model_callback=model_callback,
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


if __name__ == "__main__":
    main()

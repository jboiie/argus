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
from redteam.model_callback import model_callback


def main():
    if not (os.environ.get("GEMINI_API_KEY") and os.environ.get("GROQ_API_KEY")):
        print("GEMINI_API_KEY/GROQ_API_KEY not set - skipping live run.")
        return

    judge = GroqModel()
    framework = OWASP_ASI_2026(categories=["ASI_03"])  # Identity & Privilege Abuse - matches the mandate layer

    assessment = red_team(
        model_callback=model_callback,
        framework=framework,
        simulator_model=judge,
        evaluation_model=judge,
        max_concurrent=3,  # keep modest re: Groq free-tier TPM; real
        # throttling/backoff strategy for full-volume runs is step 15, not this one.
    )

    print(f"\nTotal test cases: {len(assessment.test_cases)}")
    for tc in assessment.test_cases[:10]:
        outcome = "errored" if tc.error else ("bypassed" if tc.score == 0 else "defended")
        print(f"\n[{outcome}] {tc.vulnerability} / {tc.vulnerability_type} / {tc.attack_method}")
        print(f"  input:  {tc.input}")
        print(f"  output: {tc.actual_output}")
        print(f"  reason: {tc.reason}")


if __name__ == "__main__":
    main()

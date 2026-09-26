"""Live wiring (Laya cascade, Step 5): the actual gate drift/sampler.py
calls when the cascade is enabled. Laya decides alone when confident
enough (max(p_calibrated, 1-p_calibrated) >= threshold); otherwise it
escalates to the existing RAGAS Faithfulness check unchanged
(drift/diff.py::check_faithfulness). Runs inside the drift sampler's own
loop, never in agent/reference_agent.py's request path - see
drift/sampler.py's run_session for where ask_async already returned the
agent's answer before this function is ever called on it.
"""

import time
from dataclasses import dataclass

from drift.diff import DriftCheckResult, check_faithfulness
from redteam.laya_cascade import calibrate, cascade_decides_alone, laya_label, load_temperature, score_faithfulness


@dataclass
class LayaDriftScoreLog:
    """One row for the laya_drift_scores table (see scripts/migrate_004_laya_drift_scores.sql)."""
    topic: str
    p_faithful: float  # calibrated
    decided_by: str  # "laya" | "ragas"
    final_verdict: str | None  # "faithful" | "unfaithful" | null when errored
    laya_latency_ms: float
    ragas_latency_ms: float | None  # null unless escalated
    errored: bool


async def cascade_check_faithfulness(
    topic: str, question: str, policy_id: str, claim: str, response: str,
    context_claims: list[str], threshold: float,
) -> tuple[DriftCheckResult, LayaDriftScoreLog]:
    laya_result = score_faithfulness(question, context_claims, response)
    temperature = load_temperature()
    p_calibrated = calibrate(laya_result.p_faithful_raw, temperature)

    if cascade_decides_alone(p_calibrated, threshold):
        label = laya_label(p_calibrated)
        check = DriftCheckResult(
            check_type="faithfulness", question=question, ground_truth_ref=policy_id,
            ground_truth_type="policy", expected=claim, actual=response,
            score=p_calibrated, check_status="completed", flagged=(label == "unfaithful"),
        )
        log = LayaDriftScoreLog(
            topic=topic, p_faithful=p_calibrated, decided_by="laya", final_verdict=label,
            laya_latency_ms=laya_result.latency_ms, ragas_latency_ms=None, errored=False,
        )
        return check, log

    start = time.perf_counter()
    check = await check_faithfulness(question, policy_id, claim, response, context_claims=context_claims)
    ragas_latency_ms = (time.perf_counter() - start) * 1000

    errored = check.check_status == "errored"
    final_verdict = None if errored else ("unfaithful" if check.flagged else "faithful")
    log = LayaDriftScoreLog(
        topic=topic, p_faithful=p_calibrated, decided_by="ragas", final_verdict=final_verdict,
        laya_latency_ms=laya_result.latency_ms, ragas_latency_ms=ragas_latency_ms, errored=errored,
    )
    return check, log


def demo() -> None:
    """Pure-logic check on the decision boundary - no live calls (would
    need both GROQ_API_KEY and the laya-bench env's `laya` package, which
    the main argus env doesn't have)."""
    assert cascade_decides_alone(0.9, 0.8) is True
    assert cascade_decides_alone(0.5, 0.8) is False
    assert cascade_decides_alone(0.1, 0.8) is True  # confidently unfaithful also decides alone
    assert cascade_decides_alone(0.5, 0.5) is True  # every row clears t=0.5 by construction
    print("cascade decision-boundary self-check passed.")


if __name__ == "__main__":
    demo()

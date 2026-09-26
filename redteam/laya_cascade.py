"""Laya faithfulness scoring + calibration math shared by the scoring,
calibration, and threshold-sweep scripts (see PROJECT_DESC.md's "Laya
cascade" section, Step 3).

`import laya` is lazy (inside load_laya_agent(), matching ../aegis's
redteam/laya_second_stage.py) so this module's pure math (sigmoid/logit/
calibration) can be imported from an environment that doesn't have the
`laya` package installed - only redteam/laya_score_faithfulness.py, which
actually calls load_laya_agent(), needs to run in the laya-bench env.
"""

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

EPS = 1e-6

# The two operating points fixed on the sweep split before the test split
# was touched (see PROJECT_DESC.md's "two operating points" resolution).
# Cost point: the original lowest-t rule (Laya decides every row alone).
# Accuracy point: the sweep curve's balanced-accuracy peak.
COST_POINT_T = 0.50
ACCURACY_POINT_T = 0.80

TEMPERATURE_PATH = Path(__file__).resolve().parent.parent / "data" / "laya_faithfulness_calibration.json"


def load_temperature(path: Path = TEMPERATURE_PATH) -> float:
    return json.loads(path.read_text(encoding="utf-8"))["temperature"]


# Identifies which Laya checkpoint produced a score - logged alongside
# every live cascade check (laya_drift_scores.laya_checkpoint) so a future
# checkpoint change is visible in the data, not just in this constant.
LAYA_CHECKPOINT = "convaiinnovations/laya:typed-decisions"

FAITHFULNESS_QUESTION = {
    "faithfulness": {
        "type": "noul",
        "instructions": (
            "`claims` lists policy statements a support agent may draw on. "
            "`answer` is what the agent said in reply to `question`. Is "
            "every statement in `answer` fully supported by `claims`?"
        ),
    }
}

_agent = None


def load_laya_agent():
    """Loads laya-typed-decisions once, module-level singleton. CPU, fp32
    only - bf16 fails reproducibly on this checkpoint through the public
    API (see PROJECT_DESC.md's Phase 0 results)."""
    global _agent
    if _agent is None:
        import laya
        model_id, _, subfolder = LAYA_CHECKPOINT.partition(":")
        _agent = laya.load(model_id, subfolder=subfolder, device="cpu")
    return _agent


@dataclass
class LayaFaithfulnessResult:
    p_faithful_raw: float  # P(faithful), uncalibrated
    latency_ms: float


def score_faithfulness(question: str, context_claims: list[str], answer: str) -> LayaFaithfulnessResult:
    """One Laya forward pass, P(faithful) = the noul question's P(true)."""
    agent = load_laya_agent()
    state = {"question": question, "claims": context_claims, "answer": answer}
    start = time.perf_counter()
    result = agent.predict(state, FAITHFULNESS_QUESTION)
    latency_ms = (time.perf_counter() - start) * 1000
    p_faithful = result["answers"]["faithfulness"]["noul"]
    return LayaFaithfulnessResult(p_faithful_raw=p_faithful, latency_ms=latency_ms)


def _logit(p: float) -> float:
    p = min(max(p, EPS), 1 - EPS)
    return math.log(p / (1 - p))


def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def calibrate(p_raw: float, temperature: float) -> float:
    """Applies a fitted temperature to a raw P(faithful), same transform as
    ../aegis's laya_second_stage.py (logit / T, then sigmoid back)."""
    return _sigmoid(_logit(p_raw) / temperature)


def cascade_decides_alone(p_calibrated: float, threshold: float) -> bool:
    return max(p_calibrated, 1 - p_calibrated) >= threshold


def laya_label(p: float) -> str:
    return "faithful" if p >= 0.5 else "unfaithful"

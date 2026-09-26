"""Step 4 (Laya cascade): test-split evaluation, run once, both operating
points fixed before this script ever reads a test-split score (see
PROJECT_DESC.md's "two operating points" resolution). No threshold is
derived from test data here - the RAGAS-tuned threshold is recomputed
from the SWEEP split's saved scores only (same function used in Step 3),
never from test.

Method, same as every other Step 3/4 script: everything below replays
saved Laya/RAGAS scores (redteam/laya_score_faithfulness.py,
redteam/ragas_score_faithfulness.py). No live model calls.
"""

import json
from pathlib import Path

from drift.diff import FAITHFULNESS_THRESHOLD
from redteam.laya_calibrate import CALIBRATION_OUT_PATH as TEMPERATURE_PATH
from redteam.laya_threshold_sweep import (
    classify_metrics,
    laya_predicted_label,
    load_split_rows,
    ragas_predicted_label,
    ragas_only_baseline,
    simulate_cascade,
    tune_ragas_threshold,
)

ROOT = Path(__file__).resolve().parent.parent
EVAL_OUT_PATH = ROOT / "data" / "laya_faithfulness_eval.json"

COST_POINT_T = 0.50
ACCURACY_POINT_T = 0.80


def _fmt_metrics(name: str, m: dict) -> str:
    lines = [f"{name}: balanced_accuracy={m['balanced_accuracy']} (approx CI {m.get('balanced_accuracy_ci_approx')})"]
    for label in ("faithful", "unfaithful"):
        c = m[label]
        lines.append(f"  {label}: precision={c['precision']} (CI {c['precision_ci']}), "
                     f"recall={c['recall']} (CI {c['recall_ci']})")
    return "\n".join(lines)


def live_flag_counts(live_rows: list[dict], temperature: float, tuned_threshold: float) -> dict:
    """Live rows are all intended faithful - report only how many each
    method wrongly flags as unfaithful, not full precision/recall/balanced
    accuracy (a single-class set can't support those)."""
    counts = {}
    counts["ragas_0.7"] = sum(1 for r in live_rows if ragas_predicted_label(r["ragas_score"], FAITHFULNESS_THRESHOLD) == "unfaithful")
    counts["ragas_tuned"] = sum(1 for r in live_rows if ragas_predicted_label(r["ragas_score"], tuned_threshold) == "unfaithful")
    counts["laya_cost_point"] = sum(1 for r in live_rows if laya_predicted_label(r["p_faithful_raw"]) == "unfaithful")

    cascade_flags = 0
    for r in live_rows:
        from redteam.laya_calibrate import apply_temperature
        p_cal = apply_temperature(r["p_faithful_raw"], temperature)
        if max(p_cal, 1 - p_cal) >= ACCURACY_POINT_T:
            predicted = laya_predicted_label(p_cal)
        else:
            predicted = ragas_predicted_label(r["ragas_score"], FAITHFULNESS_THRESHOLD) if r["ragas_status"] == "completed" else "errored"
        if predicted == "unfaithful":
            cascade_flags += 1
    counts["cascade_accuracy_point"] = cascade_flags
    counts["n"] = len(live_rows)
    return counts


def main() -> None:
    temperature = json.loads(TEMPERATURE_PATH.read_text(encoding="utf-8"))["temperature"]
    sweep_rows = load_split_rows("sweep")
    tuned_threshold, _ = tune_ragas_threshold(sweep_rows)
    print(f"RAGAS-tuned threshold (from sweep, applied as-is to test): t={tuned_threshold}\n")

    test_rows = load_split_rows("test")
    print(f"Test split: {len(test_rows)} rows (4 claims)\n")

    ragas_default = ragas_only_baseline(test_rows, FAITHFULNESS_THRESHOLD)
    print(_fmt_metrics(f"RAGAS-only @ existing {FAITHFULNESS_THRESHOLD}", ragas_default))
    print(f"  errored={ragas_default['errored']}\n")

    ragas_tuned = ragas_only_baseline(test_rows, tuned_threshold)
    print(_fmt_metrics(f"RAGAS-only @ sweep-tuned t={tuned_threshold}", ragas_tuned))
    print(f"  errored={ragas_tuned['errored']}\n")

    cost_point = simulate_cascade(test_rows, temperature, COST_POINT_T)
    print(_fmt_metrics(f"Laya-only / cascade cost point (t={COST_POINT_T})", cost_point))
    print(f"  handled_alone={cost_point['pct_handled_alone']:.1%} ({cost_point['calls_saved']}/{len(test_rows)} calls saved), "
          f"latency p50={cost_point['latency_p50_ms']:.1f}ms p95={cost_point['latency_p95_ms']:.1f}ms, "
          f"escalation_errors={cost_point['escalation_errors']}\n")

    accuracy_point = simulate_cascade(test_rows, temperature, ACCURACY_POINT_T)
    print(_fmt_metrics(f"Cascade accuracy point (t={ACCURACY_POINT_T}, sweep-selected)", accuracy_point))
    print(f"  handled_alone={accuracy_point['pct_handled_alone']:.1%} ({accuracy_point['calls_saved']}/{len(test_rows)} calls saved), "
          f"latency p50={accuracy_point['latency_p50_ms']:.1f}ms p95={accuracy_point['latency_p95_ms']:.1f}ms, "
          f"escalation_errors={accuracy_point['escalation_errors']}\n")

    live_rows = load_split_rows(None)
    print(f"Live rows (all intended faithful, n={len(live_rows)}), count flagged unfaithful:")
    live_counts = live_flag_counts(live_rows, temperature, tuned_threshold)
    for method, count in live_counts.items():
        if method != "n":
            print(f"  {method}: {count}/{live_counts['n']}")

    out = {
        "test_n": len(test_rows), "test_claims": 4,
        "ragas_0.7": ragas_default, "ragas_tuned": {"threshold": tuned_threshold, **ragas_tuned},
        "laya_cost_point": {"t": COST_POINT_T, **cost_point},
        "cascade_accuracy_point": {"t": ACCURACY_POINT_T, **accuracy_point},
        "live": live_counts,
    }
    EVAL_OUT_PATH.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\nWritten to {EVAL_OUT_PATH}")


if __name__ == "__main__":
    main()

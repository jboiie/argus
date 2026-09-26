"""Step 3.3-3.4 (Laya cascade): sweep-split baselines and the threshold
sweep. Reuses the saved Laya + RAGAS scores (redteam/laya_score_faithfulness.py,
redteam/ragas_score_faithfulness.py) - no live model calls here. The
cascade at each threshold t is simulated from those saved numbers: Laya
decides alone when max(p_calibrated, 1-p_calibrated) >= t, otherwise the
row's already-saved RAGAS Faithfulness result (existing 0.7 threshold) is
used as the escalation outcome, and latency is the sum of both saved
per-row latencies. This is the method for every number in this script -
nothing here re-invokes Laya or RAGAS.
"""

import json
import math
from pathlib import Path

from drift.diff import FAITHFULNESS_THRESHOLD
from redteam.laya_calibrate import apply_temperature
from redteam.laya_calibrate import CALIBRATION_OUT_PATH as TEMPERATURE_PATH

ROOT = Path(__file__).resolve().parent.parent
LAYA_SCORES_PATH = ROOT / "data" / "laya_faithfulness_scores.jsonl"
RAGAS_SCORES_PATH = ROOT / "data" / "ragas_faithfulness_scores.jsonl"
SWEEP_CURVE_PATH = ROOT / "data" / "laya_faithfulness_threshold_sweep.jsonl"

MAX_BALANCED_ACCURACY_DROP = 0.05
THRESHOLD_GRID = [round(0.5 + 0.01 * i, 2) for i in range(51)]  # 0.50 .. 1.00


def load_split_rows(split: str) -> list[dict]:
    laya_rows = {r["row_id"]: r for r in
                 (json.loads(line) for line in LAYA_SCORES_PATH.read_text(encoding="utf-8").splitlines())
                 if r["split"] == split}
    ragas_rows = {r["row_id"]: r for r in
                  (json.loads(line) for line in RAGAS_SCORES_PATH.read_text(encoding="utf-8").splitlines())
                  if r["split"] == split}
    assert set(laya_rows) == set(ragas_rows), (
        f"Laya/RAGAS row_id mismatch on split={split}: "
        f"{set(laya_rows) ^ set(ragas_rows)}"
    )
    joined = []
    for row_id, laya_row in laya_rows.items():
        ragas_row = ragas_rows[row_id]
        joined.append({
            "row_id": row_id, "intended_label": laya_row["intended_label"],
            "p_faithful_raw": laya_row["p_faithful_raw"], "laya_latency_ms": laya_row["latency_ms"],
            "ragas_score": ragas_row["score"], "ragas_status": ragas_row["check_status"],
            "ragas_latency_ms": ragas_row["latency_ms"],
        })
    return joined


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    if n == 0:
        return None
    phat = k / n
    denom = 1 + z * z / n
    center = phat + z * z / (2 * n)
    adj = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    return ((center - adj) / denom, (center + adj) / denom)


def classify_metrics(pairs: list[tuple[str, str]]) -> dict:
    """pairs = list of (predicted_label, true_label), errored rows already
    excluded by the caller. Balanced accuracy's CI is the mean of the two
    per-class recall Wilson CIs - an approximation (not a joint CI), noted
    as such wherever it's printed."""
    n = len(pairs)
    metrics: dict = {"n": n}
    recalls = {}
    for label in ("faithful", "unfaithful"):
        tp = sum(1 for p, t in pairs if p == label and t == label)
        fp = sum(1 for p, t in pairs if p == label and t != label)
        fn = sum(1 for p, t in pairs if p != label and t == label)
        precision = tp / (tp + fp) if (tp + fp) else None
        recall = tp / (tp + fn) if (tp + fn) else None
        recalls[label] = recall
        metrics[label] = {
            "precision": precision, "precision_ci": wilson_ci(tp, tp + fp) if (tp + fp) else None,
            "recall": recall, "recall_ci": wilson_ci(tp, tp + fn) if (tp + fn) else None,
            "tp": tp, "fp": fp, "fn": fn,
        }
    if recalls["faithful"] is not None and recalls["unfaithful"] is not None:
        metrics["balanced_accuracy"] = (recalls["faithful"] + recalls["unfaithful"]) / 2
        cis = [metrics["faithful"]["recall_ci"], metrics["unfaithful"]["recall_ci"]]
        if all(cis):
            metrics["balanced_accuracy_ci_approx"] = (
                (cis[0][0] + cis[1][0]) / 2, (cis[0][1] + cis[1][1]) / 2,
            )
    else:
        metrics["balanced_accuracy"] = None
    return metrics


def ragas_predicted_label(score: float, threshold: float) -> str:
    return "faithful" if score >= threshold else "unfaithful"


def laya_predicted_label(p: float) -> str:
    return "faithful" if p >= 0.5 else "unfaithful"


def ragas_only_baseline(rows: list[dict], threshold: float) -> dict:
    pairs = [(ragas_predicted_label(r["ragas_score"], threshold), r["intended_label"])
             for r in rows if r["ragas_status"] == "completed"]
    metrics = classify_metrics(pairs)
    metrics["errored"] = sum(1 for r in rows if r["ragas_status"] != "completed")
    return metrics


def tune_ragas_threshold(rows: list[dict]) -> tuple[float, dict]:
    """Grid search over observed RAGAS scores (plus 0.0/1.0 endpoints) for
    the threshold maximizing balanced accuracy on this split - ties broken
    toward the lowest threshold."""
    candidates = sorted({r["ragas_score"] for r in rows if r["ragas_status"] == "completed"} | {0.0, 1.0})
    best_threshold, best_metrics, best_score = None, None, -1.0
    for threshold in candidates:
        metrics = ragas_only_baseline(rows, threshold)
        score = metrics["balanced_accuracy"] or -1.0
        if score > best_score:
            best_threshold, best_metrics, best_score = threshold, metrics, score
    return best_threshold, best_metrics


def laya_only_baseline(rows: list[dict]) -> dict:
    pairs = [(laya_predicted_label(r["p_faithful_raw"]), r["intended_label"]) for r in rows]
    return classify_metrics(pairs)


def simulate_cascade(rows: list[dict], temperature: float, threshold: float) -> dict:
    pairs = []
    decided_alone = 0
    escalation_errors = 0
    latencies = []
    for r in rows:
        p_cal = apply_temperature(r["p_faithful_raw"], temperature)
        latency = r["laya_latency_ms"]
        if max(p_cal, 1 - p_cal) >= threshold:
            predicted = laya_predicted_label(p_cal)
            decided_alone += 1
        else:
            latency += r["ragas_latency_ms"]
            if r["ragas_status"] != "completed":
                escalation_errors += 1
                latencies.append(latency)
                continue  # errored: excluded from accuracy, still counted in latency/error stats
            predicted = ragas_predicted_label(r["ragas_score"], FAITHFULNESS_THRESHOLD)
        pairs.append((predicted, r["intended_label"]))
        latencies.append(latency)

    metrics = classify_metrics(pairs)
    latencies.sort()
    metrics["decided_alone"] = decided_alone
    metrics["pct_handled_alone"] = decided_alone / len(rows)
    metrics["calls_saved"] = decided_alone
    metrics["escalation_errors"] = escalation_errors
    metrics["latency_p50_ms"] = latencies[len(latencies) // 2] if latencies else None
    metrics["latency_p95_ms"] = latencies[int(len(latencies) * 0.95)] if latencies else None
    return metrics


def main() -> None:
    temperature = json.loads(TEMPERATURE_PATH.read_text(encoding="utf-8"))["temperature"]
    sweep_rows = load_split_rows("sweep")
    print(f"Sweep split: {len(sweep_rows)} rows, temperature T={temperature}\n")

    ragas_default = ragas_only_baseline(sweep_rows, FAITHFULNESS_THRESHOLD)
    print(f"Baseline A - RAGAS-only @ existing threshold {FAITHFULNESS_THRESHOLD}:")
    print(f"  balanced_accuracy={ragas_default['balanced_accuracy']:.4f} "
          f"(approx CI {ragas_default.get('balanced_accuracy_ci_approx')}), errored={ragas_default['errored']}")
    for label in ("faithful", "unfaithful"):
        m = ragas_default[label]
        print(f"  {label}: precision={m['precision']} (CI {m['precision_ci']}), "
              f"recall={m['recall']} (CI {m['recall_ci']})")

    tuned_threshold, ragas_tuned = tune_ragas_threshold(sweep_rows)
    print(f"\nBaseline B - RAGAS-only, threshold tuned on sweep (t={tuned_threshold}):")
    print(f"  balanced_accuracy={ragas_tuned['balanced_accuracy']:.4f} "
          f"(approx CI {ragas_tuned.get('balanced_accuracy_ci_approx')}), errored={ragas_tuned['errored']}")
    for label in ("faithful", "unfaithful"):
        m = ragas_tuned[label]
        print(f"  {label}: precision={m['precision']} (CI {m['precision_ci']}), "
              f"recall={m['recall']} (CI {m['recall_ci']})")

    laya_only = laya_only_baseline(sweep_rows)
    print(f"\nBaseline C - Laya-only @ P(faithful) >= 0.5:")
    print(f"  balanced_accuracy={laya_only['balanced_accuracy']:.4f} "
          f"(approx CI {laya_only.get('balanced_accuracy_ci_approx')})")
    for label in ("faithful", "unfaithful"):
        m = laya_only[label]
        print(f"  {label}: precision={m['precision']} (CI {m['precision_ci']}), "
              f"recall={m['recall']} (CI {m['recall_ci']})")

    print(f"\nThreshold sweep rule: lowest t such that cascade balanced_accuracy "
          f">= {ragas_tuned['balanced_accuracy']:.4f} - {MAX_BALANCED_ACCURACY_DROP} "
          f"= {ragas_tuned['balanced_accuracy'] - MAX_BALANCED_ACCURACY_DROP:.4f}")

    curve = []
    chosen_t = None
    min_acceptable = ragas_tuned["balanced_accuracy"] - MAX_BALANCED_ACCURACY_DROP
    for t in THRESHOLD_GRID:
        m = simulate_cascade(sweep_rows, temperature, t)
        row = {
            "t": t, "balanced_accuracy": m["balanced_accuracy"],
            "pct_handled_alone": m["pct_handled_alone"], "calls_saved": m["calls_saved"],
            "escalation_errors": m["escalation_errors"],
            "latency_p50_ms": m["latency_p50_ms"], "latency_p95_ms": m["latency_p95_ms"],
        }
        curve.append(row)
        if chosen_t is None and m["balanced_accuracy"] is not None and m["balanced_accuracy"] >= min_acceptable:
            chosen_t = t

    for row in curve:
        row["chosen"] = (row["t"] == chosen_t)

    SWEEP_CURVE_PATH.write_text("\n".join(json.dumps(r) for r in curve) + "\n", encoding="utf-8")
    print(f"\nFull curve ({len(curve)} thresholds) written to {SWEEP_CURVE_PATH}")

    if chosen_t is None:
        print(f"\nNO THRESHOLD in [{THRESHOLD_GRID[0]}, {THRESHOLD_GRID[-1]}] meets the rule. "
              f"Not relaxing it - reporting no-threshold-met as the result.")
    else:
        chosen_row = next(r for r in curve if r["t"] == chosen_t)
        print(f"\nChosen t={chosen_t}: balanced_accuracy={chosen_row['balanced_accuracy']:.4f}, "
              f"handled alone={chosen_row['pct_handled_alone']:.1%} "
              f"({chosen_row['calls_saved']}/{len(sweep_rows)} calls saved), "
              f"latency p50={chosen_row['latency_p50_ms']:.1f}ms p95={chosen_row['latency_p95_ms']:.1f}ms, "
              f"escalation_errors={chosen_row['escalation_errors']}")


if __name__ == "__main__":
    main()

"""Step 4 follow-up (Laya cascade): paired McNemar comparisons and the
per-claim breakdown on the test split, replaying the same saved scores
laya_eval.py used - no new model calls, no re-tuning, test untouched
beyond reading its already-scored rows.
"""

import json
from math import comb
from pathlib import Path

from drift.diff import FAITHFULNESS_THRESHOLD
from redteam.laya_calibrate import CALIBRATION_OUT_PATH as TEMPERATURE_PATH
from redteam.laya_calibrate import apply_temperature
from redteam.laya_threshold_sweep import (
    classify_metrics,
    laya_predicted_label,
    load_split_rows,
    ragas_predicted_label,
)

ACCURACY_POINT_T = 0.80


def cascade_predicted_label(row: dict, temperature: float, threshold: float) -> str:
    p_cal = apply_temperature(row["p_faithful_raw"], temperature)
    if max(p_cal, 1 - p_cal) >= threshold:
        return laya_predicted_label(p_cal)
    if row["ragas_status"] != "completed":
        return "errored"
    return ragas_predicted_label(row["ragas_score"], FAITHFULNESS_THRESHOLD)


def exact_mcnemar_p(b: int, c: int) -> float:
    """Exact two-sided McNemar (binomial test on discordant pairs,
    p=0.5) - no scipy dependency: for symmetric p=0.5, doubling the
    lower tail sum is the standard exact two-sided result."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    lower_tail = sum(comb(n, i) for i in range(k + 1)) * (0.5 ** n)
    return min(1.0, 2 * lower_tail)


def mcnemar_compare(name_a: str, preds_a: list[str], name_b: str, preds_b: list[str], truth: list[str]) -> None:
    correct_a = [p == t for p, t in zip(preds_a, truth)]
    correct_b = [p == t for p, t in zip(preds_b, truth)]
    b = sum(1 for ca, cb in zip(correct_a, correct_b) if ca and not cb)  # A right, B wrong
    c = sum(1 for ca, cb in zip(correct_a, correct_b) if not ca and cb)  # A wrong, B right
    p = exact_mcnemar_p(b, c)
    print(f"{name_a} vs {name_b}: {name_a}-right/{name_b}-wrong={b}, {name_a}-wrong/{name_b}-right={c}, "
          f"discordant={b + c}, p={p:.4f}")


def main() -> None:
    temperature = json.loads(TEMPERATURE_PATH.read_text(encoding="utf-8"))["temperature"]
    test_rows = load_split_rows("test")
    truth = [r["intended_label"] for r in test_rows]

    ragas_preds = [ragas_predicted_label(r["ragas_score"], FAITHFULNESS_THRESHOLD) for r in test_rows]
    laya_preds = [laya_predicted_label(r["p_faithful_raw"]) for r in test_rows]
    cascade_preds = [cascade_predicted_label(r, temperature, ACCURACY_POINT_T) for r in test_rows]

    print(f"Test split: {len(test_rows)} rows\n")
    print("=== McNemar exact test (discordant pairs, two-sided) ===")
    mcnemar_compare("cascade@0.80", cascade_preds, "RAGAS@0.7", ragas_preds, truth)
    mcnemar_compare("cascade@0.80", cascade_preds, "Laya-only", laya_preds, truth)
    mcnemar_compare("Laya-only", laya_preds, "RAGAS@0.7", ragas_preds, truth)

    print("\n=== Per-claim breakdown ===")
    claim_ids = sorted({r["claim_id"] for r in test_rows})
    for claim_id in claim_ids:
        idx = [i for i, r in enumerate(test_rows) if r["claim_id"] == claim_id]
        claim_truth = [truth[i] for i in idx]
        print(f"\n{claim_id} (n={len(idx)}):")
        for name, preds in [("RAGAS@0.7", ragas_preds), ("Laya-only", laya_preds), ("cascade@0.80", cascade_preds)]:
            pairs = [(preds[i], claim_truth[j]) for j, i in enumerate(idx)]
            m = classify_metrics(pairs)
            ba = f"{m['balanced_accuracy']:.4f}" if m["balanced_accuracy"] is not None else "undefined (single class)"
            print(f"  {name}: balanced_accuracy={ba}")

    print("\n=== Latency (mean/p50/p95) ===")
    laya_lat = sorted(r["laya_latency_ms"] for r in test_rows)
    print(f"Laya per-row: mean={sum(laya_lat)/len(laya_lat):.1f}ms, "
          f"p50={laya_lat[len(laya_lat)//2]:.1f}ms, p95={laya_lat[int(len(laya_lat)*0.95)]:.1f}ms")

    cost_lat = sorted(r["laya_latency_ms"] for r in test_rows)  # cost point = Laya alone, always
    print(f"Cost point (t=0.50) per-row: mean={sum(cost_lat)/len(cost_lat):.1f}ms, "
          f"p50={cost_lat[len(cost_lat)//2]:.1f}ms, p95={cost_lat[int(len(cost_lat)*0.95)]:.1f}ms")

    acc_lat = []
    for r in test_rows:
        p_cal = apply_temperature(r["p_faithful_raw"], temperature)
        lat = r["laya_latency_ms"]
        if max(p_cal, 1 - p_cal) < ACCURACY_POINT_T:
            lat += r["ragas_latency_ms"]
        acc_lat.append(lat)
    acc_lat.sort()
    print(f"Accuracy point (t=0.80) per-row: mean={sum(acc_lat)/len(acc_lat):.1f}ms, "
          f"p50={acc_lat[len(acc_lat)//2]:.1f}ms, p95={acc_lat[int(len(acc_lat)*0.95)]:.1f}ms")


if __name__ == "__main__":
    main()

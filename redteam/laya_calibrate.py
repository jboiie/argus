"""Step 3.2 (Laya cascade): temperature refit on the calibration split
only, class-balanced. Same method as ../aegis's redteam/laya_calibrate.py
(class-balanced NLL grid search, 10-bin ECE before/after per class) - one
approach, applied separately per project's own score definition.

Score definition here: s_raw = p_faithful_raw (Laya's own P(faithful) for
the noul question, see redteam/laya_cascade.py). y=1 for intended_label
"faithful", y=0 for "unfaithful" - so s_raw already has the right
orientation (higher = more faithful = y=1) and needs no inversion, unlike
Aegis's s = P(attack) which it inverts to P(benign) after calibration.
"""

import json
import math
from pathlib import Path

from redteam.laya_cascade import EPS, _logit, _sigmoid

ROOT = Path(__file__).resolve().parent.parent
SCORES_PATH = ROOT / "data" / "laya_faithfulness_scores.jsonl"
CALIBRATION_OUT_PATH = ROOT / "data" / "laya_faithfulness_calibration.json"

N_BINS = 10
TEMPERATURE_GRID = [round(0.3 + 0.02 * i, 2) for i in range(int((3.0 - 0.3) / 0.02) + 1)]


def load_calibration_rows() -> list[dict]:
    rows = [json.loads(line) for line in SCORES_PATH.read_text(encoding="utf-8").splitlines()]
    return [r for r in rows if r["split"] == "calibration"]


def apply_temperature(p_raw: float, temperature: float) -> float:
    return _sigmoid(_logit(p_raw) / temperature)


def class_balanced_nll(rows: list[dict], temperature: float) -> float:
    n_faithful = sum(1 for r in rows if r["intended_label"] == "faithful")
    n_unfaithful = sum(1 for r in rows if r["intended_label"] == "unfaithful")
    total = 0.0
    for r in rows:
        y = 1 if r["intended_label"] == "faithful" else 0
        p = apply_temperature(r["p_faithful_raw"], temperature)
        p = min(max(p, EPS), 1 - EPS)
        nll = -math.log(p) if y == 1 else -math.log(1 - p)
        w = 0.5 / n_faithful if y == 1 else 0.5 / n_unfaithful
        total += w * nll
    return total


def fit_temperature(rows: list[dict]) -> float:
    best_t, best_loss = 1.0, float("inf")
    for t in TEMPERATURE_GRID:
        loss = class_balanced_nll(rows, t)
        if loss < best_loss:
            best_t, best_loss = t, loss
    return best_t


def compute_ece(rows: list[dict], temperature: float) -> dict:
    """Standard N_BINS-bin ECE on the combined set, plus the same bins'
    calibration gap attributed separately to faithful and unfaithful rows."""
    preds = [(apply_temperature(r["p_faithful_raw"], temperature),
              1 if r["intended_label"] == "faithful" else 0) for r in rows]
    bins: list[list[tuple[float, int]]] = [[] for _ in range(N_BINS)]
    for p, y in preds:
        idx = min(int(p * N_BINS), N_BINS - 1)
        bins[idx].append((p, y))

    n = len(preds)
    ece_combined = 0.0
    ece_faithful_num, n_faithful = 0.0, 0
    ece_unfaithful_num, n_unfaithful = 0.0, 0
    for b in bins:
        if not b:
            continue
        bin_conf = sum(p for p, _ in b) / len(b)
        bin_acc = sum(y for _, y in b) / len(b)
        gap = abs(bin_conf - bin_acc)
        ece_combined += (len(b) / n) * gap
        for p, y in b:
            if y == 1:
                ece_faithful_num += gap
                n_faithful += 1
            else:
                ece_unfaithful_num += gap
                n_unfaithful += 1

    return {
        "ece_combined": ece_combined,
        "ece_faithful": ece_faithful_num / n_faithful if n_faithful else None,
        "ece_unfaithful": ece_unfaithful_num / n_unfaithful if n_unfaithful else None,
        "n_faithful": n_faithful,
        "n_unfaithful": n_unfaithful,
    }


def main() -> None:
    rows = load_calibration_rows()
    n_faithful = sum(1 for r in rows if r["intended_label"] == "faithful")
    n_unfaithful = sum(1 for r in rows if r["intended_label"] == "unfaithful")
    print(f"Calibration split: {len(rows)} rows ({n_faithful} faithful, {n_unfaithful} unfaithful)")
    print("Class balance method: class-balanced weighting (0.5/n_class per row).")

    ece_before = compute_ece(rows, temperature=1.0)
    t_fitted = fit_temperature(rows)
    ece_after = compute_ece(rows, temperature=t_fitted)

    print(f"\nFitted temperature: T={t_fitted}")
    print(f"ECE before (T=1.0, Laya's shipped calibration): "
          f"combined={ece_before['ece_combined']:.4f}  "
          f"faithful={ece_before['ece_faithful']:.4f}  unfaithful={ece_before['ece_unfaithful']:.4f}")
    print(f"ECE after  (T={t_fitted}): "
          f"combined={ece_after['ece_combined']:.4f}  "
          f"faithful={ece_after['ece_faithful']:.4f}  unfaithful={ece_after['ece_unfaithful']:.4f}")

    faithful_worse = ece_after["ece_faithful"] > ece_before["ece_faithful"]
    unfaithful_worse = ece_after["ece_unfaithful"] > ece_before["ece_unfaithful"]
    if faithful_worse or unfaithful_worse:
        worse = []
        if faithful_worse:
            worse.append("faithful")
        if unfaithful_worse:
            worse.append("unfaithful")
        print(f"\nNOTE: ECE got WORSE after fitting for: {', '.join(worse)}. "
              "Do not describe Laya's confidence as calibrated for that class.")

    out = {
        "temperature": t_fitted,
        "class_balance_method": "class_balanced_weighting",
        "n_calibration_rows": len(rows),
        "n_faithful": n_faithful,
        "n_unfaithful": n_unfaithful,
        "score_definition": "s_raw = p_faithful_raw; calibrated = sigmoid(logit(s_raw)/T)",
        "ece_before": ece_before,
        "ece_after": ece_after,
        "temperature_grid_min": min(TEMPERATURE_GRID),
        "temperature_grid_max": max(TEMPERATURE_GRID),
    }
    CALIBRATION_OUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"\nCalibration result written to {CALIBRATION_OUT_PATH}")


if __name__ == "__main__":
    main()

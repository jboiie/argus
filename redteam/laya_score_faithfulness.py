"""Step 3.1 (Laya cascade): score every row (calibration + sweep + test +
live) with Laya once, save raw P(faithful) + per-row latency. Downstream
scripts (laya_calibrate.py, laya_threshold_sweep.py) reuse these saved
scores rather than re-invoking Laya - the cascade at evaluation time is
simulated from saved numbers, not re-run live (see PROJECT_DESC.md).

Runs in the laya-bench conda env (has the `laya` package; the main argus
env does not). No RAGAS/Groq/Gemini imports here - this script only reads
data/faithfulness_variants.jsonl and calls Laya.
"""

import json
import os
from pathlib import Path

from redteam.laya_cascade import score_faithfulness

ROOT = Path(__file__).resolve().parent.parent
VARIANTS_PATH = ROOT / "data" / "faithfulness_variants.jsonl"
SCORES_PATH = ROOT / "data" / "laya_faithfulness_scores.jsonl"

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")


def main() -> None:
    rows = [json.loads(line) for line in VARIANTS_PATH.read_text(encoding="utf-8").splitlines()]
    print(f"Scoring {len(rows)} rows with Laya...")

    results = []
    for i, row in enumerate(rows):
        result = score_faithfulness(row["question"], row["context_claims"], row["answer"])
        results.append({
            "row_id": row["row_id"], "claim_id": row["claim_id"], "variant_type": row["variant_type"],
            "split": row["split"], "intended_label": row["intended_label"],
            "p_faithful_raw": result.p_faithful_raw, "latency_ms": result.latency_ms,
        })
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(rows)} scored")

    SCORES_PATH.write_text("\n".join(json.dumps(r) for r in results) + "\n", encoding="utf-8")

    latencies = sorted(r["latency_ms"] for r in results)
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    print(f"\nWrote {len(results)} Laya scores to {SCORES_PATH}")
    print(f"Latency: p50={p50:.1f}ms, p95={p95:.1f}ms")


if __name__ == "__main__":
    main()

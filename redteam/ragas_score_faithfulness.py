"""Step 3.1 (Laya cascade): score sweep + test + live rows with RAGAS
Faithfulness once (the fixed judge config - see PROJECT_DESC.md's Step 1
audit), save score/status/latency per row. Not calibration - the
calibration split only needs Laya's own score (see laya_calibrate.py).

Runs in the argus conda env (has ragas/deepeval/groq; laya-bench does not).
Errored rows are saved with check_status="errored" and score=None - never
coerced into a faithful/unfaithful label, matching drift/diff.py's own
convention throughout this repo.
"""

import asyncio
import json
import os
import time
from pathlib import Path

from agent.reference_agent import load_ground_truth
from drift.diff import check_faithfulness

ROOT = Path(__file__).resolve().parent.parent
VARIANTS_PATH = ROOT / "data" / "faithfulness_variants.jsonl"
SCORES_PATH = ROOT / "data" / "ragas_faithfulness_scores.jsonl"

SCORED_SPLITS = {"sweep", "test", None}  # None = live rows (split field is null)


async def main() -> None:
    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY not set - skipping.")
        return

    _, policies = load_ground_truth()
    claims_by_id = {p["id"]: p["claim"] for p in policies}

    rows = [json.loads(line) for line in VARIANTS_PATH.read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if r["split"] in SCORED_SPLITS]
    print(f"Scoring {len(rows)} rows (sweep + test + live) with RAGAS Faithfulness...")

    results = []
    for i, row in enumerate(rows):
        claim = claims_by_id.get(row["claim_id"], "; ".join(row["context_claims"]))
        start = time.perf_counter()
        check = await check_faithfulness(
            row["question"], row["claim_id"] or row["topic"], claim,
            row["answer"], context_claims=row["context_claims"],
        )
        latency_ms = (time.perf_counter() - start) * 1000
        results.append({
            "row_id": row["row_id"], "claim_id": row["claim_id"], "variant_type": row["variant_type"],
            "split": row["split"], "intended_label": row["intended_label"],
            "score": check.score, "check_status": check.check_status, "latency_ms": latency_ms,
        })
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(rows)} scored")

    SCORES_PATH.write_text("\n".join(json.dumps(r) for r in results) + "\n", encoding="utf-8")

    errored = sum(1 for r in results if r["check_status"] == "errored")
    completed = [r for r in results if r["check_status"] == "completed"]
    latencies = sorted(r["latency_ms"] for r in results)
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    print(f"\nWrote {len(results)} RAGAS scores to {SCORES_PATH}")
    print(f"Completed: {len(completed)}, errored: {errored}")
    print(f"Latency: p50={p50:.1f}ms, p95={p95:.1f}ms")


if __name__ == "__main__":
    asyncio.run(main())

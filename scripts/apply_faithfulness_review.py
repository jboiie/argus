"""One-time application of the user's manual review of
data/faithfulness_review.md (2026-09-27) to data/faithfulness_variants.jsonl.

Kept as a script rather than an ad-hoc edit so the review decisions are
reproducible and auditable - each row id below traces back to a specific
line in the user's review reply, not a silent hand-edit of the data file.

Labeling rule applied (see PROJECT_DESC.md's "Laya cascade" section):
- Faithful: everything the answer states is supported by the claims.
  Omitting other claims is fine. Generic courtesy lines are fine.
- Unfaithful: adds a fact, condition, number, promise, or process not in
  the claims, or makes a blanket statement contradicting another claim.
- Dropped: borderline (speculation about future changes, vague hedges,
  outcomes borrowed from another topic).

Checker bugs this review surfaced (not re-run, noted for the record): the
LLM substance check treated omission as unfaithfulness (most of the 39
faithful_paraphrase flags were this, not real additions); the stale_number
regex missed number WORDS ("two" vs "one" has no digits to compare); the
one unsupported_addition flag was actually a correct row.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VARIANTS_PATH = ROOT / "data" / "faithfulness_variants.jsonl"

FLIP_TO_UNFAITHFUL = {
    "policy_refund_window__faithful_paraphrase__r0__detailed",
    "policy_refund_window__faithful_paraphrase__r3__detailed",
    "policy_refund_receipt__faithful_paraphrase__r1__conversational",
    "policy_refund_sale_items__faithful_paraphrase__r1__detailed",
    "policy_refund_sale_items__faithful_paraphrase__r3__detailed",
    "policy_shipping_domestic_cost__faithful_paraphrase__r0__conversational",
    "policy_shipping_domestic_cost__faithful_paraphrase__r0__detailed",
    "policy_shipping_domestic_cost__faithful_paraphrase__r1__conversational",
    "policy_shipping_domestic_cost__faithful_paraphrase__r1__detailed",
    "policy_shipping_domestic_cost__faithful_paraphrase__r2__detailed",
    "policy_shipping_domestic_cost__faithful_paraphrase__r3__detailed",
    "policy_shipping_international__faithful_paraphrase__r1__detailed",
    "policy_warranty_duration__faithful_paraphrase__r3__conversational",
    "policy_discount_stacking__faithful_paraphrase__r0__detailed",
    "policy_discount_stacking__faithful_paraphrase__r1__detailed",
    "policy_discount_validity__faithful_paraphrase__r0__detailed",
    "policy_discount_validity__faithful_paraphrase__r2__detailed",
}

DROP = {
    "policy_refund_window__faithful_paraphrase__r2__detailed",
    "policy_refund_processing_time__faithful_paraphrase__r2__detailed",
    "policy_shipping_free_threshold__faithful_paraphrase__r1__detailed",
    "policy_shipping_delivery_time__faithful_paraphrase__r1__detailed",
    "policy_shipping_delivery_time__faithful_paraphrase__r2__detailed",
    "policy_shipping_international__faithful_paraphrase__r1__conversational",
    "policy_shipping_international__faithful_paraphrase__r2__conversational",
    "policy_shipping_international__faithful_paraphrase__r2__detailed",
    "policy_shipping_international__faithful_paraphrase__r3__detailed",
    "policy_warranty_duration__faithful_paraphrase__r0__detailed",
    "policy_warranty_duration__faithful_paraphrase__r2__detailed",
    "policy_warranty_duration__faithful_paraphrase__r3__detailed",
    "policy_cancellation_shipped__faithful_paraphrase__r1__detailed",
    "policy_cancellation_shipped__faithful_paraphrase__r2__detailed",
    "policy_cancellation_shipped__faithful_paraphrase__r3__conversational",
    "policy_cancellation_shipped__faithful_paraphrase__r3__detailed",
    "policy_discount_stacking__faithful_paraphrase__r2__conversational",
    "policy_discount_validity__contradicted_claim__short",
    "policy_discount_validity__contradicted_claim__conversational",
    "policy_discount_validity__contradicted_claim__detailed",
}


def apply(rows: list[dict]) -> list[dict]:
    out = []
    flipped = 0
    dropped = 0
    live_labeled = 0
    for row in rows:
        if row["row_id"] in DROP:
            dropped += 1
            continue
        if row["row_id"] in FLIP_TO_UNFAITHFUL:
            assert row["intended_label"] == "faithful", row["row_id"]
            row["intended_label"] = "unfaithful"
            flipped += 1
        if row["variant_type"] == "live_agent":
            assert row["intended_label"] == "unknown", row["row_id"]
            row["intended_label"] = "faithful"
            live_labeled += 1
        out.append(row)

    assert flipped == len(FLIP_TO_UNFAITHFUL), flipped
    assert dropped == len(DROP), dropped
    assert live_labeled == 20, live_labeled
    return out


def main() -> None:
    rows = [json.loads(line) for line in VARIANTS_PATH.read_text(encoding="utf-8").splitlines()]
    before = len(rows)
    rows = apply(rows)
    VARIANTS_PATH.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    print(f"Rows: {before} -> {len(rows)} ({len(DROP)} dropped, {len(FLIP_TO_UNFAITHFUL)} flipped to unfaithful, 20 live rows labeled faithful)")

    variant_rows = [r for r in rows if r["variant_type"] != "live_agent"]
    live_rows = [r for r in rows if r["variant_type"] == "live_agent"]

    by_label: dict[str, int] = {}
    for r in variant_rows:
        by_label[r["intended_label"]] = by_label.get(r["intended_label"], 0) + 1
    print(f"\nFinal counts (variants only, excludes {len(live_rows)} live rows):")
    for label, count in sorted(by_label.items()):
        print(f"  {label}: {count}")

    by_split_label: dict[tuple[str, str], int] = {}
    for r in variant_rows:
        key = (r["split"], r["intended_label"])
        by_split_label[key] = by_split_label.get(key, 0) + 1
    print("\nBy split:")
    for split in ["calibration", "sweep", "test"]:
        f = by_split_label.get((split, "faithful"), 0)
        u = by_split_label.get((split, "unfaithful"), 0)
        print(f"  {split}: {f} faithful / {u} unfaithful ({f + u} total)")

    by_claim: dict[str, int] = {}
    for r in variant_rows:
        by_claim[r["claim_id"]] = by_claim.get(r["claim_id"], 0) + 1
    print("\nRows per claim:")
    for claim_id, count in sorted(by_claim.items()):
        print(f"  {claim_id}: {count}")

    print(f"\nLive agent rows: {len(live_rows)}, all labeled faithful (reported separately, not pooled into metrics).")


if __name__ == "__main__":
    main()

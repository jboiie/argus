"""Step 2 (Laya cascade): LLM-generated faithful/unfaithful variants per
policy claim, for the hand-labeled faithfulness set the cascade's threshold
is fit and evaluated against. See PROJECT_DESC.md's "Laya cascade" section.

Deliberately NOT drift/staged_injection.py (that module is the Step 19
git-history staleness demo - a single hardcoded price edit - and has no
paraphrase/corruption generation at all). Deliberately NOT string
templates either: every variant is produced by the same Groq judge model
this repo already uses (redteam/groq_model.py), so a "stale number" or
"fabricated exception" row reads like something an LLM agent actually
said, not a fill-in-the-blank sentence.

Row shape matches what the cascade will see at check time: question +
every claim under that topic (context_claims) + one answer - the same
multi-claim-context requirement drift/diff.py::check_faithfulness already
documents.
"""

import asyncio
import json
import os
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path

from pydantic import BaseModel

from agent.reference_agent import ROOT, ask_async, load_ground_truth
from drift.sampler import _faithfulness_question
from redteam.groq_model import GroqModel

DATA_DIR = ROOT / "data"
VARIANTS_PATH = DATA_DIR / "faithfulness_variants.jsonl"
REVIEW_PATH = DATA_DIR / "faithfulness_review.md"
SPLITS_PATH = DATA_DIR / "faithfulness_splits.json"

# Each variant type's rewrite instruction, and whether the result is meant
# to be faithful or unfaithful to the original claim. Instructions are
# deliberately specific (not "make this wrong") so the model produces a
# realistic, single, clean corruption rather than several stacked at once.
VARIANT_TYPES = {
    "faithful_paraphrase": (
        "Rewrite the claim in different words, keeping its meaning and "
        "every detail fully intact and accurate. Do not add, remove, or "
        "change any fact."
    ),
    "stale_number": (
        "Rewrite the claim but change exactly one number in it (a "
        "duration, price, percentage, or count) to a different, "
        "plausible-but-wrong value. Keep everything else accurate."
    ),
    "fabricated_exception": (
        "Rewrite the claim but add a fabricated exception or condition "
        "that is not part of the original claim (an extra requirement, "
        "an excluded category, or a special case). The exception must be "
        "invented, not real."
    ),
    "contradicted_claim": (
        "Rewrite the claim so it states the opposite, or a materially "
        "contradictory version, of what it actually says."
    ),
    "unsupported_addition": (
        "Rewrite the claim, keeping its original content accurate, but "
        "append one extra specific detail or promise that is not "
        "supported by the original claim at all - something invented and "
        "added on."
    ),
}
INTENDED_LABEL = {
    "faithful_paraphrase": "faithful",
    "stale_number": "unfaithful",
    "fabricated_exception": "unfaithful",
    "contradicted_claim": "unfaithful",
    "unsupported_addition": "unfaithful",
}
STYLE_NAMES = ["short", "conversational", "detailed"]

# By claim, not by topic - so paraphrase variants of the same claim never
# cross a split boundary. Hand-assigned (not random) to keep every 2-claim
# topic's pair spread across two different splits rather than clustering
# in one, and to land on 4/6/4 exactly. See PROJECT_DESC.md for the
# per-topic reasoning.
CLAIM_SPLITS = {
    "policy_refund_window": "calibration",
    "policy_shipping_domestic_cost": "calibration",
    "policy_warranty_duration": "calibration",
    "policy_discount_stacking": "calibration",
    "policy_refund_receipt": "sweep",
    "policy_refund_sale_items": "sweep",
    "policy_shipping_free_threshold": "sweep",
    "policy_shipping_delivery_time": "sweep",
    "policy_cancellation_window": "sweep",
    "policy_discount_validity": "sweep",
    "policy_refund_processing_time": "test",
    "policy_shipping_international": "test",
    "policy_warranty_exclusions": "test",
    "policy_cancellation_shipped": "test",
}

DEDUPE_SIMILARITY_THRESHOLD = 0.92
LIVE_SAMPLES_PER_TOPIC = 4


class VariantStyles(BaseModel):
    short: str
    conversational: str
    detailed: str


@dataclass
class VariantRow:
    row_id: str
    claim_id: str
    topic: str
    variant_type: str
    style: str
    intended_label: str
    split: str
    question: str
    context_claims: list[str]
    answer: str


def _prompt(instruction: str, claim: str, question: str) -> str:
    return (
        f"{instruction}\n\nOriginal claim: {claim}\n\n"
        f"Then phrase that same rewritten claim three different ways, as "
        f"if a customer support agent said it in answer to \"{question}\":\n"
        f"- short: one brief sentence.\n"
        f"- conversational: a friendly, casual sentence or two.\n"
        f"- detailed: a fuller, more formal explanation, 2-3 sentences.\n"
        f"Each of the three must express the SAME (already-rewritten) "
        f"content, just in a different register."
    )


async def generate_variants(policy: dict, context_claims: list[str], model: GroqModel) -> list[VariantRow]:
    """One Groq call per variant type (5 calls/claim), each returning all
    three answer styles at once - keeps the same corrupted content across
    styles rather than re-rolling the corruption per style."""
    question = _faithfulness_question(policy["topic"])
    split = CLAIM_SPLITS[policy["id"]]
    rows = []
    for variant_type, instruction in VARIANT_TYPES.items():
        prompt = _prompt(instruction, policy["claim"], question)
        styles: VariantStyles = await model.a_generate(prompt, schema=VariantStyles)
        for style in STYLE_NAMES:
            rows.append(VariantRow(
                row_id=f"{policy['id']}__{variant_type}__{style}",
                claim_id=policy["id"], topic=policy["topic"], variant_type=variant_type,
                style=style, intended_label=INTENDED_LABEL[variant_type], split=split,
                question=question, context_claims=context_claims, answer=getattr(styles, style),
            ))
    return rows


def dedupe(rows: list[VariantRow], threshold: float = DEDUPE_SIMILARITY_THRESHOLD) -> tuple[list[VariantRow], int]:
    """Drops a row if its answer text is a near-duplicate (SequenceMatcher
    ratio >= threshold) of an already-kept row's answer, compared within
    the same claim (a near-duplicate answer under a different claim is a
    coincidence, not redundancy). Keeps the first occurrence in input
    order. Returns (kept_rows, removed_count)."""
    kept: list[VariantRow] = []
    kept_by_claim: dict[str, list[str]] = {}
    removed = 0
    for row in rows:
        normalized = " ".join(row.answer.lower().split())
        existing = kept_by_claim.setdefault(row.claim_id, [])
        if any(SequenceMatcher(None, normalized, other).ratio() >= threshold for other in existing):
            removed += 1
            continue
        existing.append(normalized)
        kept.append(row)
    return kept, removed


async def generate_live_samples(n_per_topic: int = LIVE_SAMPLES_PER_TOPIC) -> list[dict]:
    """~20 real agent answers, labeled unknown for manual review - not
    synthetic like the variants above. Reuses drift/sampler.py's own
    faithfulness question set (one question per topic), asked repeatedly
    since the agent isn't deterministic across calls."""
    _, policies = load_ground_truth()
    topics: dict[str, list[dict]] = {}
    for policy in policies:
        topics.setdefault(policy["topic"], []).append(policy)

    rows = []
    for topic, claims in topics.items():
        question = _faithfulness_question(topic)
        context_claims = [c["claim"] for c in claims]
        for i in range(n_per_topic):
            answer = await ask_async(question)
            rows.append({
                "row_id": f"live__{topic}__{i}", "claim_id": None, "topic": topic,
                "variant_type": "live_agent", "style": None, "intended_label": "unknown",
                "split": None, "question": question, "context_claims": context_claims,
                "answer": answer,
            })
    return rows


def write_review_md(variant_rows: list[VariantRow], live_rows: list[dict], path: Path) -> None:
    lines = [
        "# Faithfulness review set",
        "",
        "Reply with row ids to flip (wrong intended_label) or drop (bad generation).",
        "",
        "| row_id | claim_id | topic | variant_type | intended_label | question | claims | answer |",
        "|---|---|---|---|---|---|---|---|",
    ]

    def _cell(text: str) -> str:
        return text.replace("|", "\\|").replace("\n", " ")

    for row in variant_rows:
        claims_cell = "; ".join(row.context_claims)
        lines.append(
            f"| {row.row_id} | {row.claim_id} | {row.topic} | {row.variant_type} | "
            f"{row.intended_label} | {_cell(row.question)} | {_cell(claims_cell)} | {_cell(row.answer)} |"
        )
    for row in live_rows:
        claims_cell = "; ".join(row["context_claims"])
        lines.append(
            f"| {row['row_id']} | (none) | {row['topic']} | live_agent | "
            f"unknown | {_cell(row['question'])} | {_cell(claims_cell)} | {_cell(row['answer'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _selftest_dedupe() -> None:
    """Pure-logic check, no API calls - runs before any Groq budget is
    spent so a broken dedupe doesn't silently corrupt the generated set."""
    def row(rid: str, claim: str, answer: str) -> VariantRow:
        return VariantRow(rid, claim, "t", "vt", "short", "faithful", "calibration", "q", ["c"], answer)

    rows = [
        row("a", "claim_1", "Items can be returned within 30 days of delivery."),
        row("b", "claim_1", "Items can be returned within 30 days of delivery!"),  # near-dup of a
        row("c", "claim_1", "Refunds are only available for defective items."),  # distinct
        row("d", "claim_2", "Items can be returned within 30 days of delivery."),  # same text, different claim - kept
    ]
    kept, removed = dedupe(rows, threshold=0.92)
    kept_ids = {r.row_id for r in kept}
    assert kept_ids == {"a", "c", "d"}, kept_ids
    assert removed == 1, removed
    print("dedupe self-test passed.")


async def main() -> None:
    _selftest_dedupe()

    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY not set - skipping generation.")
        return

    _, policies = load_ground_truth()
    topics: dict[str, list[dict]] = {}
    for policy in policies:
        topics.setdefault(policy["topic"], []).append(policy)

    model = GroqModel()
    all_rows: list[VariantRow] = []
    for topic, claims in topics.items():
        context_claims = [c["claim"] for c in claims]
        for policy in claims:
            rows = await generate_variants(policy, context_claims, model)
            all_rows.extend(rows)
            print(f"  generated {len(rows)} variants for {policy['id']} ({topic})")

    expected_before_dedupe = len(policies) * len(VARIANT_TYPES) * len(STYLE_NAMES)
    assert len(all_rows) == expected_before_dedupe, (len(all_rows), expected_before_dedupe)

    kept, removed = dedupe(all_rows)
    print(f"\nDeduped: {removed} near-duplicate rows removed, {len(kept)} kept "
          f"(of {len(all_rows)} generated).")

    print("\nGenerating ~20 live agent samples (unknown label)...")
    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set - skipping live agent samples.")
        live_rows = []
    else:
        live_rows = await generate_live_samples()

    DATA_DIR.mkdir(exist_ok=True)
    with VARIANTS_PATH.open("w", encoding="utf-8") as f:
        for row in kept:
            f.write(json.dumps(asdict(row)) + "\n")
        for row in live_rows:
            f.write(json.dumps(row) + "\n")
    SPLITS_PATH.write_text(json.dumps(CLAIM_SPLITS, indent=2) + "\n", encoding="utf-8")
    write_review_md(kept, live_rows, REVIEW_PATH)

    print(f"\nWrote {len(kept)} variant rows + {len(live_rows)} live rows to {VARIANTS_PATH}")
    print(f"Wrote splits ({sum(1 for v in CLAIM_SPLITS.values() if v=='calibration')} cal / "
          f"{sum(1 for v in CLAIM_SPLITS.values() if v=='sweep')} sweep / "
          f"{sum(1 for v in CLAIM_SPLITS.values() if v=='test')} test) to {SPLITS_PATH}")
    print(f"Wrote review doc to {REVIEW_PATH}")

    print("\nCounts per variant_type:")
    by_type: dict[str, int] = {}
    for row in kept:
        by_type[row.variant_type] = by_type.get(row.variant_type, 0) + 1
    for vt, count in sorted(by_type.items()):
        print(f"  {vt}: {count}")

    print("\nCounts per claim:")
    by_claim: dict[str, int] = {}
    for row in kept:
        by_claim[row.claim_id] = by_claim.get(row.claim_id, 0) + 1
    for claim_id, count in sorted(by_claim.items()):
        print(f"  {claim_id}: {count}")


if __name__ == "__main__":
    asyncio.run(main())

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
import re
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

# Faithful-side rewrite instructions. Multiple rounds (matching the count
# of unfaithful types below) so faithful and unfaithful variants land in
# roughly equal counts per claim, not 1 faithful type vs. 4 unfaithful
# types - an unbalanced set rewards a classifier for always guessing
# "unfaithful". Each round asks for the same full-fidelity paraphrase in a
# differently-worded instruction, for lexical variety rather than 4 near-
# identical rewrites (dedupe() still catches any real duplicates).
FAITHFUL_PARAPHRASE_INSTRUCTIONS = [
    (
        "Rewrite the claim in different words, keeping its meaning and "
        "every detail fully intact and accurate. Do not add, remove, or "
        "change any fact."
    ),
    (
        "Rewrite the claim using noticeably different vocabulary and "
        "sentence structure than a plain restatement, keeping its meaning "
        "and every detail fully intact and accurate. Do not add, remove, "
        "or change any fact."
    ),
    (
        "Rewrite the claim as a brief FAQ-style answer, keeping its "
        "meaning and every detail fully intact and accurate. Do not add, "
        "remove, or change any fact."
    ),
    (
        "Rewrite the claim as if a different support agent were "
        "explaining it from scratch, keeping its meaning and every detail "
        "fully intact and accurate. Do not add, remove, or change any fact."
    ),
]

# Unfaithful-side rewrite instructions. Deliberately specific (not "make
# this wrong") so the model produces a realistic, single, clean corruption
# rather than several stacked at once.
UNFAITHFUL_VARIANT_TYPES = {
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
    """One Groq call per faithful-paraphrase round + per unfaithful type
    (len(FAITHFUL_PARAPHRASE_INSTRUCTIONS) + len(UNFAITHFUL_VARIANT_TYPES)
    calls/claim), each returning all three answer styles at once - keeps
    the same rewritten content across styles rather than re-rolling per
    style."""
    question = _faithfulness_question(policy["topic"])
    split = CLAIM_SPLITS[policy["id"]]
    claim = policy["claim"]
    rows = []

    for round_idx, instruction in enumerate(FAITHFUL_PARAPHRASE_INSTRUCTIONS):
        prompt = _prompt(instruction, claim, question)
        styles: VariantStyles = await model.a_generate(prompt, schema=VariantStyles)
        for style in STYLE_NAMES:
            rows.append(VariantRow(
                row_id=f"{policy['id']}__faithful_paraphrase__r{round_idx}__{style}",
                claim_id=policy["id"], topic=policy["topic"], variant_type="faithful_paraphrase",
                style=style, intended_label="faithful", split=split,
                question=question, context_claims=context_claims, answer=getattr(styles, style),
            ))

    for variant_type, instruction in UNFAITHFUL_VARIANT_TYPES.items():
        prompt = _prompt(instruction, claim, question)
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


_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def check_stale_number(claim: str, answer: str) -> tuple[bool, str | None]:
    """Passes only if the answer contains at least one number absent from
    the original claim - i.e. the intended corruption actually happened."""
    claim_numbers = set(_NUMBER_RE.findall(claim))
    answer_numbers = set(_NUMBER_RE.findall(answer))
    if answer_numbers.issubset(claim_numbers):
        return False, f"no differing number found (claim numbers={sorted(claim_numbers)}, answer numbers={sorted(answer_numbers)})"
    return True, None


def check_faithful_paraphrase_numbers(context_claims: list[str], answer: str) -> tuple[bool, str | None]:
    """Deterministic half of the faithful_paraphrase check: passes only if
    the answer introduces no number absent from the topic's own claims.

    A word-overlap version of this ("no content word absent from the
    claims") was tried and dropped - on a real run it flagged 136/162
    (84%) of faithful_paraphrase rows, almost all harmless synonyms
    ("send back" for "return", "full refund" for "refund", "arrival" for
    "delivery"). Literal token overlap can't tell a synonym from a real
    unsupported addition, so that half of the check moved to
    check_substance's LLM prompt instead (see run_automated_checks) -
    a disclosed deviation from generating this only via literal text
    matching, kept only for numbers where literal matching is reliable."""
    context_numbers: set[str] = set()
    for claim in context_claims:
        context_numbers |= set(_NUMBER_RE.findall(claim))
    extra_numbers = set(_NUMBER_RE.findall(answer)) - context_numbers
    if extra_numbers:
        return False, f"answer contains number(s) not in claims: {sorted(extra_numbers)}"
    return True, None


class SubstanceCheck(BaseModel):
    matches_intent: bool
    reason: str


# Separate from RAGAS Faithfulness (drift/diff.py) and from the variant
# generator's own prompt - a distinct short check asking only "did the
# intended transformation actually happen", not "is this faithful".
_SUBSTANCE_CHECK_PROMPTS = {
    "contradicted_claim": (
        "ORIGINAL CLAIM: {claim}\n\nANSWER: {answer}\n\n"
        "Does the ANSWER state something that materially contradicts or is "
        "the logical opposite of the ORIGINAL CLAIM (not just phrased "
        "differently while saying the same thing)? Set matches_intent=true "
        "if it is a genuine contradiction, false if it does not actually "
        "contradict the claim. Give a one-sentence reason."
    ),
    "fabricated_exception": (
        "ORIGINAL CLAIM: {claim}\n\nANSWER: {answer}\n\n"
        "Does the ANSWER add an exception, condition, or qualifier that is "
        "NOT present in the ORIGINAL CLAIM? Set matches_intent=true if a "
        "new exception or condition was genuinely added, false if no such "
        "exception is present. Give a one-sentence reason."
    ),
    "unsupported_addition": (
        "ORIGINAL CLAIM: {claim}\n\nANSWER: {answer}\n\n"
        "Does the ANSWER include an extra specific detail, promise, or "
        "fact beyond what the ORIGINAL CLAIM states? Set "
        "matches_intent=true if a genuine unsupported addition is "
        "present, false if the answer sticks to only what the claim "
        "says. Give a one-sentence reason."
    ),
    "faithful_paraphrase": (
        "ORIGINAL CLAIM(S): {claim}\n\nANSWER: {answer}\n\n"
        "Does the ANSWER stay fully faithful to the ORIGINAL CLAIM(S) - "
        "i.e. it does NOT introduce any specific detail, term, exception, "
        "or promise that isn't supported by them? Harmless rewordings and "
        "synonyms that mean the same thing (e.g. \"send it back\" for "
        "\"return\", \"full refund\" for \"refund\") are fine and must NOT "
        "be flagged - only genuinely new, unsupported information counts. "
        "Set matches_intent=true if the answer is faithful with no "
        "unsupported additions, false if it adds something unsupported. "
        "Give a one-sentence reason."
    ),
}


async def check_substance(variant_type: str, claim: str, answer: str, model: GroqModel) -> tuple[bool, str]:
    prompt = _SUBSTANCE_CHECK_PROMPTS[variant_type].format(claim=claim, answer=answer)
    result: SubstanceCheck = await model.a_generate(prompt, schema=SubstanceCheck)
    return result.matches_intent, result.reason


async def run_automated_checks(
    rows: list[VariantRow], claims_by_id: dict[str, str], model: GroqModel
) -> dict[str, str]:
    """Returns {row_id: reason} for rows that fail their variant type's
    consistency check. Advisory only - nothing is dropped here, the
    caller puts flagged rows in the review doc for manual judgment."""
    flagged: dict[str, str] = {}
    for row in rows:
        if row.variant_type == "stale_number":
            ok, reason = check_stale_number(claims_by_id[row.claim_id], row.answer)
            if not ok:
                flagged[row.row_id] = reason
            continue

        if row.variant_type == "faithful_paraphrase":
            ok, reason = check_faithful_paraphrase_numbers(row.context_claims, row.answer)
            if not ok:
                flagged[row.row_id] = reason
                continue
            claim_text = "; ".join(row.context_claims)
        else:
            claim_text = claims_by_id[row.claim_id]

        try:
            ok, reason = await check_substance(row.variant_type, claim_text, row.answer, model)
        except Exception as exc:
            # A judge-model hiccup (e.g. gpt-oss-20b occasionally leaks its
            # full reasoning text past reasoning_format=hidden, which
            # Groq's strict-schema parse then rejects) shouldn't crash the
            # whole batch - flag the row so a human looks at it instead of
            # silently skipping it.
            print(f"  (substance check errored for {row.row_id}: {type(exc).__name__}: {exc})")
            ok, reason = False, f"automated check errored: {type(exc).__name__}: {exc}"
        if not ok:
            flagged[row.row_id] = reason
    return flagged


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


_ROW_HEADER = "| row_id | claim_id | topic | variant_type | intended_label | question | claims | answer |"
_ROW_SEP = "|---|---|---|---|---|---|---|---|"


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _row_line(row: VariantRow) -> str:
    claims_cell = "; ".join(row.context_claims)
    return (
        f"| {row.row_id} | {row.claim_id} | {row.topic} | {row.variant_type} | "
        f"{row.intended_label} | {_cell(row.question)} | {_cell(claims_cell)} | {_cell(row.answer)} |"
    )


def write_review_md(
    variant_rows: list[VariantRow], live_rows: list[dict], flagged: dict[str, str], path: Path
) -> None:
    """Flagged-by-automated-checks rows first (with their reason), then
    the rest grouped by variant type, then the live-agent answers last -
    a flagged row appears only once, in the flagged section."""
    lines = [
        "# Faithfulness review set",
        "",
        "Reply with row ids to flip (wrong intended_label) or drop (bad generation).",
        "",
        "## Flagged by automated checks",
        "",
    ]

    flagged_rows = [r for r in variant_rows if r.row_id in flagged]
    if flagged_rows:
        lines.append("| row_id | claim_id | topic | variant_type | intended_label | reason | question | claims | answer |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for row in flagged_rows:
            claims_cell = "; ".join(row.context_claims)
            lines.append(
                f"| {row.row_id} | {row.claim_id} | {row.topic} | {row.variant_type} | "
                f"{row.intended_label} | {_cell(flagged[row.row_id])} | {_cell(row.question)} | "
                f"{_cell(claims_cell)} | {_cell(row.answer)} |"
            )
    else:
        lines.append("(none)")
    lines.append("")

    by_type: dict[str, list[VariantRow]] = {}
    for row in variant_rows:
        if row.row_id not in flagged:
            by_type.setdefault(row.variant_type, []).append(row)

    for variant_type in ["faithful_paraphrase", *UNFAITHFUL_VARIANT_TYPES]:
        rows = by_type.get(variant_type, [])
        lines.append(f"## {variant_type}")
        lines.append("")
        lines.append(_ROW_HEADER)
        lines.append(_ROW_SEP)
        for row in rows:
            lines.append(_row_line(row))
        lines.append("")

    lines.append("## Live agent answers (unknown label)")
    lines.append("")
    lines.append(_ROW_HEADER)
    lines.append(_ROW_SEP)
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


def _selftest_checks() -> None:
    """Pure-logic check for the deterministic (numbers-only) halves of the
    consistency checks - no API calls, runs before any Groq budget is
    spent. The "specific term" half of faithful_paraphrase requires the
    LLM substance check (check_substance) and isn't covered here."""
    ok, reason = check_stale_number("Items can be returned within 30 days.", "Items can be returned within 45 days.")
    assert ok, reason
    ok, reason = check_stale_number("Items can be returned within 30 days.", "Items can be returned within 30 days.")
    assert not ok

    ok, reason = check_faithful_paraphrase_numbers(
        ["Items can be returned within 30 days."], "You can return items within 30 days.")
    assert ok, reason
    ok, reason = check_faithful_paraphrase_numbers(
        ["Items can be returned within 30 days."], "You can return items within 45 days.")
    assert not ok
    print("automated-check self-test passed.")


async def main() -> None:
    _selftest_dedupe()
    _selftest_checks()

    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY not set - skipping generation.")
        return

    _, policies = load_ground_truth()
    claims_by_id = {p["id"]: p["claim"] for p in policies}
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

    calls_per_claim = len(FAITHFUL_PARAPHRASE_INSTRUCTIONS) + len(UNFAITHFUL_VARIANT_TYPES)
    expected_before_dedupe = len(policies) * calls_per_claim * len(STYLE_NAMES)
    assert len(all_rows) == expected_before_dedupe, (len(all_rows), expected_before_dedupe)

    kept, removed = dedupe(all_rows)
    print(f"\nDeduped: {removed} near-duplicate rows removed, {len(kept)} kept "
          f"(of {len(all_rows)} generated).")

    print("\nRunning automated consistency checks...")
    flagged = await run_automated_checks(kept, claims_by_id, model)
    print(f"Flagged {len(flagged)} of {len(kept)} rows:")
    flagged_by_type: dict[str, int] = {}
    for row in kept:
        if row.row_id in flagged:
            flagged_by_type[row.variant_type] = flagged_by_type.get(row.variant_type, 0) + 1
    for vt, count in sorted(flagged_by_type.items()):
        print(f"  {vt}: {count} flagged")

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
    write_review_md(kept, live_rows, flagged, REVIEW_PATH)

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

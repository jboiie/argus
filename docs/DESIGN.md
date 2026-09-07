# Design Notes

Deeper rationale behind Argus's architecture — why each component works
the way it does, not just what it does. See `README.md` for the overview
and `DataModel.md` for the schema itself.

## Naming

Named after the many-eyed giant of Greek myth, the watcher who never
sleeps — the natural next step after an earlier project of mine, Aegis
(an autonomous LLM red-teaming/guardrail pipeline). Aegis tested defenses
before the fact; Argus watches continuously, after. Same lineage, one step
further: pre-deployment testing plus post-deployment monitoring, in one
project instead of two.

## Reference agent

A minimal chat-based checkout agent, built as an **MCP client against
Razorpay's own remote MCP server** (35+ tools covering payments, orders,
payment links) via the official `mcp` Python SDK. That choice matters:
it mirrors how real merchant integrations actually talk to Razorpay, and
it gives the red-team harness a real tool-calling surface to attack —
not just chat text.

The agent's own LLM is Gemini 3.5 Flash-Lite, with Groq available on the
same free-tier basis. It deliberately doesn't run on Claude, even though
Razorpay's own Agent Studio does — see "Why not Claude" below.

Cart, coupon, and multi-step checkout math (`agent/cart.py`) is computed
server-side, deterministically, against real catalog prices. The model
never states a trusted price or total for a money-moving action — it can
narrate the total, but it can't set it.

## Why not Claude

Razorpay's own Agent Studio runs on Claude, and this reference agent
originally did too. Moving off it was deliberate, not a cost-cutting
afterthought announced quietly. Argus is a testing harness, not a
customer-facing agent — its value comes from running the reference agent
through hundreds of attack attempts and repeated drift samples across many
runs, not from any single response being polished. That's a
call-volume-heavy, quality-tolerant workload — the opposite of a
production agent, where each response is a live customer interaction and
per-call quality is what's worth paying for. Groq gets roughly the same
capability at a fraction of the cost, which went toward more attack
coverage and more sampling depth instead. The model was picked to match
the job, not to match what's already popular in the ecosystem.

**Quota policy, for anyone reproducing this**: default to free tiers for
every engine, and only move to a paid tier once the free tier has caused
a *repeated, demonstrated* blocker — not preemptively because usage is
trending upward. See `BUGS.md` for exactly where that line got crossed
(Groq's TPD limit, twice) and where it didn't (Gemini's daily cap was
worked around by provisioning a second free-tier project rather than
paying — enabling billing on Google's platform deletes the free tier
entirely rather than adding to it, which cost a day rediscovering).

## Pre-deployment: the red-team harness

Built on [DeepTeam](https://github.com/confident-ai/deepteam) (Apache 2.0)
rather than a bespoke attack-generation engine — no reason to rebuild
that. `deepteam.frameworks.OWASP_ASI_2026` covers the standard agentic
attack surface (goal hijack, tool misuse, identity/privilege abuse, memory
poisoning, cascading failures); four custom vulnerabilities cover what the
standard framework doesn't know to test because it's specific to this
agent's domain: price manipulation, fake discount codes, unauthorized
refunds, and mandate bypass.

Every result is scored Attack Success Rate, labeled with its OWASP ASI
category, and run at real volume (hundreds of attempts, not a handful) —
a small-N demo proves nothing about a system meant to be attacked
continuously.

One deliberate split worth noting: attack *generation* and attack
*judging* use different models (`redteam/groq_model.py`). The judge model
handles framework attacks fine but refuses outright to write several
classes of commerce attack (a straightforward alignment-driven refusal,
not a rate limit) — so a separate model generates those specific attacks
while the same judge scores every result. Keeping generation and judgment
on genuinely independent providers also avoids a judge scoring outputs
from a model in its own family, which would risk correlated blind spots.

## Post-deployment: the drift sentinel

Ground truth is the same `catalog.json`/`policies.json` the reference
agent itself reads — no external dataset needed. This is a narrower kind
of "drift" than large-scale statistical drift detection: it's an agent's
answers checked against a spec that's already fully known, not inference
over a large historical dataset.

Three diffing strategies, chosen per claim type:
- **Numeric/price fields** — exact match. Deliberately not an LLM call:
  a price either matches ground truth or it doesn't.
- **Free-text policy claims** — [RAGAS](https://github.com/explodinggradients/ragas)'s
  Faithfulness metric, which decomposes a response into individual claims
  and checks each against ground-truth context.
- **Claims outside ground truth entirely** — self-consistency checking
  (SelfCheckGPT-style): ask the same question multiple times, disagreement
  across answers is the hallucination signal itself, since there's no
  single "expected" value to diff against.

A sampler ties all three together across the full catalog, policy set,
and a handful of out-of-scope questions, run repeatedly over the build
rather than once at the end — a real drift-over-time signal needs more
than one data point. One drift event was also injected deliberately (a
mid-build price change to a real product) to get one clean, verified,
end-to-end incident rather than hoping stochastic drift would show up
on its own — see `drift/staged_injection.py` and `BUGS.md`.

**Graceful degradation.** Every Drift Incident carries a `drift_cause`
(`stale_ground_truth` | `fabrication` | `inconsistency`) and a `severity`
(`critical` when the incident touches `Product.price` or a money-relevant
policy, `moderate` otherwise). Before answering a question or authorizing
a new mandate that touches a ground-truth reference with an unresolved
critical incident, the reference agent declines to confirm the claim
rather than repeat a possibly-wrong value. This is the project's one
concrete "detected a problem, changed behavior because of it" mechanism —
see `DataModel.md`'s Drift Incident entity for the full classification
logic.

**False-positive cost model.** `drift/audit.py` assumes reviewing one
flagged incident costs `1` unit, and states — as an explicit,
undemonstrated assumption, not a measured one — that a real drift reaching
a user *undetected* costs several times more
(`MISSED_DRIFT_ASSUMED_MULTIPLE = 5`). There's no ground truth on what
should have been flagged but wasn't, so this can't be measured directly;
it's the stated reasoning behind why both the faithfulness and
self-consistency thresholds lean toward over-flagging rather than
under-flagging. What the metric *does* measure directly: of all flagged
incidents that get human-reviewed, how many turn out to be false alarms.

## Dashboard

A static React SPA, not a backend service. Every Supabase table has
row-level security enabled with a **SELECT-only policy for the anon key**
(see `DataModel.md` → Security) — so the browser can query Supabase
directly, because there's nothing to protect behind a server that the
bundled key couldn't already read. `web/scripts/verify-rls.mjs` checks
this property directly: read every table with the anon key, then attempt
one insert, which must fail.

## Rule-based vs. LLM-judged, and why

Every check that *can* be a plain comparison, is one. Numeric price checks
(`drift/diff.py::check_numeric`) are exact equality — no LLM needed, since
a price either matches or it doesn't. `drift_cause`/`severity`
classification (`drift/classify.py`) is a fixed lookup, not a judgment
call. Cart totals (`agent/cart.py::compute_total`) apply the same
principle to the reference agent itself: checkout math is arithmetic
against real catalog prices and a validated coupon, never a number the
model gets to assert.

RAGAS Faithfulness (policy text) and self-consistency scoring (claims with
no ground truth) are the two genuinely LLM-judged checks — both are
fuzzy-by-nature (does free text match free text; do independent answers
agree), which is exactly the kind of judgment a fixed rule can't make.
The dividing line isn't "LLMs are good/bad," it's "does this specific
check actually need one."

## Reproducing the numbers

- `redteam/run_full.py` — full pre-deployment pass (all OWASP_ASI_2026
  vulnerability types + the 4 custom ones), logs Attack Success Rate per
  category to Supabase.
- `drift/sampler.py` — full post-deployment pass across products, policy
  topics, and out-of-scope questions.
- `drift/staged_injection.py` (`inject` then `verify`, with a real git
  commit of the ground-truth edit in between) reproduces the staged-drift
  demo specifically.

Every module also has a `demo()`/`__main__` self-check runnable on its
own — see the module docstrings.

## Practical constraints that shaped the build

- **Razorpay test-mode payment links are capped at 30/business.** Bulk
  attack and drift runs stub `create_payment_link`
  (`Mandate.real_call_fired = False`); only a handful of smoke tests and
  demo transactions hit the real endpoint.
- **Gemini's free tier caps at 500 requests/day, with a fixed reset at
  midnight Pacific** — not a rolling window like Groq's. A full attack
  sweep costs roughly 400 calls, so at most one full run per day on the
  free tier. Enabling billing on the underlying Google Cloud project
  deletes the free tier entirely rather than adding credit on top of it —
  learned the hard way, see `BUGS.md`.
- **Strictly defense/detection scope.** Every attack in this project
  targets only the self-built reference agent. Nothing here is meant to
  be reusable as a standalone exploit/jailbreak generator against a real
  third-party system.

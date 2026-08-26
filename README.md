# Argus — Agent QA & Monitoring Suite for Agentic Commerce

Razorpay AI Builder Buildathon — Open Track Submission

Agentic commerce agents will hallucinate prices, invent policies, and drift over time. Argus is the QA layer for that: a pre-deployment red-team harness (catches issues before an agent ships) plus a post-deployment drift sentinel (catches issues that emerge after it's live), both running against one small reference commerce agent, feeding one live dashboard.

## Status

Reference agent, pre-deployment red-team harness, post-deployment drift sentinel, and dashboard all built, deployed, and verified live (PROJECT_DESC.md build steps 1-25). See `BUGS.md` for what broke and how it was fixed along the way.

## Architecture

Everything grounds out in two flat JSON files — `catalog.json` and `policies.json` — the single source of truth every other piece is checked against.

```
catalog.json / policies.json  (ground truth)
        │
        ▼
agent/  ── Reference Commerce Agent ──────────────────────
  Gemini 3.5 Flash-Lite, MCP client against Razorpay's remote
  server, bounded multi-turn memory, cart + coupon + multi-step
  checkout (agent/cart.py — server-side, deterministic; the
  model never states a trusted price or total), a mandate/
  authorization layer gating create_payment_link behind a
  deterministic transcript-based confirmation check (not the
  model's own self-report — that's the actual thing an attack
  has to defeat).
        │                                    ▲
        │ attacked by                        │ sampled by
        ▼                                    │
redteam/  ── Pre-Deployment Engine        drift/  ── Post-Deployment Engine
  DeepTeam + OWASP_ASI_2026 (all 10          Numeric exact-match, RAGAS
  categories) + 4 commerce-specific          Faithfulness for policy text,
  custom vulnerabilities, ASI-labeled,       self-consistency sampling for
  Attack Success Rate scored per             claims outside ground truth.
  category.                                  Flagged incidents get a
                                              drift_cause (stale ground
                                              truth / fabrication /
                                              inconsistency) and severity.
        │                                    │
        └──────────────┬─────────────────────┘
                        ▼
              Supabase (Postgres + RLS)
        runs / attack_events / drift_incidents /
        mandates / session_turns — full audit trail,
        anon key is SELECT-only, service_role never
        leaves the backend scripts
                        │
                        ▼
              dashboard/  ── Streamlit, read-only
        Tab 1: ASR by ASI category. Tab 2: drift feed,
        cause breakdown, false-positive cost. Both tabs
        drill into the logged conversation behind any
        selected incident.
```

The mandate layer is the one piece that ties the two engines together: it's the concrete thing Track 01's "every money action explainable, bounded and gated" bar demands, and it's also the specific surface the red-team harness's `mandate_bypass` custom vulnerability targets — the same gate gets tested from both directions.

## Design Decisions

**Why we moved off Claude.** Razorpay's own Agent Studio runs on Claude, and our reference agent originally did too. We moved off it deliberately, not quietly. Argus is a testing harness, not a customer-facing agent — its value comes from running the reference agent through hundreds of attack attempts and repeated drift samples across many runs, not from any single response being polished. That's a call-volume-heavy, quality-tolerant workload, the opposite of Razorpay's production agents, where each response is a live customer interaction and Claude's quality-per-call is exactly what's worth paying for. On a self-funded budget, Anthropic's per-token cost caps how much red-teaming and drift-sampling we could actually run; Groq gets us roughly the same capability at a fraction of the cost, which we spent instead on more attack coverage and more sampling depth. We picked the model that matched the job, not the model that matched the pitch.

**False-positive cost model (drift sentinel).** `drift/audit.py` assumes reviewing one flagged incident costs `1` unit, and states — as an explicit, undemonstrated assumption, not a measured one — that a real drift reaching a user *undetected* costs several times more (`MISSED_DRIFT_ASSUMED_MULTIPLE = 5`). There's no ground truth on what should have been flagged but wasn't, so this can't be measured directly; it's the stated reasoning behind why `drift/diff.py`'s `FAITHFULNESS_THRESHOLD` and `drift/self_consistency.py`'s `AGREEMENT_THRESHOLD` both lean toward over-flagging rather than under-flagging. What the metric *does* measure directly: of all flagged incidents that get human-reviewed, how many turn out to be false alarms (`drift/audit.py::compute_false_positive_cost`).

**Rule-based vs. LLM-judged, and why (Section 5's "AI Judgment" axis).** Numeric price checks (`drift/diff.py::check_numeric`) are plain equality comparison — deliberately not an LLM call, since a price either matches or it doesn't. `drift_cause`/`severity` classification (`drift/classify.py`) are also rule-based: severity is a lookup against a fixed money-relevant policy-topic set, and `drift_cause` is a git-history lookup, not a judgment call. Cart totals (`agent/cart.py::compute_total`) are the same principle applied to the reference agent itself — checkout math is arithmetic against real catalog prices and a validated coupon, and the model never gets to state a trusted number for a money-moving action. RAGAS Faithfulness (policy text) and self-consistency scoring (claims with no ground truth) are the two genuinely LLM-judged checks — both are fuzzy-by-nature (does free text match free text; do N independent answers agree), which is exactly the kind of judgment a rule can't make.

**Reproducing the numbers.** `redteam/run_full.py` runs the full pre-deployment pass (all 61 OWASP_ASI_2026 vulnerability types + 4 custom ones) and logs Attack Success Rate per category to Supabase. `drift/sampler.py` runs a full post-deployment pass (25 checks across products, policy topics, and uncovered questions). `drift/staged_injection.py` (`inject` then `verify`, with a real git commit of the ground-truth edit in between) reproduces the step 19 staged-drift demo specifically. Every module also has a `demo()`/`__main__` self-check runnable on its own — see the module docstrings.

## License

MIT — see `LICENSE`.

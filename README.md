# Argus — Agent QA & Monitoring Suite for Agentic Commerce

Razorpay AI Builder Buildathon — Open Track Submission

Agentic commerce agents will hallucinate prices, invent policies, and drift over time. Argus is the QA layer for that: a pre-deployment red-team harness (catches issues before an agent ships) plus a post-deployment drift sentinel (catches issues that emerge after it's live), both running against one small reference commerce agent, feeding one live dashboard.

## Status

Reference agent, pre-deployment red-team harness, and post-deployment drift sentinel all built and verified live (PROJECT_DESC.md build steps 1-20). Dashboard not started yet. See `BUGS.md` for what broke and how it was fixed along the way.

## Components

- **Reference Commerce Agent** (`agent/`) — chat checkout agent over `catalog.json`/`policies.json`, Gemini 3.5 Flash-Lite (Groq also available, see Design Decisions below), MCP client against Razorpay's remote MCP server, bounded multi-turn memory, mandate/authorization layer gating `create_payment_link` behind a deterministic transcript-based confirmation check.
- **Pre-Deployment Engine** (`redteam/`) — DeepTeam-based red-team harness: `OWASP_ASI_2026` framework plus 4 commerce-specific custom vulnerabilities (price manipulation, fake discount codes, unauthorized refunds, catalog-field prompt injection, mandate bypass), each ASI-labeled. Attack Success Rate scored per category (`redteam/scoring.py`), logged to Supabase (`telemetry/supabase_client.py`).
- **Post-Deployment Engine** (`drift/`) — drift sentinel comparing agent responses against ground-truth catalog/policy data: exact match for numeric fields (`drift/diff.py`), RAGAS Faithfulness for policy text, self-consistency sampling for claims not covered by ground truth (`drift/self_consistency.py`). `drift/sampler.py` runs a full pass (25 checks) across products/policies/uncovered questions per session; `drift/classify.py` labels each flagged incident with a cause (`stale_ground_truth`/`fabrication`/`inconsistency`) and severity (`critical`/`moderate`); `drift/audit.py` computes the false-positive review cost (see Design Decisions). `drift/staged_injection.py` is the deliberately-staged demo (step 19).
- **Dashboard** — Streamlit app with pre-deployment ASR report and live drift feed. Not started.

## Setup

```bash
conda create -n argus python=3.11 -y
conda run -n argus pip install -r requirements.txt

cp .env.example .env
# fill in .env: Groq, Gemini, Razorpay test-mode, Supabase keys
```

Run `scripts/setup_supabase.sql` once in your Supabase project's SQL editor (Dashboard → SQL Editor → paste → Run) before any Supabase logging will work — this repo has no direct Postgres connection to run it for you.

Run any script with `conda run --no-capture-output -n argus python -m <module>` (the `--no-capture-output` flag matters on Windows — plain `conda run` buffers stdout and can crash re-printing it through the wrong codepage on non-ASCII output).

```bash
conda run --no-capture-output -n argus python -m agent.smoke_test     # reference agent smoke test
conda run --no-capture-output -n argus python -m redteam.run_asi      # small-scale OWASP_ASI_2026 wiring test
conda run --no-capture-output -n argus python -m redteam.run_custom   # small-scale commerce-vulnerability wiring test
conda run --no-capture-output -n argus python -m redteam.scoring      # ASR scoring self-check (no live API needed)
conda run --no-capture-output -n argus python -m drift.sampler        # full drift sampling pass (25 checks: numeric/faithfulness/self-consistency)
conda run --no-capture-output -n argus python -m drift.staged_injection inject  # step 19 demo, phase 1 (commit catalog.json between phases)
conda run --no-capture-output -n argus python -m drift.staged_injection verify  # step 19 demo, phase 2
conda run --no-capture-output -n argus python -m drift.audit          # false-positive cost metric self-check (no live API needed)

streamlit run dashboard/app.py  # local dashboard - needs SUPABASE_URL/SUPABASE_ANON_KEY in .env (read-only, anon key only)
```

### Deploying the dashboard (Streamlit Cloud)

1. Go to [share.streamlit.io](https://share.streamlit.io), sign in, "New app".
2. Connect this GitHub repo (must be public first — flip visibility before this step), branch `master`, main file path `dashboard/app.py`.
3. In the app's Settings → Secrets, paste `.streamlit/secrets.toml.example`'s content with real values — **`SUPABASE_ANON_KEY` only, never `service_role`** (the dashboard has no write path, so `service_role` there would be a needless privilege escalation if it ever leaked).
4. Deploy. Verify the public URL actually loads live data, not just the static shell.
5. Streamlit Community Cloud apps sleep after 12 hours of no visitor traffic, and a plain `requests.get` does not wake them (it's served a static shell). Step 26 sets up a real-browser keep-alive for this.

## Design Decisions

**Why we moved off Claude.** Razorpay's own Agent Studio runs on Claude, and our reference agent originally did too. We moved off it deliberately, not quietly. Argus is a testing harness, not a customer-facing agent — its value comes from running the reference agent through hundreds of attack attempts and repeated drift samples across many runs, not from any single response being polished. That's a call-volume-heavy, quality-tolerant workload, the opposite of Razorpay's production agents, where each response is a live customer interaction and Claude's quality-per-call is exactly what's worth paying for. On a self-funded budget, Anthropic's per-token cost caps how much red-teaming and drift-sampling we could actually run; Groq gets us roughly the same capability at a fraction of the cost, which we spent instead on more attack coverage and more sampling depth. We picked the model that matched the job, not the model that matched the pitch.

**False-positive cost model (drift sentinel).** `drift/audit.py` assumes reviewing one flagged incident costs `1` unit, and states — as an explicit, undemonstrated assumption, not a measured one — that a real drift reaching a user *undetected* costs several times more (`MISSED_DRIFT_ASSUMED_MULTIPLE = 5`). There's no ground truth on what should have been flagged but wasn't, so this can't be measured directly; it's the stated reasoning behind why `drift/diff.py`'s `FAITHFULNESS_THRESHOLD` and `drift/self_consistency.py`'s `AGREEMENT_THRESHOLD` both lean toward over-flagging rather than under-flagging. What the metric *does* measure directly: of all flagged incidents that get human-reviewed, how many turn out to be false alarms (`drift/audit.py::compute_false_positive_cost`).

**Rule-based vs. LLM-judged, and why (Section 5's "AI Judgment" axis).** Numeric price checks (`drift/diff.py::check_numeric`) are plain equality comparison — deliberately not an LLM call, since a price either matches or it doesn't. `drift_cause`/`severity` classification (`drift/classify.py`) are also rule-based: severity is a lookup against a fixed money-relevant policy-topic set, and `drift_cause` is a git-history lookup, not a judgment call. RAGAS Faithfulness (policy text) and self-consistency scoring (claims with no ground truth) are the two genuinely LLM-judged checks — both are fuzzy-by-nature (does free text match free text; do N independent answers agree), which is exactly the kind of judgment a rule can't make.

## License

TBD.

# Argus — Agent QA & Monitoring Suite for Agentic Commerce

Razorpay AI Builder Buildathon — Open Track Submission

Agentic commerce agents will hallucinate prices, invent policies, and drift over time. Argus is the QA layer for that: a pre-deployment red-team harness (catches issues before an agent ships) plus a post-deployment drift sentinel (catches issues that emerge after it's live), both running against one small reference commerce agent, feeding one live dashboard.

## Status

Reference agent and pre-deployment red-team harness built and verified live (PROJECT_DESC.md build steps 1-14). Step 15 (full-volume run) is blocked on Groq's free-tier daily token cap. Drift sentinel and dashboard not started yet. See `BUGS.md` for what broke and how it was fixed along the way.

## Components

- **Reference Commerce Agent** (`agent/`) — chat checkout agent over `catalog.json`/`policies.json`, Gemini 3.5 Flash-Lite (Groq also available, see Design Decisions below), MCP client against Razorpay's remote MCP server, bounded multi-turn memory, mandate/authorization layer gating `create_payment_link` behind a deterministic transcript-based confirmation check.
- **Pre-Deployment Engine** (`redteam/`) — DeepTeam-based red-team harness: `OWASP_ASI_2026` framework plus 4 commerce-specific custom vulnerabilities (price manipulation, fake discount codes, unauthorized refunds, catalog-field prompt injection, mandate bypass), each ASI-labeled. Attack Success Rate scored per category (`redteam/scoring.py`), logged to Supabase (`telemetry/supabase_client.py`).
- **Post-Deployment Engine** — Drift sentinel comparing agent responses against ground-truth catalog/policy data: exact match for numeric fields, RAGAS Faithfulness for policy text, self-consistency checks for uncovered claims. Not started.
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
```

## Design Decisions

**Why we moved off Claude.** Razorpay's own Agent Studio runs on Claude, and our reference agent originally did too. We moved off it deliberately, not quietly. Argus is a testing harness, not a customer-facing agent — its value comes from running the reference agent through hundreds of attack attempts and repeated drift samples across many runs, not from any single response being polished. That's a call-volume-heavy, quality-tolerant workload, the opposite of Razorpay's production agents, where each response is a live customer interaction and Claude's quality-per-call is exactly what's worth paying for. On a self-funded budget, Anthropic's per-token cost caps how much red-teaming and drift-sampling we could actually run; Groq gets us roughly the same capability at a fraction of the cost, which we spent instead on more attack coverage and more sampling depth. We picked the model that matched the job, not the model that matched the pitch.

## License

TBD.

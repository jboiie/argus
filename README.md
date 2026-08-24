# Argus — Agent QA & Monitoring Suite for Agentic Commerce

Razorpay AI Builder Buildathon — Open Track Submission

Agentic commerce agents will hallucinate prices, invent policies, and drift over time. Argus is the QA layer for that: a pre-deployment red-team harness (catches issues before an agent ships) plus a post-deployment drift sentinel (catches issues that emerge after it's live), both running against one small reference commerce agent, feeding one live dashboard.

## Status

Repo scaffolding in progress.

## Components

- **Reference Commerce Agent** — minimal chat-based checkout agent (Claude Haiku), MCP client against Razorpay's remote MCP server, small fixed catalog, mandate/authorization layer before payment actions.
- **Pre-Deployment Engine** — DeepTeam-based red-team harness (OWASP ASI Top 10 for Agentic Applications + commerce-specific attacks: price manipulation, fake discounts, unauthorized refunds, prompt injection, mandate bypass). Attack Success Rate scored per category.
- **Post-Deployment Engine** — Drift sentinel comparing agent responses against ground-truth catalog/policy data: exact match for numeric fields, RAGAS Faithfulness for policy text, self-consistency checks for uncovered claims.
- **Dashboard** — Streamlit app with pre-deployment ASR report and live drift feed.

## Setup

```bash
conda create -n argus python=3.11 -y
conda run -n argus pip install -r requirements.txt

cp .env.example .env
# fill in .env: Groq, Gemini, Razorpay test-mode, Supabase keys
```

Run any script with `conda run --no-capture-output -n argus python -m <module>` (the `--no-capture-output` flag matters on Windows — plain `conda run` buffers stdout and can crash re-printing it through the wrong codepage on non-ASCII output).

```bash
conda run --no-capture-output -n argus python -m agent.smoke_test   # reference agent smoke test
conda run --no-capture-output -n argus python -m redteam.run_asi    # small-scale red-team wiring test
```

## License

TBD.

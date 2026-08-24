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

Coming soon.

## License

TBD.

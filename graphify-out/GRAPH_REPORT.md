# Graph Report - argus  (2026-08-26)

## Corpus Check
- 47 files · ~33,080 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 260 nodes · 390 edges · 23 communities (18 shown, 5 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3709de2a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- verify
- What You Must Do When Invoked
- CLAUDE.md
- graphify reference: extra exports and benchmark
- graphify reference: query, path, explain
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- Argus — Agent QA & Monitoring Suite for Agentic Commerce
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify
- extraction-spec.md
- GroqModel
- reference_agent.py
- diff.py
- mandate.py
- Argus — Agent QA & Monitoring Suite for Agentic Commerce
- Bugs & Fixes
- main
- Argus — Data Model

## God Nodes (most connected - your core abstractions)
1. `GroqModel` - 14 edges
2. `Argus — Agent QA & Monitoring Suite for Agentic Commerce` - 12 edges
3. `main()` - 12 edges
4. `main()` - 12 edges
5. `What You Must Do When Invoked` - 12 edges
6. `ask_with_tools()` - 11 edges
7. `/graphify` - 11 edges
8. `verify()` - 10 edges
9. `main()` - 10 edges
10. `ask_async()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `verify()` --calls--> `create_run()`  [INFERRED]
  drift/staged_injection.py → telemetry/supabase_client.py
- `verify()` --calls--> `end_run()`  [INFERRED]
  drift/staged_injection.py → telemetry/supabase_client.py
- `verify()` --calls--> `get_client()`  [INFERRED]
  drift/staged_injection.py → telemetry/supabase_client.py
- `main()` --calls--> `create_run()`  [INFERRED]
  drift/sampler.py → telemetry/supabase_client.py
- `demo()` --calls--> `check_numeric()`  [INFERRED]
  telemetry/supabase_client.py → drift/diff.py

## Import Cycles
- None detected.

## Communities (23 total, 5 thin omitted)

### Community 0 - "verify"
Cohesion: 0.19
Nodes (15): classify_drift_cause(), classify_severity(), demo(), _git_history_values(), _load_ground_truth(), drift_cause and severity classification - build step 19 (PROJECT_DESC.md…, critical | moderate | None (self_consistency rows have no ground truth to be…, Every historical value `item_id`'s `value_field` has held in `filename`'s git… (+7 more)

### Community 1 - "What You Must Do When Invoked"
Cohesion: 0.07
Nodes (26): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+18 more)

### Community 2 - "CLAUDE.md"
Cohesion: 0.20
Nodes (8): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, 5. Git Commits, 6. Question the Path, Not Just the Code, 7. Milestone Recaps, graphify

### Community 3 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 4 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 5 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 6 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 7 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 8 - "Argus — Agent QA & Monitoring Suite for Agentic Commerce"
Cohesion: 0.11
Nodes (17): 0. Before You Write Any Code, 1. Context & Stakes, 2. The One-Line Idea, 3. Why Now — Use These Specific Anchors in the Pitch, 4.1 Reference Commerce Agent (the target, not the differentiator), 4.2 Authorization / Mandate Layer (new — don't skip this), 4.3 Pre-Deployment Engine — Guardrail Red-Team Harness, 4.4 Post-Deployment Engine — Drift Sentinel (+9 more)

### Community 13 - "GroqModel"
Cohesion: 0.16
Nodes (12): BadRequestError, BaseModel, DeepEvalBaseLLM, RateLimitError, demo(), GroqModel, _is_empty_generation(), Groq-backed judge/simulator model for DeepTeam - keeps attack generation and… (+4 more)

### Community 14 - "reference_agent.py"
Cohesion: 0.23
Nodes (16): ask(), ask_async(), ask_with_tools(), build_system_prompt(), demo(), demo_tools(), _generate_with_retry(), _has_genuine_confirmation() (+8 more)

### Community 16 - "diff.py"
Cohesion: 0.12
Nodes (25): AsyncOpenAI, check_faithfulness(), check_numeric(), demo(), DriftCheckResult, _extract_number(), _judge_client(), Ground-truth diffing: exact-match for numeric fields, RAGAS Faithfulness for… (+17 more)

### Community 17 - "mandate.py"
Cohesion: 0.15
Nodes (16): create_mandate(), demo(), is_valid(), Mandate, Mandate / authorization layer - logged before any payment-link action. In-…, _auth_header(), call_tool(), demo() (+8 more)

### Community 19 - "Argus — Agent QA & Monitoring Suite for Agentic Commerce"
Cohesion: 0.29
Nodes (6): Argus — Agent QA & Monitoring Suite for Agentic Commerce, Components, Design Decisions, License, Setup, Status

### Community 21 - "main"
Cohesion: 0.10
Nodes (35): Client, Commerce-specific vulnerabilities not covered by OWASP_ASI_2026's standard…, demo(), make_model_callback(), Bridges DeepTeam's model_callback contract to the reference agent. DeepTeam…, Bind run_id via closure - keeps model_callback's exact (input, turns=None)…, _seed_session(), session_id_for() (+27 more)

### Community 22 - "Argus — Data Model"
Cohesion: 0.18
Nodes (10): Argus — Data Model, Cross-cutting conventions, Currency convention, Entity 0: Run (Supabase), Entity 1: Product (`catalog.json`), Entity 2: Policy (`policies.json`), Entity 3: Mandate (logged per authorization attempt, Supabase), Entity 4: Attack Event (red-team harness log, Supabase) (+2 more)

## Knowledge Gaps
- **81 isolated node(s):** `Retired: `DEBUG_JOURNAL.md``, `Razorpay AI Builder Buildathon — Open Track Submission`, `0. Before You Write Any Code`, `1. Context & Stakes`, `2. The One-Line Idea` (+76 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ask_with_tools()` connect `reference_agent.py` to `mandate.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `GroqModel` connect `GroqModel` to `diff.py`, `main`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `ask_async()` connect `reference_agent.py` to `diff.py`, `verify`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `main()` (e.g. with `create_run()` and `end_run()`) actually correct?**
  _`main()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `main()` (e.g. with `create_run()` and `end_run()`) actually correct?**
  _`main()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Retired: `DEBUG_JOURNAL.md``, `Razorpay AI Builder Buildathon — Open Track Submission`, `0. Before You Write Any Code` to the rest of the system?**
  _81 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.07407407407407407 - nodes in this community are weakly interconnected._
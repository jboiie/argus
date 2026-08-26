# Graph Report - argus  (2026-08-26)

## Corpus Check
- 42 files · ~30,004 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 227 nodes · 308 edges · 24 communities (19 shown, 5 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `437dd799`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- /graphify
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
- razorpay_mcp.py
- diff.py
- mandate.py
- Argus — Agent QA & Monitoring Suite for Agentic Commerce
- Bugs & Fixes
- main
- Argus — Data Model

## God Nodes (most connected - your core abstractions)
1. `GroqModel` - 13 edges
2. `Argus — Agent QA & Monitoring Suite for Agentic Commerce` - 12 edges
3. `main()` - 12 edges
4. `main()` - 12 edges
5. `What You Must Do When Invoked` - 12 edges
6. `ask_with_tools()` - 11 edges
7. `/graphify` - 11 edges
8. `main()` - 10 edges
9. `Argus — Data Model` - 10 edges
10. `compute_asr()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `demo()` --calls--> `check_numeric()`  [EXTRACTED]
  telemetry/supabase_client.py → drift/diff.py
- `main()` --calls--> `create_run()`  [INFERRED]
  redteam/run_asi.py → telemetry/supabase_client.py
- `main()` --calls--> `end_run()`  [INFERRED]
  redteam/run_asi.py → telemetry/supabase_client.py
- `main()` --calls--> `get_client()`  [INFERRED]
  redteam/run_asi.py → telemetry/supabase_client.py
- `main()` --calls--> `log_attack_event()`  [INFERRED]
  redteam/run_asi.py → telemetry/supabase_client.py

## Import Cycles
- None detected.

## Communities (24 total, 5 thin omitted)

### Community 0 - "/graphify"
Cohesion: 0.17
Nodes (11): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, PowerShell 5.1: Vertical scrolling stops working (+3 more)

### Community 1 - "What You Must Do When Invoked"
Cohesion: 0.13
Nodes (15): Part A - Structural extraction for code files, Part B - Semantic extraction (parallel subagents), Part C - Merge AST + semantic into final extraction, Step 0 - GitHub repos and multi-path merge (only if a URL or several paths), Step 1 - Ensure graphify is installed, Step 2.5 - Video and audio (only if video files detected), Step 2 - Detect files, Step 3 - Extract entities and relationships (+7 more)

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
Cohesion: 0.25
Nodes (14): ask(), ask_with_tools(), build_system_prompt(), demo(), demo_tools(), _generate_with_retry(), _has_genuine_confirmation(), load_ground_truth() (+6 more)

### Community 15 - "razorpay_mcp.py"
Cohesion: 0.43
Nodes (6): _auth_header(), call_tool(), demo(), list_tools(), MCP client wiring against Razorpay's remote MCP server. Connects with the…, Read-only: returns the names of tools Razorpay's MCP server exposes.

### Community 16 - "diff.py"
Cohesion: 0.26
Nodes (11): AsyncOpenAI, check_faithfulness(), check_numeric(), demo(), DriftCheckResult, _extract_number(), _judge_client(), Ground-truth diffing: exact-match for numeric fields, RAGAS Faithfulness for… (+3 more)

### Community 17 - "mandate.py"
Cohesion: 0.24
Nodes (10): create_mandate(), demo(), is_valid(), Mandate, Mandate / authorization layer - logged before any payment-link action. In-…, create_payment_link_declaration(), execute_tool_call(), Bridges Razorpay MCP tools into Gemini function-calling. Money-moving tools go… (+2 more)

### Community 19 - "Argus — Agent QA & Monitoring Suite for Agentic Commerce"
Cohesion: 0.29
Nodes (6): Argus — Agent QA & Monitoring Suite for Agentic Commerce, Components, Design Decisions, License, Setup, Status

### Community 21 - "main"
Cohesion: 0.09
Nodes (37): Client, Commerce-specific vulnerabilities not covered by OWASP_ASI_2026's standard…, demo(), make_model_callback(), Bridges DeepTeam's model_callback contract to the reference agent. DeepTeam…, Bind run_id via closure - keeps model_callback's exact (input, turns=None)…, _seed_session(), session_id_for() (+29 more)

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
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `GroqModel` connect `GroqModel` to `main`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `_generate_with_retry()` connect `reference_agent.py` to `main`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `main()` (e.g. with `create_run()` and `end_run()`) actually correct?**
  _`main()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `main()` (e.g. with `create_run()` and `end_run()`) actually correct?**
  _`main()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Retired: `DEBUG_JOURNAL.md``, `Razorpay AI Builder Buildathon — Open Track Submission`, `0. Before You Write Any Code` to the rest of the system?**
  _81 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
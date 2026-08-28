# Graph Report - argus  (2026-08-28)

## Corpus Check
- 50 files · ~47,169 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 376 nodes · 661 edges · 27 communities (20 shown, 7 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 39 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d4990c31`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.py
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
- reference_agent.py
- razorpay_mcp.py
- supabase_client.py
- sampler.py
- Client
- Argus — Agent QA & Monitoring Suite for Agentic Commerce
- Bugs & Fixes
- diff.py
- Argus — Data Model
- mandate_attacks.py
- GroqModel
- Client

## God Nodes (most connected - your core abstractions)
1. `ask_with_tools()` - 17 edges
2. `GroqModel` - 16 edges
3. `execute_tool_call()` - 13 edges
4. `ask_async()` - 12 edges
5. `get_client()` - 12 edges
6. `main()` - 12 edges
7. `What You Must Do When Invoked` - 12 edges
8. `Argus — Agent QA & Monitoring Suite for Agentic Commerce` - 12 edges
9. `verify()` - 11 edges
10. `create_run()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `_log_mandate_safe()` --calls--> `log_mandate()`  [INFERRED]
  agent/tools.py → telemetry/supabase_client.py
- `run_scenario()` --calls--> `clear_cart()`  [INFERRED]
  redteam/mandate_attacks.py → agent/cart.py
- `start_run()` --calls--> `create_run()`  [INFERRED]
  redteam/mandate_attacks.py → telemetry/supabase_client.py
- `log_to_supabase()` --calls--> `end_run()`  [INFERRED]
  redteam/mandate_attacks.py → telemetry/supabase_client.py
- `log_to_supabase()` --calls--> `log_attack_event()`  [INFERRED]
  redteam/mandate_attacks.py → telemetry/supabase_client.py

## Import Cycles
- None detected.

## Communities (27 total, 7 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.10
Nodes (46): cache_data, cache_resource, Client, _client(), _find_staged_drift(), _load_attack_events(), _load_drift_incidents(), _load_mandates() (+38 more)

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

### Community 13 - "reference_agent.py"
Cohesion: 0.07
Nodes (54): add_item(), apply_coupon(), _cart(), clear_cart(), compute_total(), demo(), load_coupons(), load_products() (+46 more)

### Community 14 - "razorpay_mcp.py"
Cohesion: 0.43
Nodes (6): _auth_header(), call_tool(), demo(), list_tools(), MCP client wiring against Razorpay's remote MCP server. Connects with the…, Read-only: returns the names of tools Razorpay's MCP server exposes.

### Community 15 - "supabase_client.py"
Cohesion: 0.09
Nodes (32): demo(), Graceful-degradation gate - PROJECT_DESC.md Section 4.4 / DataModel.md's Drift…, unresolved_critical_refs(), classify_drift_cause(), classify_severity(), demo(), _git_history_values(), _load_ground_truth() (+24 more)

### Community 16 - "sampler.py"
Cohesion: 0.09
Nodes (38): _faithfulness_question(), main(), _numeric_question(), Sampler that simulates repeated sessions asking overlapping questions against…, Returns each result paired with the RAW agent text(s) that produced it - not…, run_and_log(), run_session(), _summarize() (+30 more)

### Community 19 - "Argus — Agent QA & Monitoring Suite for Agentic Commerce"
Cohesion: 0.25
Nodes (7): Architecture, Argus — Agent QA & Monitoring Suite for Agentic Commerce, Design Decisions, Full-sweep results, License, Status, What Argus Actually Caught

### Community 21 - "diff.py"
Cohesion: 0.16
Nodes (17): AsyncOpenAI, check_faithfulness(), check_numeric(), demo(), DriftCheckResult, _extract_number(), _judge_client(), Ground-truth diffing: exact-match for numeric fields, RAGAS Faithfulness for… (+9 more)

### Community 22 - "Argus — Data Model"
Cohesion: 0.17
Nodes (11): Argus — Data Model, Cross-cutting conventions, Currency convention, Entity 0: Run (Supabase), Entity 1: Product (`catalog.json`), Entity 2.5: Coupon (`coupons.json`), Entity 2: Policy (`policies.json`), Entity 3: Mandate (logged per authorization attempt, Supabase) (+3 more)

### Community 24 - "mandate_attacks.py"
Cohesion: 0.19
Nodes (16): _AttackEventShim, log_to_supabase(), main(), print_results(), Targeted mandate-bypass scenarios - the attacks DeepTeam's generic single-turn…, A real UUID, not a readable slug. mandates.session_id and…, ask_fn(session_id, run_id, message) -> str. Injected rather than imported so…, Attack scenarios only - the control is a suite-validity check, not an attack,… (+8 more)

### Community 25 - "GroqModel"
Cohesion: 0.14
Nodes (13): BadRequestError, BaseModel, DeepEvalBaseLLM, RateLimitError, Commerce-specific vulnerabilities not covered by OWASP_ASI_2026's standard…, demo(), GroqModel, _is_empty_generation() (+5 more)

## Knowledge Gaps
- **82 isolated node(s):** `For /graphify add and --watch`, `For /graphify query`, `For the commit hook and native CLAUDE.md integration`, `For --update and --cluster-only`, `Honesty Rules` (+77 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ask_with_tools()` connect `reference_agent.py` to `mandate_attacks.py`, `supabase_client.py`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `GroqModel` connect `GroqModel` to `sampler.py`, `diff.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `_generate_with_retry()` connect `reference_agent.py` to `app.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `ask_with_tools()` (e.g. with `load_coupons()` and `unresolved_critical_refs()`) actually correct?**
  _`ask_with_tools()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `execute_tool_call()` (e.g. with `ask_with_tools()` and `demo_drift_guard_block()`) actually correct?**
  _`execute_tool_call()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ask_async()` (e.g. with `load_coupons()` and `unresolved_critical_refs()`) actually correct?**
  _`ask_async()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `For /graphify add and --watch`, `For /graphify query`, `For the commit hook and native CLAUDE.md integration` to the rest of the system?**
  _82 weakly-connected nodes found - possible documentation gaps or missing edges._
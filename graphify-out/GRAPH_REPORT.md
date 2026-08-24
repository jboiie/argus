# Graph Report - argus  (2026-08-24)

## Corpus Check
- 39 files · ~29,745 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 213 nodes · 270 edges · 23 communities (19 shown, 4 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `087512a8`
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
- ask_with_tools
- razorpay_mcp.py
- Debug Journal
- mandate.py
- Argus — Agent QA & Monitoring Suite for Agentic Commerce
- DeepTeam / Red-Team Harness (`redteam/`)
- main
- model_callback.py

## God Nodes (most connected - your core abstractions)
1. `GroqModel` - 12 edges
2. `What You Must Do When Invoked` - 12 edges
3. `Argus — Agent QA & Monitoring Suite for Agentic Commerce` - 12 edges
4. `/graphify` - 11 edges
5. `main()` - 10 edges
6. `main()` - 10 edges
7. `ask_with_tools()` - 10 edges
8. `DeepTeam / Red-Team Harness (`redteam/`)` - 9 edges
9. `compute_asr()` - 8 edges
10. `graphify reference: extra exports and benchmark` - 8 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `create_run()`  [INFERRED]
  redteam/run_asi.py → telemetry/supabase_client.py
- `main()` --calls--> `end_run()`  [INFERRED]
  redteam/run_asi.py → telemetry/supabase_client.py
- `main()` --calls--> `get_client()`  [INFERRED]
  redteam/run_asi.py → telemetry/supabase_client.py
- `main()` --calls--> `log_attack_event()`  [INFERRED]
  redteam/run_asi.py → telemetry/supabase_client.py
- `main()` --calls--> `create_run()`  [INFERRED]
  redteam/run_custom.py → telemetry/supabase_client.py

## Import Cycles
- None detected.

## Communities (23 total, 4 thin omitted)

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
Cohesion: 0.18
Nodes (9): BaseModel, DeepEvalBaseLLM, RateLimitError, demo(), GroqModel, Groq-backed judge/simulator model for DeepTeam - keeps attack generation and…, Pydantic's default model_json_schema() doesn't satisfy Groq's strict…, _retry_after_seconds() (+1 more)

### Community 14 - "ask_with_tools"
Cohesion: 0.27
Nodes (13): ask(), ask_with_tools(), build_system_prompt(), demo(), demo_tools(), _has_genuine_confirmation(), load_ground_truth(), Reference commerce agent — Gemini 3.5 Flash-Lite over… (+5 more)

### Community 15 - "razorpay_mcp.py"
Cohesion: 0.43
Nodes (6): _auth_header(), call_tool(), demo(), list_tools(), MCP client wiring against Razorpay's remote MCP server. Connects with the…, Read-only: returns the names of tools Razorpay's MCP server exposes.

### Community 16 - "Debug Journal"
Cohesion: 0.25
Nodes (7): 2026-08-24 — Custom commerce vulnerabilities (step 12): two more Groq rate-limit layers found, 2026-08-24 — DeepTeam judge model: three-stage saga to find a usable free-tier model, 2026-08-24 — Gemini 2.5 Flash-Lite retired for new users, 2026-08-24 — Mandate gate accepted an external `user_confirmed` flag, defeating its own purpose, 2026-08-24 — Razorpay MCP server auth: docs/README say Bearer, server requires Basic, 2026-08-24 — Stubbed tool result had no url field, model fabricated a fake-looking payment link, Debug Journal

### Community 17 - "mandate.py"
Cohesion: 0.24
Nodes (10): create_mandate(), demo(), is_valid(), Mandate, Mandate / authorization layer - logged before any payment-link action. In-…, create_payment_link_declaration(), execute_tool_call(), Bridges Razorpay MCP tools into Gemini function-calling. Money-moving tools go… (+2 more)

### Community 19 - "Argus — Agent QA & Monitoring Suite for Agentic Commerce"
Cohesion: 0.33
Nodes (5): Argus — Agent QA & Monitoring Suite for Agentic Commerce, Components, License, Setup, Status

### Community 20 - "DeepTeam / Red-Team Harness (`redteam/`)"
Cohesion: 0.11
Nodes (17): Bugs & Fixes Reference, Concurrent DeepTeam tasks thundering-herd the shared Groq rate limit — fixed, `conda run` crashes re-printing captured output with non-ASCII characters, DeepTeam full-category run: high error rate on Groq free tier — fixed, DeepTeam / Red-Team Harness (`redteam/`), Empty stub field → model fabricated a fake payment link, External API Integration, Format (+9 more)

### Community 21 - "main"
Cohesion: 0.18
Nodes (20): Client, main(), main(), asi_code_for(), CategoryASR, compute_asr(), demo(), outcome() (+12 more)

### Community 22 - "model_callback.py"
Cohesion: 0.21
Nodes (10): Commerce-specific vulnerabilities not covered by OWASP_ASI_2026's standard…, demo(), make_model_callback(), Bridges DeepTeam's model_callback contract to the reference agent. DeepTeam…, Bind run_id via closure - keeps model_callback's exact (input, turns=None)…, _seed_session(), session_id_for(), Wires DeepTeam's OWASP_ASI_2026 framework against the reference agent. Small-… (+2 more)

## Knowledge Gaps
- **89 isolated node(s):** `For /graphify add and --watch`, `For /graphify query`, `For the commit hook and native CLAUDE.md integration`, `For --update and --cluster-only`, `Honesty Rules` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ask_with_tools()` connect `ask_with_tools` to `mandate.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `GroqModel` connect `GroqModel` to `main`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `main()` connect `main` to `GroqModel`, `model_callback.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `main()` (e.g. with `create_run()` and `end_run()`) actually correct?**
  _`main()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `For /graphify add and --watch`, `For /graphify query`, `For the commit hook and native CLAUDE.md integration` to the rest of the system?**
  _89 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
- **Should `Argus — Agent QA & Monitoring Suite for Agentic Commerce` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
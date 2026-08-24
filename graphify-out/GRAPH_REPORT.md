# Graph Report - argus  (2026-08-24)

## Corpus Check
- 36 files · ~26,418 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 182 nodes · 205 edges · 22 communities (18 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `081b08a2`
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
- model_callback

## God Nodes (most connected - your core abstractions)
1. `What You Must Do When Invoked` - 12 edges
2. `Argus — Agent QA & Monitoring Suite for Agentic Commerce` - 12 edges
3. `GroqModel` - 11 edges
4. `ask_with_tools()` - 11 edges
5. `/graphify` - 11 edges
6. `graphify reference: extra exports and benchmark` - 8 edges
7. `model_callback()` - 7 edges
8. `DeepTeam / Red-Team Harness (`redteam/`)` - 7 edges
9. `ask()` - 6 edges
10. `Debug Journal` - 6 edges

## Surprising Connections (you probably didn't know these)
- `model_callback()` --calls--> `ask_with_tools()`  [EXTRACTED]
  redteam/model_callback.py → agent/reference_agent.py
- `ask_with_tools()` --calls--> `create_payment_link_declaration()`  [INFERRED]
  agent/reference_agent.py → agent/tools.py
- `ask_with_tools()` --calls--> `execute_tool_call()`  [INFERRED]
  agent/reference_agent.py → agent/tools.py
- `main()` --calls--> `GroqModel`  [EXTRACTED]
  redteam/run_asi.py → redteam/groq_model.py
- `main()` --indirect_call--> `model_callback()`  [INFERRED]
  redteam/run_asi.py → redteam/model_callback.py

## Import Cycles
- None detected.

## Communities (22 total, 4 thin omitted)

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
Cohesion: 0.29
Nodes (6): 2026-08-24 — DeepTeam judge model: three-stage saga to find a usable free-tier model, 2026-08-24 — Gemini 2.5 Flash-Lite retired for new users, 2026-08-24 — Mandate gate accepted an external `user_confirmed` flag, defeating its own purpose, 2026-08-24 — Razorpay MCP server auth: docs/README say Bearer, server requires Basic, 2026-08-24 — Stubbed tool result had no url field, model fabricated a fake-looking payment link, Debug Journal

### Community 17 - "mandate.py"
Cohesion: 0.24
Nodes (10): create_mandate(), demo(), is_valid(), Mandate, Mandate / authorization layer - logged before any payment-link action. In-…, create_payment_link_declaration(), execute_tool_call(), Bridges Razorpay MCP tools into Gemini function-calling. Money-moving tools go… (+2 more)

### Community 19 - "Argus — Agent QA & Monitoring Suite for Agentic Commerce"
Cohesion: 0.33
Nodes (5): Argus — Agent QA & Monitoring Suite for Agentic Commerce, Components, License, Setup, Status

### Community 20 - "DeepTeam / Red-Team Harness (`redteam/`)"
Cohesion: 0.12
Nodes (15): Bugs & Fixes Reference, `conda run` crashes re-printing captured output with non-ASCII characters, DeepTeam full-category run: high error rate on Groq free tier — open problem, DeepTeam / Red-Team Harness (`redteam/`), Empty stub field → model fabricated a fake payment link, External API Integration, Format, Gemini 2.5 Flash-Lite retired for new API keys (+7 more)

### Community 21 - "model_callback"
Cohesion: 0.36
Nodes (7): demo(), model_callback(), Bridges DeepTeam's model_callback contract to the reference agent. DeepTeam…, _seed_session(), main(), Wires DeepTeam's OWASP_ASI_2026 framework against the reference agent. Small-…, RTTurn

## Knowledge Gaps
- **86 isolated node(s):** `For /graphify add and --watch`, `For /graphify query`, `For the commit hook and native CLAUDE.md integration`, `For --update and --cluster-only`, `Honesty Rules` (+81 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ask_with_tools()` connect `ask_with_tools` to `mandate.py`, `model_callback`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `model_callback()` connect `model_callback` to `ask_with_tools`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `GroqModel` connect `GroqModel` to `model_callback`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `ask_with_tools()` (e.g. with `create_payment_link_declaration()` and `execute_tool_call()`) actually correct?**
  _`ask_with_tools()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `For /graphify add and --watch`, `For /graphify query`, `For the commit hook and native CLAUDE.md integration` to the rest of the system?**
  _86 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
- **Should `Argus — Agent QA & Monitoring Suite for Agentic Commerce` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
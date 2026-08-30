# Graph Report - argus  (2026-08-30)

## Corpus Check
- 80 files · ~275,924 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 589 nodes · 981 edges · 40 communities (26 shown, 14 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 39 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9f316cd9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- audit.py
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
- DriftAct.tsx
- GroqModel
- Client
- Argus — Agent QA & Monitoring Suite for Agentic Commerce
- Bugs & Fixes
- App.tsx
- Argus — Data Model
- mandate_attacks.py
- devDependencies
- Client
- compilerOptions
- compilerOptions
- plugins
- Argus dashboard (web)
- verify-rls.mjs
- tsconfig.json
- supabase_client.py
- Dock.tsx
- cache_data
- cache_resource
- DataFrame
- Series

## God Nodes (most connected - your core abstractions)
1. `compilerOptions` - 18 edges
2. `ask_with_tools()` - 17 edges
3. `GroqModel` - 16 edges
4. `react` - 16 edges
5. `compilerOptions` - 15 edges
6. `execute_tool_call()` - 13 edges
7. `ask_async()` - 12 edges
8. `main()` - 12 edges
9. `get_client()` - 12 edges
10. `What You Must Do When Invoked` - 12 edges

## Surprising Connections (you probably didn't know these)
- `run_scenario()` --calls--> `clear_cart()`  [INFERRED]
  redteam/mandate_attacks.py → agent/cart.py
- `main()` --indirect_call--> `ask_with_tools()`  [INFERRED]
  redteam/mandate_attacks.py → agent/reference_agent.py
- `_log_mandate_safe()` --calls--> `log_mandate()`  [INFERRED]
  agent/tools.py → telemetry/supabase_client.py
- `main()` --calls--> `create_run()`  [INFERRED]
  redteam/run_asi.py → telemetry/supabase_client.py
- `main()` --calls--> `end_run()`  [INFERRED]
  redteam/run_asi.py → telemetry/supabase_client.py

## Import Cycles
- None detected.

## Communities (40 total, 14 thin omitted)

### Community 0 - "audit.py"
Cohesion: 0.38
Nodes (6): compute_false_positive_cost(), demo(), print_audit_trail(), Audit trail + false-positive cost metric - build step 20 (PROJECT_DESC.md…, incidents: drift_incidents rows as returned by the Supabase client (plain…, Full per-incident detail - question, expected/actual, score, classification,…

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
Nodes (52): add_item(), apply_coupon(), _cart(), clear_cart(), compute_total(), demo(), load_coupons(), load_products() (+44 more)

### Community 14 - "razorpay_mcp.py"
Cohesion: 0.43
Nodes (6): _auth_header(), call_tool(), demo(), list_tools(), MCP client wiring against Razorpay's remote MCP server. Connects with the…, Read-only: returns the names of tools Razorpay's MCP server exposes.

### Community 15 - "DriftAct.tsx"
Cohesion: 0.07
Nodes (28): Step(), StepperProps, stepVariants, Stamp(), rawSleep(), RunCtl, sleep(), typeInto() (+20 more)

### Community 16 - "GroqModel"
Cohesion: 0.07
Nodes (39): BadRequestError, BaseModel, DeepEvalBaseLLM, RateLimitError, Commerce-specific vulnerabilities not covered by OWASP_ASI_2026's standard…, demo(), GroqModel, _is_empty_generation() (+31 more)

### Community 19 - "Argus — Agent QA & Monitoring Suite for Agentic Commerce"
Cohesion: 0.20
Nodes (9): Architecture, Argus — Agent QA & Monitoring Suite for Agentic Commerce, Dashboard, Design Decisions, Full-sweep results, Known Issues, License, Status (+1 more)

### Community 21 - "App.tsx"
Cohesion: 0.06
Nodes (62): react, App(), NAV, TabId, Conversation(), Iris(), RunSelector(), ShuffleDirection (+54 more)

### Community 22 - "Argus — Data Model"
Cohesion: 0.17
Nodes (11): Argus — Data Model, Cross-cutting conventions, Currency convention, Entity 0: Run (Supabase), Entity 1: Product (`catalog.json`), Entity 2.5: Coupon (`coupons.json`), Entity 2: Policy (`policies.json`), Entity 3: Mandate (logged per authorization attempt, Supabase) (+3 more)

### Community 24 - "mandate_attacks.py"
Cohesion: 0.19
Nodes (16): _AttackEventShim, log_to_supabase(), main(), print_results(), Targeted mandate-bypass scenarios - the attacks DeepTeam's generic single-turn…, A real UUID, not a readable slug. mandates.session_id and…, ask_fn(session_id, run_id, message) -> str. Injected rather than imported so…, Attack scenarios only - the control is a suite-validity check, not an attack,… (+8 more)

### Community 25 - "devDependencies"
Cohesion: 0.04
Nodes (45): gsap, @gsap/react, lucide-react, motion, oxlint, react, react-dom, recharts (+37 more)

### Community 27 - "compilerOptions"
Cohesion: 0.08
Nodes (23): DOM, src, vite/client, compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx (+15 more)

### Community 28 - "compilerOptions"
Cohesion: 0.10
Nodes (19): node, vite.config.ts, compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection (+11 more)

### Community 29 - "plugins"
Cohesion: 0.22
Nodes (8): oxc, typescript, warn, plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 30 - "Argus dashboard (web)"
Cohesion: 0.29
Nodes (6): Argus dashboard (web), Build, Deploy, Local, Rendering untrusted text, Why a static SPA and not a backend

### Community 34 - "supabase_client.py"
Cohesion: 0.06
Nodes (64): demo(), Graceful-degradation gate - PROJECT_DESC.md Section 4.4 / DataModel.md's Drift…, unresolved_critical_refs(), ask_async(), Async single-turn Q&A, same grounding as ask() - used by the drift sampler…, AsyncOpenAI, Client, classify_drift_cause() (+56 more)

## Knowledge Gaps
- **186 isolated node(s):** `NAV`, `TabId`, `VerdictInfo`, `Beat`, `Scenario` (+181 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `react` connect `App.tsx` to `Dock.tsx`, `plugins`, `DriftAct.tsx`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `ask_with_tools()` connect `reference_agent.py` to `mandate_attacks.py`, `supabase_client.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `GroqModel` connect `GroqModel` to `supabase_client.py`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `ask_with_tools()` (e.g. with `load_coupons()` and `unresolved_critical_refs()`) actually correct?**
  _`ask_with_tools()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `NAV`, `TabId`, `VerdictInfo` to the rest of the system?**
  _186 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.07407407407407407 - nodes in this community are weakly interconnected._
- **Should `Argus — Agent QA & Monitoring Suite for Agentic Commerce` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
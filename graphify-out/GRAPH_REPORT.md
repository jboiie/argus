# Graph Report - argus  (2026-09-07)

## Corpus Check
- 81 files · ~276,950 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 594 nodes · 1103 edges · 38 communities (31 shown, 7 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `75b8e4ae`
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
- data.ts
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify
- extraction-spec.md
- reference_agent.py
- ui.tsx
- DriftAct.tsx
- get_client
- .a_generate
- Design Notes
- Bugs & Fixes
- App.tsx
- Argus — Data Model
- mandate_attacks.py
- devDependencies
- Findings.tsx
- compilerOptions
- compilerOptions
- plugins
- Argus dashboard (web)
- verify-rls.mjs
- tsconfig.json
- razorpay_mcp.py
- supabase.ts
- sampler.py
- index.tsx

## God Nodes (most connected - your core abstractions)
1. `get_client()` - 23 edges
2. `ask_with_tools()` - 20 edges
3. `GroqModel` - 19 edges
4. `compilerOptions` - 18 edges
5. `react` - 16 edges
6. `execute_tool_call()` - 15 edges
7. `create_run()` - 15 edges
8. `end_run()` - 15 edges
9. `compilerOptions` - 15 edges
10. `ask_async()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `main()` --indirect_call--> `ask_with_tools()`  [INFERRED]
  redteam/mandate_attacks.py → agent/reference_agent.py
- `check_self_consistency()` --uses--> `GroqModel`  [INFERRED]
  drift/self_consistency.py → redteam/groq_model.py
- `run_scenario()` --calls--> `clear_cart()`  [EXTRACTED]
  redteam/mandate_attacks.py → agent/cart.py
- `unresolved_critical_refs()` --calls--> `fetch_unresolved_critical_refs()`  [EXTRACTED]
  agent/drift_guard.py → telemetry/supabase_client.py
- `unresolved_critical_refs()` --calls--> `get_client()`  [EXTRACTED]
  agent/drift_guard.py → telemetry/supabase_client.py

## Import Cycles
- None detected.

## Communities (38 total, 7 thin omitted)

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

### Community 8 - "data.ts"
Cohesion: 0.17
Nodes (20): Conversation(), Untrusted(), ASI_DISPLAY_NAMES, computeFalsePositiveCost(), driftCauseBreakdown(), driftIncidentsOverTime(), EXCLUDED_LABEL_SUFFIXES, EXCLUDED_RUN_LABELS (+12 more)

### Community 13 - "reference_agent.py"
Cohesion: 0.07
Nodes (59): add_item(), apply_coupon(), _cart(), clear_cart(), compute_total(), demo(), load_coupons(), load_products() (+51 more)

### Community 14 - "ui.tsx"
Cohesion: 0.19
Nodes (15): RunSelector(), Empty(), LoadingView(), Note(), ScrollX(), Select(), Tag(), Td() (+7 more)

### Community 15 - "DriftAct.tsx"
Cohesion: 0.13
Nodes (22): CompletionCard(), Panel(), Stamp(), Stat(), StatStrip(), RunCtl, DemoFindings(), Beat (+14 more)

### Community 16 - "get_client"
Cohesion: 0.07
Nodes (61): Graceful-degradation gate - PROJECT_DESC.md Section 4.4 / DataModel.md's Drift…, DeepEvalBaseLLM, classify_drift_cause(), classify_severity(), demo(), _git_history_values(), _load_ground_truth(), drift_cause and severity classification - build step 19 (PROJECT_DESC.md… (+53 more)

### Community 17 - ".a_generate"
Cohesion: 0.27
Nodes (8): BadRequestError, RateLimitError, _is_empty_generation(), BaseModel, Pydantic's default model_json_schema() doesn't satisfy Groq's strict…, True for the transient case: Groq's strict-schema mode occasionally returns 400…, _retry_after_seconds(), _to_strict_schema()

### Community 19 - "Design Notes"
Cohesion: 0.09
Nodes (20): Dashboard, Design Notes, Naming, Post-deployment: the drift sentinel, Practical constraints that shaped the build, Pre-deployment: the red-team harness, Reference agent, Reproducing the numbers (+12 more)

### Community 21 - "App.tsx"
Cohesion: 0.19
Nodes (15): react, App(), NAV, TabId, Shuffle(), ShuffleDirection, ShuffleProps, Spotlight() (+7 more)

### Community 22 - "Argus — Data Model"
Cohesion: 0.17
Nodes (11): Argus — Data Model, Cross-cutting conventions, Currency convention, Entity 0: Run (Supabase), Entity 1: Product (`catalog.json`), Entity 2.5: Coupon (`coupons.json`), Entity 2: Policy (`policies.json`), Entity 3: Mandate (logged per authorization attempt, Supabase) (+3 more)

### Community 24 - "mandate_attacks.py"
Cohesion: 0.17
Nodes (18): _AttackEventShim, log_to_supabase(), main(), print_results(), Targeted mandate-bypass scenarios - the attacks DeepTeam's generic single-turn…, A real UUID, not a readable slug. mandates.session_id and…, ask_fn(session_id, run_id, message) -> str. Injected rather than imported so…, Attack scenarios only - the control is a suite-validity check, not an attack,… (+10 more)

### Community 25 - "devDependencies"
Cohesion: 0.04
Nodes (45): gsap, @gsap/react, lucide-react, motion, oxlint, react, react-dom, recharts (+37 more)

### Community 26 - "Findings.tsx"
Cohesion: 0.24
Nodes (6): Iris(), Record(), Reveal(), EXHIBITS, Findings(), findStagedDrift()

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
Cohesion: 0.33
Nodes (5): Argus dashboard (web), Build, Local, Rendering untrusted text, Why a static SPA and not a backend

### Community 34 - "razorpay_mcp.py"
Cohesion: 0.43
Nodes (6): _auth_header(), call_tool(), demo(), list_tools(), MCP client wiring against Razorpay's remote MCP server. Connects with the…, Read-only: returns the names of tools Razorpay's MCP server exposes.

### Community 35 - "supabase.ts"
Cohesion: 0.40
Nodes (4): anonKey, isConfigured, supabase, url

### Community 36 - "sampler.py"
Cohesion: 0.12
Nodes (26): AsyncOpenAI, check_faithfulness(), check_numeric(), demo(), DriftCheckResult, _extract_number(), _judge_client(), Ground-truth diffing: exact-match for numeric fields, RAGAS Faithfulness for… (+18 more)

### Community 42 - "index.tsx"
Cohesion: 0.06
Nodes (25): Dock(), DockItemData, Hoverable, Step(), Stepper(), StepperProps, stepVariants, rawSleep() (+17 more)

## Knowledge Gaps
- **185 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+180 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_client()` connect `get_client` to `mandate_attacks.py`, `sampler.py`, `reference_agent.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `react` connect `App.tsx` to `data.ts`, `index.tsx`, `ui.tsx`, `DriftAct.tsx`, `plugins`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `GroqModel` connect `get_client` to `.a_generate`, `sampler.py`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `GroqModel` (e.g. with `check_self_consistency()` and `main()`) actually correct?**
  _`GroqModel` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _185 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.07407407407407407 - nodes in this community are weakly interconnected._
- **Should `reference_agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07341269841269842 - nodes in this community are weakly interconnected._
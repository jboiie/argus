# Graph Report - argus  (2026-09-08)

## Corpus Check
- 81 files · ~276,866 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 596 nodes · 1085 edges · 40 communities (31 shown, 9 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 19 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5a90a366`
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
- App.tsx
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify
- extraction-spec.md
- reference_agent.py
- RedTeamAct.tsx
- DriftAct.tsx
- supabase_client.py
- .a_generate
- Design Notes
- Bugs & Fixes
- index.tsx
- Argus — Data Model
- mandate_attacks.py
- devDependencies
- MandateAct.tsx
- compilerOptions
- compilerOptions
- plugins
- Argus dashboard (web)
- verify-rls.mjs
- tsconfig.json
- Dock.tsx
- Demo
- sampler.py
- Client
- BaseModel
- Stepper.tsx

## God Nodes (most connected - your core abstractions)
1. `ask_with_tools()` - 20 edges
2. `get_client()` - 20 edges
3. `compilerOptions` - 18 edges
4. `GroqModel` - 17 edges
5. `react` - 16 edges
6. `execute_tool_call()` - 15 edges
7. `compilerOptions` - 15 edges
8. `ask_async()` - 14 edges
9. `create_run()` - 14 edges
10. `end_run()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `main()` --indirect_call--> `ask_with_tools()`  [INFERRED]
  redteam/mandate_attacks.py → agent/reference_agent.py
- `run_and_log()` --calls--> `log_session_turn()`  [INFERRED]
  drift/sampler.py → telemetry/supabase_client.py
- `main()` --calls--> `create_run()`  [INFERRED]
  drift/sampler.py → telemetry/supabase_client.py
- `main()` --calls--> `end_run()`  [INFERRED]
  drift/sampler.py → telemetry/supabase_client.py
- `main()` --calls--> `get_client()`  [INFERRED]
  drift/sampler.py → telemetry/supabase_client.py

## Import Cycles
- None detected.

## Communities (40 total, 9 thin omitted)

### Community 0 - "audit.py"
Cohesion: 0.38
Nodes (6): compute_false_positive_cost(), demo(), print_audit_trail(), Audit trail + false-positive cost metric for the drift sentinel. Cost model is…, incidents: drift_incidents rows as returned by the Supabase client (plain…, Full per-incident detail - question, expected/actual, score, classification,…

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

### Community 8 - "App.tsx"
Cohesion: 0.06
Nodes (64): react, App(), NAV, TabId, Conversation(), Iris(), RunSelector(), Shuffle() (+56 more)

### Community 13 - "reference_agent.py"
Cohesion: 0.06
Nodes (60): add_item(), apply_coupon(), _cart(), clear_cart(), compute_total(), demo(), load_coupons(), load_products() (+52 more)

### Community 14 - "RedTeamAct.tsx"
Cohesion: 0.22
Nodes (11): rawSleep(), RunCtl, sleep(), typeInto(), play(), play(), Attack, ATTACK_ORDER (+3 more)

### Community 15 - "DriftAct.tsx"
Cohesion: 0.22
Nodes (7): CompletionCard(), Beat, CategoryKey, DriftAct(), Scenario, SCENARIOS, VerdictInfo

### Community 16 - "supabase_client.py"
Cohesion: 0.08
Nodes (49): _log_mandate_safe(), DataModel.md Entity 3: logged for every mandate creation attempt, regardless of…, DeepEvalBaseLLM, Commerce-specific vulnerabilities not covered by OWASP_ASI_2026's standard…, demo(), GroqModel, Groq-backed judge/simulator model for DeepTeam - keeps attack generation and…, demo() (+41 more)

### Community 17 - ".a_generate"
Cohesion: 0.27
Nodes (8): BadRequestError, RateLimitError, _is_empty_generation(), BaseModel, Pydantic's default model_json_schema() doesn't satisfy Groq's strict…, True for the transient case: Groq's strict-schema mode occasionally returns 400…, _retry_after_seconds(), _to_strict_schema()

### Community 19 - "Design Notes"
Cohesion: 0.09
Nodes (20): Dashboard, Design Notes, Naming, Post-deployment: the drift sentinel, Practical constraints that shaped the build, Pre-deployment: the red-team harness, Reference agent, Reproducing the numbers (+12 more)

### Community 21 - "index.tsx"
Cohesion: 0.25
Nodes (8): DemoFindings(), DriftUpdate, AUTO_SEQUENCE, DEMO_NAV, DemoTab, SPEEDS, MandateUpdate, RedTeamRow

### Community 22 - "Argus — Data Model"
Cohesion: 0.17
Nodes (11): Argus — Data Model, Cross-cutting conventions, Currency convention, Entity 0: Run (Supabase), Entity 1: Product (`catalog.json`), Entity 2.5: Coupon (`coupons.json`), Entity 2: Policy (`policies.json`), Entity 3: Mandate (logged per authorization attempt, Supabase) (+3 more)

### Community 24 - "mandate_attacks.py"
Cohesion: 0.17
Nodes (18): _AttackEventShim, log_to_supabase(), main(), print_results(), Targeted mandate-bypass scenarios - the attacks DeepTeam's generic single-turn…, A real UUID, not a readable slug. mandates.session_id and…, ask_fn(session_id, run_id, message) -> str. Injected rather than imported so…, Attack scenarios only - the control is a suite-validity check, not an attack,… (+10 more)

### Community 25 - "devDependencies"
Cohesion: 0.04
Nodes (45): gsap, @gsap/react, lucide-react, motion, oxlint, react, react-dom, recharts (+37 more)

### Community 26 - "MandateAct.tsx"
Cohesion: 0.25
Nodes (5): MandateAct(), Scenario, SCENARIO_ORDER, SCENARIOS, Controls()

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

### Community 34 - "Dock.tsx"
Cohesion: 0.29
Nodes (3): Dock(), DockItemData, Hoverable

### Community 35 - "Demo"
Cohesion: 0.40
Nodes (3): setSpeed(), Demo(), changeSpeed()

### Community 36 - "sampler.py"
Cohesion: 0.08
Nodes (43): ask_async(), Async single-turn Q&A, same grounding as ask() - used by the drift sampler…, AsyncOpenAI, BaseModel, classify_drift_cause(), classify_severity(), demo(), _git_history_values() (+35 more)

### Community 42 - "Stepper.tsx"
Cohesion: 0.15
Nodes (6): Step(), Stepper(), StepperProps, stepVariants, CompletedActs, Overview()

## Knowledge Gaps
- **185 isolated node(s):** `Beat`, `CategoryKey`, `Scenario`, `VerdictInfo`, `Scenario` (+180 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `react` connect `App.tsx` to `Dock.tsx`, `Stepper.tsx`, `RedTeamAct.tsx`, `DriftAct.tsx`, `index.tsx`, `MandateAct.tsx`, `plugins`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `get_client()` connect `supabase_client.py` to `mandate_attacks.py`, `sampler.py`, `reference_agent.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Why does `ask_with_tools()` connect `reference_agent.py` to `mandate_attacks.py`, `supabase_client.py`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `get_client()` (e.g. with `_log_mandate_safe()` and `main()`) actually correct?**
  _`get_client()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `GroqModel` (e.g. with `main()` and `main()`) actually correct?**
  _`GroqModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Beat`, `CategoryKey`, `Scenario` to the rest of the system?**
  _185 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.07407407407407407 - nodes in this community are weakly interconnected._
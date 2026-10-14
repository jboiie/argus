# Graph Report - argus  (2026-10-14)

## Corpus Check
- 100 files · ~392,466 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 752 nodes · 1350 edges · 50 communities (38 shown, 12 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 31 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d855fb9c`
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
- sampler.py
- index.tsx
- Laya Integration — Plan (Argus side)
- get_client
- faithfulness_variants.py
- Argus: Agent QA and Monitoring Suite for Agentic Commerce
- Bugs & Fixes
- Faithfulness review set
- Argus — Data Model
- Client
- devDependencies
- laya_cascade.py
- compilerOptions
- compilerOptions
- plugins
- Argus dashboard (web)
- verify-rls.mjs
- tsconfig.json
- test_self_check_no_network.py
- reference_agent.py
- Client
- BaseModel
- Drift.tsx
- Stepper.tsx
- apply_faithfulness_review.py
- DriftCheckResult
- LayaDriftScoreLog
- mandate_attacks.py
- Demo
- Findings.tsx
- Dock.tsx
- layaEval.ts
- Shuffle.tsx

## God Nodes (most connected - your core abstractions)
1. `get_client()` - 21 edges
2. `ask_with_tools()` - 20 edges
3. `compilerOptions` - 18 edges
4. `GroqModel` - 17 edges
5. `react` - 16 edges
6. `create_run()` - 15 edges
7. `end_run()` - 15 edges
8. `compilerOptions` - 15 edges
9. `ask_async()` - 14 edges
10. `execute_tool_call()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `demo()` --calls--> `check_numeric()`  [INFERRED]
  telemetry/supabase_client.py → drift/diff.py
- `cascade_check_faithfulness()` --calls--> `laya_label()`  [EXTRACTED]
  drift/laya_cascade_check.py → redteam/laya_cascade.py
- `main()` --indirect_call--> `ask_with_tools()`  [INFERRED]
  redteam/mandate_attacks.py → agent/reference_agent.py
- `log_laya_drift_score()` --uses--> `LayaDriftScoreLog`  [INFERRED]
  telemetry/supabase_client.py → drift/laya_cascade_check.py
- `check_self_consistency()` --calls--> `GroqModel`  [EXTRACTED]
  drift/self_consistency.py → redteam/groq_model.py

## Import Cycles
- None detected.

## Communities (50 total, 12 thin omitted)

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
Cohesion: 0.11
Nodes (30): App(), NAV, TabId, Spotlight(), LoadingView(), ASI_DISPLAY_NAMES, computeAsrByCategory(), EXCLUDED_LABEL_SUFFIXES (+22 more)

### Community 13 - "sampler.py"
Cohesion: 0.06
Nodes (56): ask_async(), Async single-turn Q&A, same grounding as ask() - used by the drift sampler…, AsyncOpenAI, classify_drift_cause(), classify_severity(), demo(), _git_history_values(), _load_ground_truth() (+48 more)

### Community 14 - "index.tsx"
Cohesion: 0.09
Nodes (33): CompletionCard(), Reveal(), Stamp(), rawSleep(), RunCtl, sleep(), typeInto(), DemoFindings() (+25 more)

### Community 15 - "Laya Integration — Plan (Argus side)"
Cohesion: 0.14
Nodes (13): Background, Known limitations carried into Phase 1, Laya cascade — plan for steps 2-5 (2026-09-26, plan only, not built), Laya cascade — pre-flight audit (2026-09-26), Laya Integration — Plan (Argus side), Phase 0 results (measured on this machine), Phase 1 — Argus build order, Phase 2 — plan only, cross-reference (+5 more)

### Community 16 - "get_client"
Cohesion: 0.06
Nodes (60): demo(), Graceful-degradation gate - see DataModel.md's Drift Incident entity for the…, unresolved_critical_refs(), _log_mandate_safe(), DataModel.md Entity 3: logged for every mandate creation attempt, regardless of…, BadRequestError, Client, DeepEvalBaseLLM (+52 more)

### Community 17 - "faithfulness_variants.py"
Cohesion: 0.12
Nodes (32): load_ground_truth(), BaseModel, _cell(), check_faithful_paraphrase_numbers(), check_stale_number(), check_substance(), dedupe(), generate_live_samples() (+24 more)

### Community 19 - "Argus: Agent QA and Monitoring Suite for Agentic Commerce"
Cohesion: 0.06
Nodes (31): Dashboard, Design Notes, Naming, Post-deployment: the drift sentinel, Practical constraints that shaped the build, Pre-deployment: the red-team harness, Reference agent, Reproducing the numbers (+23 more)

### Community 21 - "Faithfulness review set"
Cohesion: 0.22
Nodes (8): contradicted_claim, fabricated_exception, faithful_paraphrase, Faithfulness review set, Flagged by automated checks, Live agent answers (unknown label), stale_number, unsupported_addition

### Community 22 - "Argus — Data Model"
Cohesion: 0.17
Nodes (11): Argus — Data Model, Cross-cutting conventions, Currency convention, Entity 0: Run (Supabase), Entity 1: Product (`catalog.json`), Entity 2.5: Coupon (`coupons.json`), Entity 2: Policy (`policies.json`), Entity 3: Mandate (logged per authorization attempt, Supabase) (+3 more)

### Community 25 - "devDependencies"
Cohesion: 0.04
Nodes (45): gsap, @gsap/react, lucide-react, motion, oxlint, react, react-dom, recharts (+37 more)

### Community 26 - "laya_cascade.py"
Cohesion: 0.08
Nodes (47): Path, apply_temperature(), class_balanced_nll(), compute_ece(), fit_temperature(), load_calibration_rows(), main(), Step 3.2 (Laya cascade): temperature refit on the calibration split only,… (+39 more)

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

### Community 35 - "test_self_check_no_network.py"
Cohesion: 0.47
Nodes (5): Exception, _blocked_connect(), main(), NetworkCallAttempted, Regression test: --self-check must never touch the network. Blocks…

### Community 36 - "reference_agent.py"
Cohesion: 0.07
Nodes (55): add_item(), apply_coupon(), _cart(), clear_cart(), compute_total(), demo(), load_coupons(), load_products() (+47 more)

### Community 39 - "Drift.tsx"
Cohesion: 0.20
Nodes (21): react, Conversation(), RunSelector(), Empty(), Note(), Panel(), ScrollX(), Select() (+13 more)

### Community 40 - "Stepper.tsx"
Cohesion: 0.15
Nodes (6): Step(), Stepper(), StepperProps, stepVariants, CompletedActs, Overview()

### Community 41 - "apply_faithfulness_review.py"
Cohesion: 0.67
Nodes (3): apply(), main(), One-time application of the user's manual review of data/faithfulness_review.md…

### Community 44 - "mandate_attacks.py"
Cohesion: 0.17
Nodes (18): _AttackEventShim, log_to_supabase(), main(), print_results(), Targeted mandate-bypass scenarios - the attacks DeepTeam's generic single-turn…, A real UUID, not a readable slug. mandates.session_id and…, ask_fn(session_id, run_id, message) -> str. Injected rather than imported so…, Attack scenarios only - the control is a suite-validity check, not an attack,… (+10 more)

### Community 45 - "Demo"
Cohesion: 0.40
Nodes (3): setSpeed(), Demo(), changeSpeed()

### Community 47 - "Findings.tsx"
Cohesion: 0.18
Nodes (10): Iris(), Record(), computeFalsePositiveCost(), driftCauseBreakdown(), driftIncidentsOverTime(), fetchLayaDriftScores(), Drift(), EXHIBITS (+2 more)

### Community 51 - "Dock.tsx"
Cohesion: 0.29
Nodes (3): Dock(), DockItemData, Hoverable

### Community 52 - "layaEval.ts"
Cohesion: 0.29
Nodes (6): OPERATING_POINTS, SWEEP_CURVE, SweepCurvePoint, TEST_CLAIMS, TEST_COMPARISON, TestComparisonRow

### Community 54 - "Shuffle.tsx"
Cohesion: 0.50
Nodes (3): Shuffle(), ShuffleDirection, ShuffleProps

## Knowledge Gaps
- **215 isolated node(s):** `Beat`, `CategoryKey`, `Scenario`, `VerdictInfo`, `DemoTab` (+210 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_client()` connect `get_client` to `mandate_attacks.py`, `sampler.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `ask_with_tools()` connect `reference_agent.py` to `get_client`, `faithfulness_variants.py`, `mandate_attacks.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `react` connect `Drift.tsx` to `App.tsx`, `Stepper.tsx`, `index.tsx`, `Dock.tsx`, `Shuffle.tsx`, `plugins`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `ask_with_tools()` (e.g. with `load_coupons()` and `unresolved_critical_refs()`) actually correct?**
  _`ask_with_tools()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `GroqModel` (e.g. with `main()` and `main()`) actually correct?**
  _`GroqModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Beat`, `CategoryKey`, `Scenario` to the rest of the system?**
  _215 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.07407407407407407 - nodes in this community are weakly interconnected._
# Argus — Data Model

Shared schema referenced by the reference agent, red-team harness, drift sentinel, and dashboard. Ground truth (Product, Policy) lives in flat JSON files; everything else is logged to Supabase.

## Cross-cutting conventions

- **IDs**: every `*_id` field is a client-generated UUIDv4, not an auto-increment integer. Needed because Mandate ↔ Attack Event ↔ Session cross-reference each other by ID, and a crashed/replayed run must be able to generate new rows without collision.
- **Timestamps**: stored UTC everywhere (`timestamptz`), converted to local only at display time. The build spans multiple days plus a round-the-clock keep-alive script — mixed timezones would scramble the "drift over time" chart's ordering.
- **Fixed-vocabulary strings** (`asi_category`, `check_type`, and any other category-like field): validated against a fixed set at write time, not free strings. Written by multiple code paths (custom vulnerabilities, DeepTeam's own categories, the drift sampler) — an uncaught typo (`"ASI3"` vs `"ASI03"`) silently splits one dashboard category into two with no error thrown.
- **Ground-truth ID stability**: no database-level foreign key is possible into a JSON file, so nothing stops `catalog.json`/`policies.json` IDs from being renamed or deleted mid-build — which would orphan historical Mandate/Attack Event/Drift Incident rows. Rule: only add or edit values during the build, **never delete or rename an existing ID**. A "removed product" attack scenario uses a clearly separate fake ID, not a deleted real one.
- **Security (public repo)**: the repo is public and Supabase's anon key ships client-side by design — without Row Level Security this is a full read/write hole (see [CVE-2025-48757](https://nvd.nist.gov/vuln/detail/CVE-2025-48757), 303 exposed endpoints across 170 apps from exactly this misconfiguration). Before the repo goes public: never commit keys (`.env` stays gitignored; Streamlit Cloud's secrets manager holds the deployed app's copy); enable RLS on every table, no exceptions; give the public dashboard a `SELECT`-only policy; keep `INSERT`/`UPDATE` behind the service-role key, used only by harness/sentinel backend scripts, never in the Streamlit app's code path.

## Currency convention

**Rupees everywhere except the Razorpay API boundary.** `Product.price` and `Mandate.amount` inconsistency risk (Razorpay requires the smallest currency unit — paise — on every Payment Link/Order call) is handled like this:

- `Product.price` — rupees (decimal). Matches what the agent says in conversation and what the drift sentinel's exact-match check compares against.
- `Mandate.amount` — paise (integer). This is the number that actually reaches Razorpay, so it's stored in Razorpay's native unit to avoid converting twice in two places.
- Conversion (rupees → paise, ×100) happens exactly once, at the point a Mandate is built from a Product lookup. No other file performs this conversion.

## Entity 1: Product (`catalog.json`)

Flat catalog, 5–10 products, no variants — keeps the drift sentinel's numeric diff a single-field comparison.

| Field | Type | Notes |
|---|---|---|
| `id` | string | e.g. `"prod_001"` |
| `name` | string | |
| `price` | number | rupees — see currency convention above |
| `description` | string | plain text only, no markdown/HTML — this is the prompt-injection attack surface (Section 4.3) |
| `category` | string | optional |
| `stock` | integer | optional — only if an out-of-stock scenario is in scope |

## Entity 2: Policy (`policies.json`)

One row per **atomic claim**, not one row per topic — a topic like "refund" spans multiple rows if it bundles multiple facts ("30-day window", "receipt required", "no refunds on sale items"). Keeps the staged drift injection a one-row swap instead of an edit inside a blob, and maps more precisely onto RAGAS's own per-claim decomposition.

| Field | Type | Notes |
|---|---|---|
| `id` | string | e.g. `"policy_refund_window"` |
| `topic` | string | e.g. `"refund"`, `"shipping"` — groups related claim rows; list open, filled in during reference agent build |
| `claim` | string | one atomic fact — the ground-truth text RAGAS Faithfulness checks a response claim against |
| `category` | string | optional |

## Entity 3: Mandate (logged per authorization attempt, Supabase)

Logged for **every** mandate creation attempt, regardless of whether a real Razorpay call fires — Supabase rows are free at this volume. The 30-link cap only limits the real API call, gated separately.

| Field | Type | Notes |
|---|---|---|
| `mandate_id` | string (UUID) | |
| `session_id` | string | |
| `scope` | enum | `purchase` \| `refund` \| `discount_application` |
| `amount` | integer | paise — see currency convention above |
| `product_id` | string | references `Product.id` |
| `authorized_at` | timestamptz | |
| `expires_at` | timestamptz | mandate validity window — without this there's no way to test or demo a **replay attack** (reusing an old, legitimately-issued mandate to authorize a new action), a well-known attack class adjacent to ASI03. `"mandate_replay"` should be an explicit `vulnerability` value in Attack Event once the harness covers it. |
| `user_confirmed` | boolean | did a real user-confirmation turn precede this |
| `status` | enum | `authorized` \| `denied` \| `bypassed` — the actual outcome, needed to score ASI03 (Identity & Privilege Abuse) |
| `is_live_demo` | boolean | intent flag — whether this mandate is allowed to trigger a real Razorpay call |
| `real_call_fired` | boolean | actual outcome — whether a real Razorpay call happened (may diverge from `is_live_demo` on error/stub) |

## Entity 4: Attack Event (red-team harness log, Supabase)

Fields matched against DeepTeam's actual test-case objects, not assumed.

| Field | Type | Notes |
|---|---|---|
| `attack_id` | string (UUID) | |
| `run_id` | string (UUID) | groups rows into one campaign — separates "ASR this run" from "ASR cumulative," and lets a crashed/rerun batch's partial rows be identified and excluded instead of silently padding totals |
| `timestamp` | timestamptz | |
| `asi_category` | string | e.g. `"ASI03"` — validated against a fixed set at write time, see Cross-cutting conventions |
| `vulnerability` | string | e.g. `"unauthorized_refund"` — the vulnerability under test |
| `attack_method` | string | the technique used (Roleplay, PromptInjection, etc.) — DeepTeam provides this separately from `vulnerability`; needed for "which technique gets past guardrails most" breakdown |
| `prompt` | string | for multi-turn attacks (DeepTeam's progression/multi-turn strategies), holds the final triggering turn only — full build-up across turns lives in Session/Conversation Turn under the same `session_id` |
| `response` | string | same multi-turn convention as `prompt` — final turn only |
| `reason` | string | DeepTeam's judge justification for the score — required for the full audit trail (Section 4.5) |
| `bypassed` | boolean | **DeepTeam convention is `score: 1 = defended, 0 = vulnerable` — inverted from this field. Flip on ingest, never pass through raw.** |
| `session_id` | string | |
| `mandate_id` | string, optional | FK — pins down which mandate a bypass attempt targeted, since a session can contain multiple mandates |

## Entity 5: Drift Incident (drift sentinel log, Supabase)

| Field | Type | Notes |
|---|---|---|
| `incident_id` | string (UUID) | |
| `run_id` | string (UUID) | groups rows into one sampler run — needed for a clean before/after comparison across the deliberately-injected drift event (Section 4.4), and to exclude a crashed/rerun batch's partial rows |
| `timestamp` | timestamptz | |
| `check_type` | enum | `numeric` \| `faithfulness` \| `self_consistency` — validated at write time |
| `question` | string | |
| `ground_truth_ref` | string | `Product.id` or `Policy.id` — for traceability only |
| `ground_truth_type` | enum | `product` \| `policy` — disambiguates which table `ground_truth_ref` points into (polymorphic FK, no real constraint possible without this) |
| `expected` | value, nullable | **snapshot of the ground-truth value at check-time, not a live lookup via `ground_truth_ref`.** A later catalog/policy edit must not retroactively change past rows — this is what keeps the deliberately-injected drift demo timeline honest. `null` for `self_consistency` rows (no external ground truth applies). |
| `actual` | value | the agent's answer. For `self_consistency` rows: the majority answer across samples. |
| `sampled_responses` | array, optional | populated only for `self_consistency` rows — the N sampled answers the majority/score were computed from |
| `score` | float (numeric), nullable | must be a real float column, not int/boolean — holds both DeepTeam's binary 0/1 and RAGAS/self-consistency's continuous 0–1 scores. null for `numeric` (exact match is binary). For `self_consistency`: agreement rate across samples. |
| `flagged` | boolean | |
| `reviewed_at` | timestamptz, nullable | when a human reviewed this row for the false-positive cost metric — null means not yet reviewed |
| `is_false_positive` | boolean, nullable | the review's verdict, separate from whether it was reviewed at all. null = not yet reviewed, true/false = the actual finding. (Splits what was one conflated `false_positive_reviewed` boolean.) |
| `session_id` | string | which conversation produced this incident — required for the audit trail |

## Entity 6: Session / Conversation Turn (Supabase, full transcripts persisted)

Persisted in full — this is synthetic test traffic against Argus's own reference agent, not real user data, so there's no privacy exposure to weigh, and volume (thousands of rows over the build, not millions) isn't a real cost. Needed to reconstruct multi-turn attacks, where a bypass at turn 4 only makes sense in light of turns 1–3.

**Concurrency**: session memory during a live conversation is a plain in-process store, keyed by `session_id`. Turns within one session are never interleaved concurrently — the harness may run multiple *sessions* in parallel, but each session's own turns execute sequentially. If that assumption stops holding (e.g. a future async fan-out within a single session), session state moves external (Supabase or Redis) instead of in-process.

**Uniqueness**: `(session_id, turn_index)` is a unique constraint — nothing else stops two rows from claiming the same turn in the same session.

| Field | Type | Notes |
|---|---|---|
| `session_id` | string | |
| `session_type` | enum | `smoke_test` \| `drift_sampler` \| `attack` — distinguishes which producer created the session; without it, benign traffic can't be filtered from attack noise, and the graceful-failure demo session can't be pulled cleanly for the video |
| `turn_index` | integer | unique together with `session_id` |
| `role` | enum | `user` \| `agent` |
| `content` | string | |
| `timestamp` | timestamptz | |

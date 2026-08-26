# Argus — Data Model

Shared schema referenced by the reference agent, red-team harness, drift sentinel, and dashboard. Ground truth (Product, Policy) lives in flat JSON files; everything else is logged to Supabase.

## Cross-cutting conventions

- **IDs**: every `*_id` field is a client-generated UUIDv4, not an auto-increment integer. Needed because Mandate ↔ Attack Event ↔ Session cross-reference each other by ID, and a crashed/replayed run must be able to generate new rows without collision.
- **Timestamps**: stored UTC everywhere (`timestamptz`), converted to local only at display time. The build spans multiple days plus a round-the-clock keep-alive script — mixed timezones would scramble the "drift over time" chart's ordering.
- **Fixed-vocabulary strings** (`asi_category`, `check_type`, and any other category-like field): validated against a fixed set at write time, not free strings. Written by multiple code paths (custom vulnerabilities, DeepTeam's own categories, the drift sampler) — an uncaught typo (`"ASI3"` vs `"ASI03"`) silently splits one dashboard category into two with no error thrown.
- **Ground-truth ID stability**: no database-level foreign key is possible into a JSON file, so nothing stops `catalog.json`/`policies.json` IDs from being renamed or deleted mid-build — which would orphan historical Mandate/Attack Event/Drift Incident rows. Rule: only add or edit values during the build, **never delete or rename an existing ID**. A "removed product" attack scenario uses a clearly separate fake ID, not a deleted real one.
- **Security (public repo)**: the repo is public and Supabase's anon key ships client-side by design — without Row Level Security this is a full read/write hole (see [CVE-2025-48757](https://nvd.nist.gov/vuln/detail/CVE-2025-48757), 303 exposed endpoints across 170 apps from exactly this misconfiguration). Before the repo goes public: never commit keys (`.env` stays gitignored; Streamlit Cloud's secrets manager holds the deployed app's copy); enable RLS on every table, no exceptions; give the public dashboard a `SELECT`-only policy; keep `INSERT`/`UPDATE` behind the service-role key, used only by harness/sentinel backend scripts, never in the Streamlit app's code path.
- **No unsafe HTML rendering**: this is a code-level rule, not a per-field data-model one, because every attacker-influenced free-text field is a candidate — `Product.description`, `Attack Event.prompt`/`response`, `Session Turn.content`. A prompt-injection payload is often literally designed to look like markup or instructions. Never set `unsafe_allow_html=True` anywhere in the dashboard when rendering any of these.

## Currency convention

**Rupees everywhere except the Razorpay API boundary.** `Product.price` and `Mandate.amount` inconsistency risk (Razorpay requires the smallest currency unit — paise — on every Payment Link/Order call) is handled like this:

- `Product.price` — rupees (decimal). Matches what the agent says in conversation and what the drift sentinel's exact-match check compares against.
- `Mandate.amount` — paise (integer). This is the number that actually reaches Razorpay, so it's stored in Razorpay's native unit to avoid converting twice in two places.
- Conversion (rupees → paise, ×100) happens exactly once, at the point a Mandate is built from a Product lookup. No other file performs this conversion.

## Entity 0: Run (Supabase)

Metadata for what `run_id` (on Attack Event and Drift Incident) actually refers to. Without this, "before" vs "after" the staged drift injection (Section 4.4) has to be reconstructed from raw timestamps instead of a one-line query.

| Field | Type | Notes |
|---|---|---|
| `run_id` | string (UUID) | |
| `run_type` | enum | `redteam` \| `drift_sample` — which engine produced this run, without joining out to Attack Event/Drift Incident to find out |
| `started_at` | timestamptz | |
| `ended_at` | timestamptz, nullable | null while the run is in progress |
| `label` | string | validated against a fixed set at write time (same typo-fragmentation risk as `asi_category`/`check_type` — this string is exact-matched to pull "baseline" vs "post-injection" for the one required before/after comparison). e.g. `"phase_a_baseline"`, `"drift_after_price_change"` |
| `notes` | string, optional | free text — e.g. which ground-truth state was active; cross-reference with `DEBUG_JOURNAL.md` |

## Entity 1: Product (`catalog.json`)

Flat catalog, 5–10 products, no variants — keeps the drift sentinel's numeric diff a single-field comparison.

| Field | Type | Notes |
|---|---|---|
| `id` | string | e.g. `"prod_001"` |
| `name` | string | |
| `price` | number | rupees — see currency convention above |
| `description` | string | plain text only, no markdown/HTML — this is the prompt-injection attack surface (Section 4.3); see the no-unsafe-HTML rendering rule under Cross-cutting conventions |
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

## Entity 2.5: Coupon (`coupons.json`)

Ground truth for the cart stretch goal (Section 4.1) — flat file, same pattern as Product/Policy. `agent/cart.py::apply_coupon` is the only place a code gets validated against this; the reference agent never honors a code that isn't listed here and active, no matter how a customer phrases the request.

| Field | Type | Notes |
|---|---|---|
| `code` | string | e.g. `"WELCOME10"` |
| `discount_type` | enum | `percent` \| `flat` |
| `discount_value` | number | percent (0–100) or rupees, depending on `discount_type` |
| `active` | boolean | matches `policy_discount_validity`'s claim — an inactive code must be rejected, never silently honored |

## Entity 3: Mandate (logged per authorization attempt, Supabase)

Logged for **every** mandate creation attempt, regardless of whether a real Razorpay call fires — Supabase rows are free at this volume. The 30-link cap only limits the real API call, gated separately.

| Field | Type | Notes |
|---|---|---|
| `mandate_id` | string (UUID) | |
| `run_id` | string (UUID) | same reasoning as Attack Event/Drift Incident — separates phases, lets a crashed/rerun batch's orphaned rows be identified and excluded |
| `session_id` | string | |
| `scope` | enum | `purchase` \| `refund` \| `discount_application` |
| `amount` | integer | paise, post-discount total — see currency convention above |
| `line_items` | array, nullable | `[{"product_id": str, "quantity": int}, ...]` — the cart stretch goal (Section 4.1) reached; computed server-side (`agent/cart.py::compute_total`) against `catalog.json`'s real prices, never trusted from the model. `null` only on pre-cart historical rows. |
| `coupon_code` | string, nullable | the applied discount code, if any — validated against `coupons.json`'s active list before ever reaching here (see `agent/cart.py::apply_coupon`) |
| `product_id` | string, nullable, deprecated | pre-cart single-product field. Kept only so old rows still read back correctly; new code always writes `line_items` instead. |
| `authorized_at` | timestamptz | |
| `expires_at` | timestamptz | mandate validity window — without this there's no way to test or demo a **replay attack** (reusing an old, legitimately-issued mandate to authorize a new action), a well-known attack class adjacent to ASI03. `"mandate_replay"` should be an explicit `vulnerability` value in Attack Event once the harness covers it. |
| `user_confirmed` | boolean | did a real user-confirmation turn precede this |
| `status` | enum | `authorized` \| `denied` — set once, at creation, by the mandate layer's own real-time check (in scope, not expired, `user_confirmed`). This is the primary write path and covers every mandate, not just ones an attack targets — `mandate_id` on Attack Event is optional, so most mandates (ordinary smoke-test/drift-sampler traffic) never get a linked Attack Event at all. **Immutable once set** — never overwritten in place. If an attack later finds this mandate bypassable, that's a separate fact, not a correction to this field: see `bypass_confirmed_at`. |
| `bypass_confirmed_at` | timestamptz, nullable | set by whatever writes the linked Attack Event row (via `mandate_id`) if an attack got past this mandate's check. Kept separate from `status` so the original authorized/denied record stays an immutable audit trail, not a field that gets mutated after the fact — the kind of thing a panel would poke at on a project pitched around auditability. |
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
| `vulnerability` | string | e.g. `"CommerceManipulation"` — the parent vulnerability, matching DeepTeam's custom-vulnerability API where one vulnerability declares multiple types |
| `vulnerability_type` | string | e.g. `"unauthorized_refund"` — the sub-category under `vulnerability`. Kept separate rather than folded into one field, since a single custom vulnerability can declare several types and collapsing them loses that grouping. |
| `attack_method` | string | the technique used (Roleplay, PromptInjection, etc.) — DeepTeam provides this separately from `vulnerability`/`vulnerability_type`; needed for "which technique gets past guardrails most" breakdown |
| `prompt` | string | for multi-turn attacks (DeepTeam's progression/multi-turn strategies), holds the final triggering turn only — full build-up across turns lives in Session/Conversation Turn under the same `session_id` |
| `response` | string, nullable | same multi-turn convention as `prompt` — final turn only. Nullable for `outcome = errored` (API call never returned a response). |
| `reason` | string, nullable | DeepTeam's judge justification for the score — required for the full audit trail (Section 4.5). Nullable alongside `response`: same cause, `outcome = errored` means no judge ran, so no judge reasoning exists. |
| `outcome` | enum | `bypassed` \| `defended` \| `errored` — not a boolean. DeepTeam's own results track passing/failing/errored as three distinct counts; a free-tier API run will genuinely error sometimes (rate limit, timeout, malformed response), and a boolean forces either silently dropping those rows or miscoding them as a real pass/fail, corrupting ASR. **DeepTeam convention is `score: 1 = defended, 0 = vulnerable` — map to `outcome` on ingest (never pass the raw score through as-is), with a caught API failure mapped to `errored` before it ever reaches DeepTeam's scoring.** |
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
| `ground_truth_ref` | string, nullable | `Product.id` or `Policy.id` — for traceability only. `null` for `self_consistency` rows (build step 17): those check claims not covered by ground truth in the first place, so no real id applies (see `migrate_002_self_consistency_nullable_refs.sql`) |
| `ground_truth_type` | enum, nullable | `product` \| `policy` — disambiguates which table `ground_truth_ref` points into (polymorphic FK, no real constraint possible without this). `null` alongside `ground_truth_ref` for `self_consistency` rows, same reasoning |
| `expected` | value, nullable | **snapshot of the ground-truth value at check-time, not a live lookup via `ground_truth_ref`.** A later catalog/policy edit must not retroactively change past rows — this is what keeps the deliberately-injected drift demo timeline honest. `null` for `self_consistency` rows (no external ground truth applies). |
| `actual` | value | the agent's answer. For `self_consistency` rows: the majority answer across samples. |
| `sampled_responses` | array, optional | populated only for `self_consistency` rows — the N sampled answers the majority/score were computed from |
| `score` | float (numeric), nullable | must be a real float column, not int/boolean — holds both DeepTeam's binary 0/1 and RAGAS/self-consistency's continuous 0–1 scores. null for `numeric` (exact match is binary). For `self_consistency`: agreement rate across samples. |
| `check_status` | enum | `completed` \| `errored` — parallel to Attack Event's `outcome`, same reasoning: a free-tier API failure mid-check (RAGAS/self-consistency call errors) needs a distinct state, not a miscoded `flagged` value. |
| `flagged` | boolean, nullable | `null` when `check_status = errored` — not `false`. A stray `false` on an errored row would read as "checked and clean" to a naive count query, which is wrong: it was never checked. |
| `drift_cause` | enum, nullable | `stale_ground_truth` \| `fabrication` \| `inconsistency` — null when `flagged = false`/`null` (nothing to classify). See classification logic below. |
| `severity` | enum, nullable | `critical` \| `moderate` — null when `flagged = false`/`null`. `critical` when `ground_truth_ref` points to `Product.price` or to a `Policy` whose `topic`/`category` is money-relevant (refunds, discounts, anything a Mandate could act on); `moderate` otherwise. |
| `reviewed_at` | timestamptz, nullable | when a human reviewed this row for the false-positive cost metric — null means not yet reviewed |
| `is_false_positive` | boolean, nullable | the review's verdict, separate from whether it was reviewed at all. null = not yet reviewed, true/false = the actual finding. (Splits what was one conflated `false_positive_reviewed` boolean.) |
| `session_id` | string | which conversation produced this incident — required for the audit trail |

**`drift_cause` classification logic** (computed at write time, when `flagged = true`):
- `stale_ground_truth` — `actual` matches a *prior* (pre-edit) value of the Product/Policy field `ground_truth_ref` points to, not its current value. Requires keeping prior ground-truth values around to check against (e.g. git history of `catalog.json`/`policies.json`, or a local snapshot taken at each edit) — not just the current file.
- `fabrication` — `actual` matches no known past-or-present value for that ground-truth ID at all.
- `inconsistency` — only possible when `check_type = self_consistency`, and entries in `sampled_responses` disagree with each other on the same question.

**Graceful-degradation behavior rule** (reference agent, not the drift sentinel itself): before answering a question, or before authorizing a new Mandate, that touches a `ground_truth_ref` with an unresolved critical incident (`severity = critical` and `reviewed_at IS NULL`), the agent must decline to confirm the claim or hold the Mandate — never repeat the possibly-wrong value. This is the project's one concrete "failure recovery" behavior, demonstrated live rather than just logged. Depends on drift sentinel data existing (build steps 16-20); implement this check as part of that work, not before there are real incidents to check against.

## Entity 6: Session / Conversation Turn (Supabase, full transcripts persisted)

Persisted in full — this is synthetic test traffic against Argus's own reference agent, not real user data, so there's no privacy exposure to weigh, and volume (thousands of rows over the build, not millions) isn't a real cost. Needed to reconstruct multi-turn attacks, where a bypass at turn 4 only makes sense in light of turns 1–3.

**Concurrency**: session memory during a live conversation is a plain in-process store, keyed by `session_id`. Turns within one session are never interleaved concurrently — the harness may run multiple *sessions* in parallel, but each session's own turns execute sequentially. If that assumption stops holding (e.g. a future async fan-out within a single session), session state moves external (Supabase or Redis) instead of in-process.

**Uniqueness**: `(session_id, turn_index)` is a unique constraint — nothing else stops two rows from claiming the same turn in the same session.

| Field | Type | Notes |
|---|---|---|
| `session_id` | string | |
| `run_id` | string (UUID) | same reasoning as the other event tables — same automated runs produce these rows, equally exposed to a mid-run crash |
| `session_type` | enum | `smoke_test` \| `drift_sampler` \| `attack` \| `demo` — distinguishes which producer created the session. `demo` marks a deliberately staged session (graceful-failure refusal, drift-injection clip) so it can be pulled by a plain filter for the video instead of remembering which run happened to be the staged one. |
| `turn_index` | integer | unique together with `session_id` |
| `role` | enum | `user` \| `agent` \| `tool_call` \| `tool_result` — MCP tool invocations (Razorpay payment-link/order calls, etc.) get their own rows, not flattened into an `agent` turn's natural-language text. This is the row Section 4.2's "every money action explainable, bounded and gated" actually depends on: without it, "full transcript" and "auditable money-action trail" are two different claims wearing one name. |
| `content` | string | for `tool_call`: the tool name + arguments (JSON). for `tool_result`: the raw MCP response. for `user`/`agent`: natural-language text. |
| `mandate_id` | string, optional | set on `tool_call` rows that correspond to a money-moving action — ties the tool invocation back to the Mandate that authorized it |
| `timestamp` | timestamptz | |

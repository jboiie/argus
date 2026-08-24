# Bugs & Fixes Reference

Structured catalog of every real bug/gap found during the build — organized by component, not by date. Companion to `DEBUG_JOURNAL.md`, which is the as-it-happened timeline (feeds the video's "what broke" segment). This file is the reference for quick lookup during panel Q&A or when hitting the same class of issue again.

**Update this file every time a real bug/gap is found and fixed** — same rule as `DEBUG_JOURNAL.md`, different shape: entries here are organized by component and structured for scanning, not chronological narrative.

## Format

Each entry: **Symptom** (what you'd observe) → **Root Cause** (why) → **Fix** (what changed) → **Mitigation** (how to avoid/catch it next time).

---

## Reference Agent (`agent/`)

### Empty stub field → model fabricated a fake payment link

- **Symptom:** Agent presented a fake-looking Razorpay short link (`https://rzp.io/i/stubbed`) as if it were real, even though `is_live_demo=False` (no real call made).
- **Root Cause:** Stub tool result had no `short_url` field. Gemini had nothing to point to for "the link," so it pattern-matched what a real one looks like and invented one.
- **Fix:** `agent/tools.py::execute_tool_call` — stub result now includes an explicit `short_url: "[TEST RUN - no real payment link was created]"` placeholder.
- **Mitigation:** Never leave a field blank/missing that a model can plausibly fill in on its own. Any stub/mock result needs an explicit, honest placeholder in every field a real result would have — not an omission.

### Mandate gate accepted an external `user_confirmed` flag

- **Symptom:** Nothing yet visibly broken, but caught during red-team-harness prep: any caller of `ask_with_tools(..., user_confirmed=True)` could just assert confirmation happened, regardless of the actual conversation.
- **Root Cause:** Step 8/9 built `user_confirmed` as a caller-supplied parameter (convenient for controlled smoke tests) without registering that the same parameter would make ASI03 mandate-bypass testing meaningless — there'd be nothing for an attack to actually forge.
- **Fix:** `agent/reference_agent.py::_has_genuine_confirmation()` — deterministic, code-level check over the real transcript (≥2 user turns, latest containing explicit affirmative language via regex). Computed internally, not accepted from the caller.
- **Mitigation:** Any gate meant to be attacked later must derive its decision from data an attacker can actually influence (the conversation), never from a parameter only trusted code paths set.

---

## External API Integration

### Gemini 2.5 Flash-Lite retired for new API keys

- **Symptom:** `404 NOT_FOUND` — "This model models/gemini-2.5-flash-lite is no longer available to new users."
- **Root Cause:** Google retired the model for new keys ahead of full retirement (Oct 16 2026); PROJECT_DESC.md's pricing reference predated the change.
- **Fix:** Switched to `gemini-3.5-flash-lite` in `agent/reference_agent.py`. Corrected pricing in PROJECT_DESC.md too ($0.30/$2.50 per M, not $0.10/$0.40).
- **Mitigation:** Before committing to a model name in a spec doc, live-test it — pricing pages lag behind actual availability changes.

### Razorpay MCP server: docs/README both say `Bearer`, server actually requires `Basic`

- **Symptom:** Every connection attempt returned `401 OAUTH_BAD_TOKEN: "Bad token; invalid JSON"`. The `WWW-Authenticate: Bearer ...` response header made it look like a full OAuth 2.1 flow was needed.
- **Root Cause:** Razorpay's own docs page and GitHub README both state `Authorization: Bearer <base64(key:secret)>`. The actual server expects `Authorization: Basic <base64(key:secret)>` — confirmed via a raw `httpx` POST bypassing the MCP SDK, then found the correct scheme buried in the README's Claude Desktop config JSON snippet.
- **Fix:** `agent/razorpay_mcp.py::_auth_header()` — changed `Bearer` to `Basic`.
- **Mitigation:** When official docs and a live 401 disagree, test the raw HTTP call directly before trusting either the docs prose or an SDK's error message — both were misleading here (docs wrong, SDK's generic 500-style error obscured the real cause).

---

## DeepTeam / Red-Team Harness (`redteam/`)

### `mcp` SDK wraps every failure in nested `ExceptionGroup`s

- **Symptom:** `except MCPError` never matched a real `MCPError` raised deep inside `streamable_http_client`/`ClientSession`'s nested `async with` blocks.
- **Root Cause:** Python 3.11+ exception groups — nested task groups (`streamable_http.py`, `session.py`) each re-wrap child exceptions in their own `ExceptionGroup`, so the leaf `MCPError` ends up several `ExceptionGroup` layers deep.
- **Fix:** Use `except*` or a manual recursive `_leaves()` unwrapper to reach the real exception when debugging.
- **Mitigation:** For any future MCP debugging in this repo, drop to a raw HTTP call first to see the actual server response — faster than fighting the SDK's exception wrapping.

### `GroqModel.a_generate(self, prompt, *args, **kwargs)` silently broke DeepTeam's schema-detection probe

- **Symptom:** `AttributeError: 'str' object has no attribute 'data'` deep inside `deepteam/vulnerabilities/prompt_leakage/prompt_leakage.py`.
- **Root Cause:** DeepTeam detects whether a custom model supports schema-based generation by calling `a_generate(prompt, schema=SomeSchema)` and catching the resulting `TypeError` to fall back to its own plain-text + JSON-parse path. My method's `**kwargs` silently absorbed the `schema` argument instead of raising `TypeError`, so DeepTeam assumed schema support and tried to read `.data` off a plain string.
- **Fix:** Stripped `*args, **kwargs` from `generate`/`a_generate` — strict `(self, prompt: str) -> str` signature, so the schema probe genuinely fails and triggers DeepTeam's fallback.
- **Mitigation:** When implementing a library's documented callback/interface contract, match the signature exactly — don't add convenience `**kwargs`, they can silently break a caller's introspection-based feature detection.

### `openai/gpt-oss-120b` refuses attack-generation prompts outright

- **Symptom:** `"I'm sorry, but I can't help with that."` for every DeepTeam attack-simulation prompt, even in this legitimate, self-targeted, defensive security-testing context.
- **Root Cause:** Model's own safety alignment, independent of any policy on our end — it won't role-play generating adversarial/credential-extraction-style text regardless of framing.
- **Fix:** Switched judge/simulator model to `openai/gpt-oss-20b`, which complies on most (not all) prompt types.
- **Mitigation:** Not every model on a provider's roster is fit for the "attacker simulator" role in a red-team harness — test compliance on a representative sample of the actual attack-generation prompts before committing to a model, not just a generic capability check.

### `qwen/qwen3.6-27b`: hidden reasoning trace breaks JSON parsing, then blows the TPM budget

- **Symptom (1):** Every downstream JSON-parse step failed — response wrapped in `<think>...</think>` before the actual JSON.
- **Root Cause (1):** Qwen on Groq is a reasoning model; its default output includes the full chain-of-thought inline.
- **Fix (1):** `extra_body={"reasoning_format": "hidden"}` on the Groq chat-completions call (Groq-specific param — not a recognized kwarg on the `openai` SDK's typed `create()`, must go through `extra_body`).
- **Symptom (2):** Some responses came back with empty `content` and no error.
- **Root Cause (2):** The hidden reasoning trace still *consumes* completion tokens even though it's not shown. With no `max_tokens` set, heavy reasoning (~2000 tokens on a trivial request) sometimes ate the entire default budget, leaving nothing for the visible answer.
- **Fix (2):** Explicit `max_tokens` ceiling.
- **Symptom (3):** `429 rate_limit_exceeded` — Groq's 8000 TPM free-tier cap on this model, hit even with `max_concurrent=1` (fully serialized).
- **Root Cause (3):** A single call could burn 2000-4000+ tokens on reasoning alone; the free-tier budget can't sustain that per-minute regardless of concurrency.
- **Fix (3):** Abandoned Qwen as the judge model — switched to `openai/gpt-oss-20b` (~4x fewer tokens/call).
- **Mitigation:** For any reasoning-capable model on a token-metered free tier, check `response.usage.completion_tokens_details.reasoning_tokens` before trusting a "it works" result — a low visible-output cost can hide a large real cost, and reasoning consumption doesn't show up unless you look for it specifically.

### `conda run` crashes re-printing captured output with non-ASCII characters

- **Symptom:** `UnicodeEncodeError: 'charmap' codec can't encode character '�'` — `conda run` itself crashes, even though the wrapped Python process succeeded and produced correct output.
- **Root Cause:** `conda run` buffers the subprocess's stdout, then re-prints it through the console's `cp1252` codepage on Windows. Any emoji/non-ASCII in the buffered output (common in `deepteam`'s progress-bar/rich-formatted terminal output) breaks that re-print step.
- **Fix:** Always use `conda run --no-capture-output -n argus ...` for anything that might print non-ASCII — streams directly instead of buffering + re-encoding. (Matches the pattern already used in the sibling Aegis project's own README for exactly this reason.)
- **Mitigation:** Documented in `README.md`'s Setup section as the required invocation pattern for this repo, so it's not rediscovered per-session.

### DeepTeam full-category run: high error rate on Groq free tier — fixed

- **Symptom:** Small-scale `OWASP_ASI_2026` / ASI_03 wiring test: 9 of 10 test cases came back `errored`. `BOLA` and `Agent Identity & Trust Abuse` categories failed at attack-generation entirely (empty input/output); one `RBAC` case failed at judge-scoring (real response, judge's JSON didn't parse).
- **Root Cause:** Two separate causes, found via research (Groq rate-limit docs, DeepTeam/deepeval GitHub issues, Groq structured-outputs docs) after the narrow model-swap fix wasn't enough on its own:
  1. **Invalid JSON from the judge/simulator model.** DeepTeam's own call sites do `await self.simulator_model.a_generate(prompt, schema=SomeSchema)` directly — if the custom model doesn't genuinely support `schema`, it falls back to plain text + `trimAndLoadJson`, which is fragile (any preamble, refusal, or formatting quirk breaks it). Confirmed via deepeval GitHub issues #929/#982 as a known failure mode with custom models.
  2. **Groq free-tier TPM (8000/min)** gets hit even at `max_concurrent=1` once a few calls land in the same window, and DeepTeam's own built-in retry backoff (1s, 2s) is far shorter than Groq's real cooldown (observed up to ~25s).
- **Fix:**
  1. Implemented genuine schema support in `GroqModel.generate`/`a_generate` (real `schema` parameter, not swallowed via `**kwargs`) using Groq's **strict `json_schema` structured-output mode** — confirmed via Groq docs that only `gpt-oss-20b`/`gpt-oss-120b` support `strict: true`, which guarantees schema-valid JSON via constrained decoding (never errors). Pydantic's default `model_json_schema()` doesn't satisfy Groq's strict requirements (every property must be in `required`, every object needs `additionalProperties: false`) — added `_to_strict_schema()` to normalize recursively. DeepTeam now gets a validated pydantic object back directly, skipping the fragile fallback entirely.
  2. Added real retry-with-backoff in `GroqModel` itself: catches `RateLimitError`, reads Groq's actual suggested wait time (response header or parsed from the error message), sleeps that long (+1s buffer), retries up to twice.
- **Result (confirmed at full 10-test-case scale, same ASI_03 category, before/after):**

  | | Before | After |
  |---|---|---|
  | Errored | 9/10 | 1/10 |
  | Bypassed (real finding) | 0/10 | 1/10 |
  | Defended | 1/10 | 8/10 |

  The one remaining error: a single `RBAC/ROLE_BYPASS` case where the model's refusal still didn't fit the schema even after retries (Groq returns `400 json_validate_failed` with the refusal text in `failed_generation` when constrained decoding can't reconcile a refusal with the required schema shape — a real, narrow residual failure mode, not corrupted data). The one bypass is a genuine finding, not noise: under `Prompt Leakage/PERMISSIONS_AND_ROLES`, the agent's refusal ("I am a customer support agent... I don't have information about system upgrades") got scored as a permissions/role exposure — arguably borderline, worth flagging as a candidate for the false-positive-cost metric (Section 4.4) once that's built.
- **New cost discovered:** the fix trades throughput for reliability — this 10-test-case run took ~10 minutes (retry waits under free-tier TPM). Step 15's full-volume run (hundreds of attempts) needs explicit pacing/paid-tier planning as a result, not just reliability.
- **Mitigation:** `ignore_errors=True` (the real default) still matters as a backstop — an isolated genuine refusal becomes one `errored` test case, not a crashed run, matching DataModel.md's `errored` outcome design. If TPM pressure resurfaces at step 15's real volume, Groq's paid Developer tier (pay-as-you-go, no subscription, ~30-40x the free-tier TPM) is the next lever.

### Concurrent DeepTeam tasks thundering-herd the shared Groq rate limit — fixed

- **Symptom:** Custom-vulnerability wiring test (step 12): 6/7 test cases errored completely (empty input/output), while each vulnerability's `a_simulate_attacks()` succeeded fine when called in isolation (same code, same model, no error).
- **Root Cause:** `max_concurrent` in `red_team()` controls DeepTeam's own task-level parallelism, not real API request concurrency. Multiple concurrent tasks (attack generation + judge scoring across several vulnerabilities) all shared the same 8000 TPM budget on one Groq key/model. Each hit 429 independently, each independently retried, and all piled back onto the same still-recovering budget — a thundering herd that could exceed any single call's 2-retry budget even though every call succeeded fine on its own.
- **Fix:** Added a process-wide `asyncio.Semaphore(1)` inside `GroqModel.a_generate`, serializing actual outbound Groq requests regardless of how many DeepTeam tasks are "concurrently" running. Decouples DeepTeam's task parallelism from real API concurrency.
- **Result:** Rerun of the same custom-vulnerability test: 5/7 succeeded (up from 1/7), remaining 2 errors traced to a different, unrelated cause (see below — daily token cap, not concurrency).
- **Mitigation:** When wrapping any rate-limited API as a custom model for a framework with its own internal concurrency setting, don't assume that setting bounds real request concurrency — verify, and serialize at the actual API-call layer if the two are decoupled.

### `RTTurn.metadata` doesn't propagate to `RTTestCase` — session correlation needed a different design

- **Symptom:** Planning Supabase logging (step 14) needed each Attack Event row to carry the `session_id` used during that attack's `model_callback` invocation. Attaching `session_id` to `RTTurn.metadata` and reading it back off the resulting test case seemed like the obvious approach.
- **Root Cause:** Checked against DeepTeam's actual source (`red_teamer.py::_a_attack`) rather than assumed — only `model_response.content`, `.retrieval_context`, and `.tools_called` get copied from the returned `RTTurn` onto the `RTTestCase`. `metadata` is silently dropped.
- **Fix:** Derived `session_id` deterministically from the attack's prompt text (`uuid.uuid5` keyed on `tc.input`) instead of trying to carry a randomly-generated ID through DeepTeam's pipeline. `model_callback.py::session_id_for()` is the single source of truth, called both when creating the session and later when logging — no shared mutable state, no correlation table needed.
- **Mitigation:** Before designing a data flow that depends on a framework passing your custom fields through its own object pipeline, check the actual assignment code, not just the field's presence in the dataclass — a field existing on a type doesn't mean every code path populates or forwards it.

### Groq free-tier daily token cap (TPD), separate from the per-minute cap — open, real constraint for step 15

- **Symptom:** After a day of build/debug testing, `Refund Abuse` custom vulnerability errored in the full pipeline run but succeeded when called in isolation moments later.
- **Root Cause:** `openai/gpt-oss-20b` on Groq's free tier has a **200,000 tokens/day** cap, separate from and in addition to the 8000 TPM per-minute cap. Cumulative usage from a day's worth of build-time testing (all the `run_asi`/`run_custom`/isolated debug-script calls) reached 198,802/200,000 — the last vulnerability in the pipeline simply ran into an near-exhausted daily budget, with a Groq-reported ~24-minute wait for enough headroom to trickle back (rolling window, not a fixed daily reset).
- **Fix:** **Not fixed, and not really fixable on the free tier** — this is a hard quota, not a bug. Stopped further live Groq calls for the rest of the day once found, rather than burning the last ~1,200 tokens against a 24-minute wait per retry.
- **Mitigation:** This is the strongest evidence yet that step 15's full-volume run ("hundreds of attempts across categories," per PROJECT_DESC.md Section 4.3) needs Groq's paid Developer tier planned in ahead of time — if build-time testing alone came within ~1% of the daily free cap, a real hundreds-of-attempts run won't fit inside it. Decide before step 15, not during it.

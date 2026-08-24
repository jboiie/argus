# Debug Journal

Real breakage, logged as it happens, with what fixed it. Feeds the video's "what broke" segment and the Failure Recovery judging axis.

## 2026-08-24 — Gemini 2.5 Flash-Lite retired for new users

**What broke:** `agent/reference_agent.py` step 6 build called `gemini-2.5-flash-lite` (the model PROJECT_DESC.md originally specified based on published pricing). API returned `404 NOT_FOUND`: "This model models/gemini-2.5-flash-lite is no longer available to new users."

**Why:** Google retired 2.5 Flash-Lite for new API keys ahead of its full retirement (Oct 16 2026); pricing pages hadn't caught up with the change.

**Fix:** Switched to `gemini-3.5-flash-lite`, confirmed working live. Pricing is different too ($0.30/$2.50 per M vs the $0.10/$0.40 quoted for 2.5) — corrected in PROJECT_DESC.md rather than left stale.

## 2026-08-24 — Razorpay MCP server auth: docs/README say Bearer, server requires Basic

**What broke:** `agent/razorpay_mcp.py` step 7 build. Razorpay's own docs page (`razorpay.com/docs/mcp-server/remote/`) and the `razorpay-mcp-server` GitHub README both describe the auth header as `Authorization: Bearer <base64(key:secret)>`. Following that literally, every connection attempt failed with `401 OAUTH_BAD_TOKEN: "Bad token; invalid JSON"` — a misleading error, since the token wasn't malformed JSON, it was just the wrong auth scheme.

**Why:** The `401` response's `WWW-Authenticate: Bearer resource_metadata=...` header made it look like a real OAuth 2.1 flow was required (dynamic client registration, authorization codes) — a much bigger problem than it actually was. Re-reading the GitHub README's Claude Desktop config snippet more carefully showed the actual header: `"Authorization: Basic <Merchant Token>"`. The docs page's prose just mislabeled the scheme.

**Fix:** Changed `Authorization: Bearer {token}` to `Authorization: Basic {token}` in `agent/razorpay_mcp.py`. Confirmed via a raw `httpx` POST to `https://mcp.razorpay.com/mcp` before touching the SDK-wrapped client — isolating the auth layer from the MCP SDK's own exception-group wrapping (which obscured the real error further, see below) made the actual cause visible in one request instead of guessing through several failed hypotheses (JSON-encoded token, trailing-newline-in-base64 per literal `echo | base64` semantics).

**Secondary annoyance:** the `mcp` Python SDK (v2.0.0) wraps every failure from nested `async with` blocks (`streamable_http_client` + `ClientSession`) in nested `ExceptionGroup`s, so a plain `except MCPError` never matches — needs `except*` or manual recursive unwrapping to see the real leaf exception. Worth remembering for any future MCP debugging in this repo: drop to a raw HTTP call first to see the actual server response before fighting the SDK's exception wrapping.

## 2026-08-24 — Stubbed tool result had no url field, model fabricated a fake-looking payment link

**What broke:** build steps 8-9, wiring `create_payment_link` into Gemini's function-calling with the mandate gate. When a mandate was authorized but `is_live_demo=False` (the default, no real Razorpay call made), the stub tool result was `{"stubbed": True, "mandate_id": ..., "would_call": ..., "args": ...}` — no `short_url` field. Gemini's final response to the user invented one anyway: `https://rzp.io/i/stubbed`, formatted exactly like a real Razorpay short link.

**Why:** the model had no field to point to for "the link," so it pattern-matched what a real Razorpay payment link URL looks like and produced one that reads as genuine but goes nowhere. Caught by inspecting the live demo output, not by any automated check — worth remembering as a live example for the drift-sentinel pitch itself: an LLM given an incomplete tool result will confidently fabricate the missing piece rather than flag the gap.

**Fix:** stub result now includes an explicit `short_url: "[TEST RUN - no real payment link was created]"` placeholder, so there's nothing plausible-looking left for the model to reach for. Re-ran the same two-turn conversation: agent now correctly tells the user it's a test run instead of presenting a fake link as real. General lesson for later stub/mock design in this repo: never leave a field blank that a model can plausibly fill in on its own — put an explicit, honest placeholder there instead.

## 2026-08-24 — Mandate gate accepted an external `user_confirmed` flag, defeating its own purpose

**What broke:** while prepping DeepTeam wiring (step 11), noticed `ask_with_tools(..., user_confirmed: bool)` let *any caller* — including the future red-team harness — just pass `True` and the mandate gate would rubber-stamp it. Nothing forced the confirmation to come from the actual conversation.

**Why:** built it that way in step 8/9 for a controllable smoke test, without registering that the same parameter would make ASI03 mandate-bypass testing meaningless — there'd be nothing for an attack to actually forge.

**Fix:** replaced the external flag with `_has_genuine_confirmation()` — a deterministic, code-level check over the real transcript (>=2 user turns, latest containing explicit affirmative language), computed internally, not supplied by the caller. Smoke test results held (its message content already satisfied the new check naturally).

## 2026-08-24 — DeepTeam judge model: three-stage saga to find a usable free-tier model

**What broke:** wiring DeepTeam's `OWASP_ASI_2026` framework (step 11) against Groq needed a judge/simulator model. Three failure modes in sequence, each masking the next:

1. `openai/gpt-oss-120b` (largest active Groq production model) flatly refused every attack-generation prompt: `"I'm sorry, but I can't help with that."` — even framed as legitimate, self-targeted security-testing. DeepTeam's own code then crashed trying to call `.data` on that plain string (`prompt_leakage.py:285`), because my `GroqModel.a_generate(self, prompt, *args, **kwargs)` silently swallowed DeepTeam's `schema=SyntheticDataList` probe kwarg instead of raising `TypeError` — DeepTeam relies on that `TypeError` to know a custom model needs its plain-text-JSON fallback path. Fixed the signature to be strict (`a_generate(self, prompt: str) -> str`, no `**kwargs`).
2. Switched to `qwen/qwen3.6-27b` (complies, doesn't refuse) but it's a reasoning model — wraps output in `<think>...</think>`, which broke every downstream JSON-parsing step. Fixed with `extra_body={"reasoning_format": "hidden"}` (Groq-specific param, not a recognized kwarg on the `openai` SDK's typed `create()` — has to go through `extra_body`). Then hit a second issue: the hidden reasoning trace still *consumes* completion tokens even though it's not shown, and with no `max_tokens` set, heavy reasoning (~2000 tokens on a trivial one-line request) sometimes ate the entire default budget, leaving nothing for the visible answer — empty `content`, no error, `finish_reason` truncated. Added an explicit `max_tokens=8192` ceiling. Then hit Groq's 8000 TPM free-tier cap on `qwen/qwen3.6-27b` — a *single* call could burn 2000-4000+ tokens, so even fully serialized requests (`max_concurrent=1`) couldn't stay under budget.
3. Switched to `openai/gpt-oss-20b` (smaller sibling of the model that refused everything) — ~4x cheaper per call (150-650 reasoning tokens vs Qwen's 2000+), fits the TPM budget, and complies on most prompt types (only refuses the narrow `SECRETS_AND_CREDENTIALS` framing). Small-scale wiring test against ASI_03 completed end-to-end this time: one test case fully scored (RBAC/`unauthorized_role_assumption`, correctly `defended`). But 9/10 test cases still errored — `BOLA` and `Agent Identity & Trust Abuse` categories failed at simulation entirely (empty everything), one `RBAC` case failed at judge-scoring (real response, unparseable judge JSON). Reliability gap not yet solved — **open problem, carried into step 12/15**, not silently accepted as "wiring done."

**Lesson for later Groq-model debugging in this repo:** always run `--no-capture-output` with `conda run` on this machine (plain `conda run` buffers stdout and crashes re-printing it through the wrong codepage on any non-ASCII/emoji output — a `conda run` bug, not our code). And check `response.usage.completion_tokens_details.reasoning_tokens` before trusting a "works" result from a reasoning-capable Groq model — silence and refusal look identical from the outside (both empty `content`) but have completely different causes and fixes.

**Resolved same day:** researched the 9/10-errored problem properly instead of accepting it. Root cause was DeepTeam calling `simulator_model.a_generate(prompt, schema=SomeSchema)` directly and falling back to fragile plain-text + `trimAndLoadJson` parsing whenever the custom model didn't genuinely support `schema` — a known failure mode (deepeval GitHub issues #929/#982). Fix: implemented real schema support in `GroqModel` using Groq's strict `json_schema` structured-output mode (`gpt-oss-20b`/`gpt-oss-120b` are the only two Groq models supporting `strict: true`, which constrains decoding to guarantee valid JSON — confirmed via Groq's own docs). Pydantic's default schema output needed a recursive normalizer (`_to_strict_schema`) to satisfy strict mode's `required`/`additionalProperties` rules first. Also added real retry-with-backoff reading Groq's actual suggested wait time (DeepTeam's built-in 1s/2s backoff was far shorter than Groq's real ~15-25s TPM cooldown).

Result, same ASI_03 category, same 10 test cases: errored dropped from 9/10 to 1/10, with 1 genuine bypass finding and 8 correctly defended. Side effect: structured/constrained decoding also reduced refusals (the model complied on `SECRETS_AND_CREDENTIALS` once forced into schema-shaped output, where it previously refused outright). Trade-off: reliability came at the cost of speed — 10 attempts took ~10 minutes under free-tier rate limits, so step 15's full-volume run needs explicit pacing (or Groq's paid Developer tier) planned in, not just assumed to work. Full detail in `BUGS.md`.

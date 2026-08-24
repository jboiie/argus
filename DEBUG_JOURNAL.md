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

"""Groq-backed judge/simulator model for DeepTeam - keeps attack generation
and scoring off Claude/Gemini and on the free tier.

Groq's API is OpenAI-compatible, so this wraps the openai SDK pointed at
Groq's base URL rather than adding a second HTTP client dependency.
"""

import asyncio
import os
import re
import time

from deepeval.models.base_model import DeepEvalBaseLLM
from dotenv import load_dotenv
from openai import AsyncOpenAI, BadRequestError, OpenAI, RateLimitError
from pydantic import BaseModel

load_dotenv()

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
# openai/gpt-oss-120b refuses to generate attack-simulation text outright,
# even in this legitimate self-targeted security-testing context (see
# DEBUG_JOURNAL.md). qwen/qwen3.6-27b complies but burns ~2-4k hidden
# reasoning tokens per call, blowing through Groq's 8000 TPM free-tier cap
# almost immediately even serialized. gpt-oss-20b is the practical middle
# ground: ~150-650 reasoning tokens per call (fits the TPM budget), only
# refuses one narrow sub-category, and is one of only two Groq models that
# support strict json_schema structured outputs (see _to_strict_schema
# below) - which is what actually fixes the "invalid JSON" failures rather
# than just working around them.
DEFAULT_MODEL = "openai/gpt-oss-20b"

# Simulation (writing attack prompts) and evaluation (judging the agent's
# reply) are split because they fail differently. gpt-oss-20b judges fine
# but REFUSES to write attacks for whole categories - the x3 full run had
# 57/204 cases error with `failed_generation: "I'm sorry, but I can't help
# with that."`, and all 18 commerce-vulnerability attacks (Price Integrity,
# Refund Abuse, Mandate Bypass) were among them. Those are the project's
# differentiator, so silently losing them to a simulator's alignment is not
# an acceptable default.
#
# qwen3.8-27b writes them and honors strict json_schema (verified directly
# against all four available Groq text models). The reasoning-token blowup
# that got the older qwen3.6 abandoned during step 11 is already handled
# here by reasoning_format=hidden + an explicit max_tokens.
DEFAULT_SIMULATOR_MODEL = os.environ.get("GROQ_SIMULATOR_MODEL", "qwen/qwen3.8-27b")

MAX_COMPLETION_TOKENS = 4096

# All Groq calls share one 8000 TPM budget on this key/model regardless of
# how many DeepTeam tasks run concurrently (max_concurrent). Without this,
# concurrent callers each independently hit 429, each independently retry,
# and pile back onto the same still-recovering budget - a thundering herd
# that can exceed any single call's retry budget even though each call in
# isolation succeeds fine (confirmed: a_simulate_attacks() alone works).
# One process-wide semaphore serializes actual Groq requests, decoupling
# DeepTeam's task parallelism from real API concurrency.
_REQUEST_LOCK = asyncio.Semaphore(1)


def _to_strict_schema(model: type[BaseModel]) -> dict:
    """Pydantic's default model_json_schema() doesn't satisfy Groq's strict
    json_schema requirements (every property in `required`, `additionalProperties:
    false` on every object) - Optional fields land outside `required` and
    `additionalProperties` is left unset. Normalize recursively.
    """
    schema = model.model_json_schema()

    def normalize(node: dict) -> None:
        if node.get("type") == "object" or "properties" in node:
            props = node.get("properties", {})
            node["required"] = list(props.keys())
            node["additionalProperties"] = False
            for prop in props.values():
                normalize(prop)
        if "items" in node:
            normalize(node["items"])
        for variant in node.get("anyOf", []):
            normalize(variant)
        for definition in node.get("$defs", {}).values():
            normalize(definition)

    normalize(schema)
    return schema


_RETRY_AFTER_RE = re.compile(r"try again in ([\d.]+)s", re.IGNORECASE)
MAX_RETRIES = 2


def _is_empty_generation(exc: BadRequestError) -> bool:
    """True for the transient case: Groq's strict-schema mode occasionally
    returns 400 json_validate_failed with a genuinely EMPTY completion
    (confirmed by replaying the identical prompt raw - it succeeded fine,
    same reasoning-token cost, well under the token budget - so this isn't
    a schema/budget problem, it's a one-off flake worth retrying).

    Deliberately narrower than "any json_validate_failed": a REAL refusal
    also fails schema validation but leaves the refusal text in
    failed_generation (see BUGS.md's DeepTeam judge-model saga) - that's a
    genuine finding, not a glitch, and must surface as errored, not be
    retried away.
    """
    body = exc.body if isinstance(exc.body, dict) else {}
    return body.get("code") == "json_validate_failed" and not (body.get("failed_generation") or "").strip()


def _retry_after_seconds(exc: RateLimitError, default: float = 30.0) -> float:
    # DeepTeam's own built-in backoff (1s, 2s) is far shorter than Groq's
    # real TPM cooldown (seen up to ~25s) - read the actual wait time Groq
    # tells us instead of guessing.
    header = exc.response.headers.get("retry-after") if exc.response is not None else None
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    match = _RETRY_AFTER_RE.search(str(exc))
    if match:
        return float(match.group(1))
    return default


class GroqModel(DeepEvalBaseLLM):
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model_name = model
        api_key = os.environ["GROQ_API_KEY"]
        self._client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
        self._aclient = AsyncOpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
        super().__init__(model)

    def load_model(self):
        return self

    def _kwargs(self, schema: type[BaseModel] | None) -> dict:
        kwargs = {
            "model": self.model_name,
            "max_tokens": MAX_COMPLETION_TOKENS,
            "extra_body": {"reasoning_format": "hidden"},
        }
        if schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "strict": True,
                    "schema": _to_strict_schema(schema),
                },
            }
        return kwargs

    # schema is a real accepted parameter (not swallowed via **kwargs) so
    # DeepTeam's `a_generate(prompt, schema=SomeModel)` call sites get a
    # validated pydantic object back directly, skipping their fragile
    # plain-text + trimAndLoadJson fallback path entirely.
    def generate(self, prompt: str, schema: type[BaseModel] | None = None):
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self._client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    **self._kwargs(schema),
                )
                break
            except RateLimitError as exc:
                if attempt == MAX_RETRIES:
                    raise
                time.sleep(_retry_after_seconds(exc) + 1)
            except BadRequestError as exc:
                if attempt == MAX_RETRIES or not _is_empty_generation(exc):
                    raise
        content = response.choices[0].message.content or ""
        return schema.model_validate_json(content) if schema else content

    async def a_generate(self, prompt: str, schema: type[BaseModel] | None = None):
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with _REQUEST_LOCK:
                    response = await self._aclient.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        **self._kwargs(schema),
                    )
                break
            except RateLimitError as exc:
                if attempt == MAX_RETRIES:
                    raise
                await asyncio.sleep(_retry_after_seconds(exc) + 1)
            except BadRequestError as exc:
                if attempt == MAX_RETRIES or not _is_empty_generation(exc):
                    raise
        content = response.choices[0].message.content or ""
        return schema.model_validate_json(content) if schema else content

    def get_model_name(self) -> str:
        return f"groq/{self.model_name}"

    def supports_structured_outputs(self) -> bool:
        return True


def demo():
    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY not set - skipping live call.")
        return
    model = GroqModel()
    answer = model.generate("Reply with exactly one word: 'ok'.")
    assert answer, "expected a non-empty response"
    print(f"Groq judge model ({model.get_model_name()}) responded:", answer)


if __name__ == "__main__":
    demo()

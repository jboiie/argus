"""Groq-backed judge/simulator model for DeepTeam - keeps attack generation
and scoring off Claude/Gemini and on the free tier.

Groq's API is OpenAI-compatible, so this wraps the openai SDK pointed at
Groq's base URL rather than adding a second HTTP client dependency.
"""

import os

from deepeval.models.base_model import DeepEvalBaseLLM
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

load_dotenv()

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
# openai/gpt-oss-120b refuses to generate attack-simulation text outright,
# even in this legitimate self-targeted security-testing context (see
# DEBUG_JOURNAL.md). qwen/qwen3.6-27b complies but burns ~2-4k hidden
# reasoning tokens per call, blowing through Groq's 8000 TPM free-tier cap
# almost immediately even serialized. gpt-oss-20b is the practical middle
# ground: ~150-650 reasoning tokens per call (fits the TPM budget), and
# only refuses one narrow sub-category (credential-extraction framing) -
# that becomes a single "errored" test case via ignore_errors=True, not a
# crashed run.
DEFAULT_MODEL = "openai/gpt-oss-20b"
MAX_COMPLETION_TOKENS = 4096


class GroqModel(DeepEvalBaseLLM):
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model_name = model
        api_key = os.environ["GROQ_API_KEY"]
        self._client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
        self._aclient = AsyncOpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
        super().__init__(model)

    def load_model(self):
        return self

    def generate(self, prompt: str) -> str:
        # No *args/**kwargs on purpose: DeepTeam probes for schema-generation
        # support by calling generate(prompt, schema=...) and catching the
        # resulting TypeError to fall back to its own plain-text + JSON-parse
        # path. Accepting **kwargs here would silently swallow that probe.
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_COMPLETION_TOKENS,
            extra_body={"reasoning_format": "hidden"},
        )
        return response.choices[0].message.content or ""

    async def a_generate(self, prompt: str) -> str:
        response = await self._aclient.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_COMPLETION_TOKENS,
            extra_body={"reasoning_format": "hidden"},
        )
        return response.choices[0].message.content or ""

    def get_model_name(self) -> str:
        return f"groq/{self.model_name}"


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

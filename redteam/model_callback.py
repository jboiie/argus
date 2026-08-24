"""Bridges DeepTeam's model_callback contract to the reference agent.

DeepTeam tracks its own simulated conversation via the `turns` argument;
our agent keeps its own per-session history in agent.reference_agent's
module-level store, keyed by session_id. Each attack gets a fresh session,
seeded by replaying DeepTeam's prior turns first - so the mandate gate
(agent/reference_agent.py::_has_genuine_confirmation) sees the exact same
conversation DeepTeam thinks it's having, including anything a multi-turn
attack tried to engineer as a fake confirmation.
"""

import uuid

from deepteam.test_case.test_case import RTTurn
from google.genai import types

from agent.reference_agent import _SESSION_HISTORY, ask_with_tools

RUN_ID = "run_redteam_dev"


def _seed_session(session_id: str, turns: list[RTTurn] | None) -> None:
    if not turns:
        return
    history = _SESSION_HISTORY.setdefault(session_id, [])
    for turn in turns:
        role = "user" if turn.role == "user" else "model"
        history.append(types.Content(role=role, parts=[types.Part(text=turn.content)]))


async def model_callback(input: str, turns: list[RTTurn] | None = None) -> RTTurn:
    session_id = str(uuid.uuid4())
    _seed_session(session_id, turns)
    response_text = await ask_with_tools(session_id, RUN_ID, input)
    return RTTurn(role="assistant", content=response_text)


async def demo():
    import os

    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set - skipping live call.")
        return
    turn = await model_callback("What is the refund window?")
    assert turn.role == "assistant"
    assert turn.content
    print("model_callback response:", turn.content)


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo())

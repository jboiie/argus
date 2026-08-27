"""Bridges DeepTeam's model_callback contract to the reference agent.

DeepTeam tracks its own simulated conversation via the `turns` argument;
our agent keeps its own per-session history in agent.reference_agent's
module-level store, keyed by session_id. Each attack gets a fresh session,
seeded by replaying DeepTeam's prior turns first - so the mandate gate
(agent/reference_agent.py::_has_genuine_confirmation) sees the exact same
conversation DeepTeam thinks it's having, including anything a multi-turn
attack tried to engineer as a fake confirmation.

session_id is derived deterministically from the attack's prompt text
(uuid5, not uuid4) rather than tracked through DeepTeam's pipeline -
RTTurn.metadata does NOT propagate to the resulting RTTestCase (checked
against deepteam's own _a_attack source, not assumed), so there's no
built-in way to carry a randomly-generated session_id from model_callback
through to the test case DataModel.md logging needs it on. Deterministic
derivation means telemetry/supabase_client.py can recompute the same ID
from tc.input with zero shared state.
"""

import os
import uuid

from deepteam.test_case.test_case import RTTurn
from google.genai import types

from agent.reference_agent import _SESSION_HISTORY, ask_with_tools

_SESSION_NAMESPACE = uuid.UUID("6f9c7c5a-3b1a-4e9e-9c2a-8f1a5d6b2c11")

# session_turns was schema-ready since step 14 but nothing in the red-team
# harness ever wrote to it (BUGS.md, 2026-08-26 entry) - only the drift
# sentinel's sampler did. Logs the triggering exchange only (not DeepTeam's
# replayed seed turns, which are synthetic prompts, not real agent output) -
# enough for the dashboard's per-attack conversation drill-down to show what
# the agent actually said, which is the part an audit trail needs most.
_TURN_COUNTERS: dict[str, int] = {}


def _log_turn_safe(session_id: str, run_id: str, role: str, content: str) -> None:
    if not (os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY")):
        return
    idx = _TURN_COUNTERS.get(session_id, 0)
    _TURN_COUNTERS[session_id] = idx + 1
    try:
        from telemetry.supabase_client import get_client, log_session_turn
        log_session_turn(get_client(), session_id, run_id, "attack", idx, role, content)
    except Exception:
        pass


def session_id_for(prompt: str) -> str:
    return str(uuid.uuid5(_SESSION_NAMESPACE, prompt))


def _seed_session(session_id: str, turns: list[RTTurn] | None) -> None:
    if not turns:
        return
    history = _SESSION_HISTORY.setdefault(session_id, [])
    for turn in turns:
        role = "user" if turn.role == "user" else "model"
        history.append(types.Content(role=role, parts=[types.Part(text=turn.content)]))


def make_model_callback(run_id: str):
    """Bind run_id via closure - keeps model_callback's exact (input, turns=None)
    signature, which DeepTeam inspects via inspect.signature() to decide whether
    to pass turns at all (see red_teamer.py::_a_attack).
    """

    async def model_callback(input: str, turns: list[RTTurn] | None = None) -> RTTurn:
        session_id = session_id_for(input)
        _seed_session(session_id, turns)
        response_text = await ask_with_tools(session_id, run_id, input)
        _log_turn_safe(session_id, run_id, "user", input)
        _log_turn_safe(session_id, run_id, "agent", response_text)
        return RTTurn(role="assistant", content=response_text)

    return model_callback


async def demo():
    import os

    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set - skipping live call.")
        return
    callback = make_model_callback(run_id="run_dev_demo")
    turn = await callback("What is the refund window?")
    assert turn.role == "assistant"
    assert turn.content
    assert session_id_for("What is the refund window?") == session_id_for("What is the refund window?")
    print("model_callback response:", turn.content)


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo())

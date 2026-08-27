"""Streamlit dashboard - build steps 21-24.

Three tabs: pre-deployment report (ASR by category), live drift feed
(incidents over time), and mandate audit trail (Section 4.2's
authorization layer) - each with an audit-trail detail view per row
(Section 4.5's "must show full audit trail per incident"). Read-only -
anon key only, never service_role (see DataModel.md's Security
convention - this is the one place that rule actually matters, since
it's the code path that ships to a public URL).

Run with: streamlit run dashboard/app.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Streamlit puts the entry file's own directory (dashboard/) on sys.path,
# not the repo root - so the repo-root-qualified imports below (this file
# importing its own parent package, plus drift.audit) can't resolve
# without this, even though it happens to work locally depending on how
# `streamlit run` is invoked. Explicit and portable beats relying on that.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard.data import (
    compute_asr_by_category,
    drift_cause_breakdown,
    drift_incidents_over_time,
    fetch_attack_events,
    fetch_drift_incidents,
    fetch_mandates,
    fetch_session_turns,
    get_client,
)
from drift.audit import compute_false_positive_cost

load_dotenv()

st.set_page_config(page_title="Argus Dashboard", page_icon="\U0001F441", layout="wide")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


@st.cache_resource
def _client():
    return get_client(SUPABASE_URL, SUPABASE_ANON_KEY)


@st.cache_data(ttl=30)
def _load_attack_events():
    try:
        return fetch_attack_events(_client())
    except Exception as exc:
        st.error(f"Couldn't reach Supabase for attack_events: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=30)
def _load_drift_incidents():
    try:
        return fetch_drift_incidents(_client())
    except Exception as exc:
        st.error(f"Couldn't reach Supabase for drift_incidents: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=30)
def _load_mandates():
    try:
        return fetch_mandates(_client())
    except Exception as exc:
        st.error(f"Couldn't reach Supabase for mandates: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=30)
def _load_session_turns(session_id: str):
    try:
        return fetch_session_turns(_client(), session_id)
    except Exception as exc:
        st.error(f"Couldn't reach Supabase for session_turns: {exc}")
        return pd.DataFrame()


def _render_conversation(session_id: str) -> None:
    turns = _load_session_turns(session_id)
    if turns.empty:
        st.caption("No session_turns logged for this session.")
        return
    st.write("**Conversation:**")
    for _, t in turns.sort_values("turn_index").iterrows():
        st.write(f"- `{t['role']}`: {t['content']}")


def _render_attack_report() -> None:
    events = _load_attack_events()
    if events.empty:
        st.info("No attack events logged yet - run redteam/run_full.py.")
        return

    asr = compute_asr_by_category(events)
    total_scored = int(asr["bypassed"].sum() + asr["defended"].sum())
    overall_asr = (int(asr["bypassed"].sum()) / total_scored * 100) if total_scored else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total attempts", int(asr["attempts"].sum()))
    col2.metric("Bypassed", int(asr["bypassed"].sum()))
    col3.metric("Overall ASR", f"{overall_asr:.1f}%")

    st.subheader("ASR by category")
    st.dataframe(asr, use_container_width=True)

    st.subheader("Audit trail - inspect an attack event")
    selected = st.selectbox("attack_id", events["attack_id"].tolist())
    if selected:
        row = events[events["attack_id"] == selected].iloc[0]
        st.write(f"**Vulnerability:** {row['vulnerability']} / {row['vulnerability_type']} ({row['asi_category'] or 'no ASI mapping'})")
        st.write(f"**Outcome:** {row['outcome']}")
        st.write(f"**Prompt:** {row['prompt']}")
        st.write(f"**Response:** {row['response']}")
        st.write(f"**Reason:** {row['reason']}")
        _render_conversation(row["session_id"])


def _render_drift_feed() -> None:
    incidents = _load_drift_incidents()
    if incidents.empty:
        st.info("No drift incidents logged yet - run drift/sampler.py.")
        return

    flagged_count = int(incidents["flagged"].sum())
    col1, col2, col3 = st.columns(3)
    col1.metric("Total checks", len(incidents))
    col2.metric("Flagged", flagged_count)
    col3.metric("Flag rate", f"{flagged_count / len(incidents) * 100:.1f}%")

    st.subheader("Incidents over time")
    st.line_chart(drift_incidents_over_time(incidents))

    breakdown = drift_cause_breakdown(incidents)
    if not breakdown.empty:
        st.subheader("Drift cause breakdown (flagged only)")
        st.bar_chart(breakdown)

    st.subheader("False-positive cost")
    cost = compute_false_positive_cost(incidents.to_dict("records"))
    st.json(cost)

    st.subheader("Audit trail - inspect an incident")
    flagged_ids = incidents[incidents["flagged"] == True]["incident_id"].tolist()  # noqa: E712
    if not flagged_ids:
        st.caption("No flagged incidents to inspect yet.")
        return
    selected = st.selectbox("incident_id", flagged_ids)
    if selected:
        row = incidents[incidents["incident_id"] == selected].iloc[0]
        st.write(f"**Question:** {row['question']}")
        st.write(f"**Expected:** {row['expected']}")
        st.write(f"**Actual:** {row['actual']}")
        st.write(f"**Cause:** {row.get('drift_cause')}  **Severity:** {row.get('severity')}")
        review = "confirmed" if row.get("is_false_positive") is False else ("false positive" if row.get("is_false_positive") else "unreviewed")
        st.write(f"**Review status:** {review}")
        _render_conversation(row["session_id"])


def _render_mandates() -> None:
    mandates = _load_mandates()
    if mandates.empty:
        st.info("No mandates logged yet - a checkout has to run against the tools-enabled agent (agent/reference_agent.py::ask_with_tools).")
        return

    authorized = int((mandates["status"] == "authorized").sum())
    denied = int((mandates["status"] == "denied").sum())
    live_calls = int(mandates["real_call_fired"].sum())
    col1, col2, col3 = st.columns(3)
    col1.metric("Authorized", authorized)
    col2.metric("Denied", denied)
    col3.metric("Real Razorpay calls fired", live_calls)

    st.caption("Every mandate creation attempt gets logged here, authorized or denied, live or stubbed - Track 01's \"every money action explainable, bounded and gated\" bar (DataModel.md Entity 3).")
    display_cols = ["mandate_id", "authorized_at", "status", "scope", "amount", "coupon_code", "user_confirmed", "is_live_demo", "real_call_fired", "session_id"]
    st.dataframe(mandates[display_cols], use_container_width=True)

    st.subheader("Audit trail - inspect a mandate")
    selected = st.selectbox("mandate_id", mandates["mandate_id"].tolist())
    if selected:
        row = mandates[mandates["mandate_id"] == selected].iloc[0]
        st.write(f"**Status:** {row['status']}  **Amount:** Rs.{row['amount'] / 100:.2f}")
        st.write(f"**Line items:** {row['line_items']}")
        st.write(f"**Coupon:** {row['coupon_code'] or '(none)'}")
        st.write(f"**User confirmed:** {row['user_confirmed']}  **Bypass confirmed at:** {row['bypass_confirmed_at'] or '(never - not bypassed)'}")
        _render_conversation(row["session_id"])


def main():
    st.title("\U0001F441 Argus — Agent QA & Monitoring")
    st.caption("Pre-deployment red-team results and post-deployment drift feed for the reference commerce agent.")

    if not (SUPABASE_URL and SUPABASE_ANON_KEY):
        st.warning("SUPABASE_URL / SUPABASE_ANON_KEY not configured.")
        return

    tab1, tab2, tab3 = st.tabs(["Pre-Deployment Report", "Drift Feed", "Mandates"])
    with tab1:
        _render_attack_report()
    with tab2:
        _render_drift_feed()
    with tab3:
        _render_mandates()


if __name__ == "__main__":
    main()

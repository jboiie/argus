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
    fetch_runs,
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
def _load_runs(run_type: str | None = None):
    try:
        return fetch_runs(_client(), run_type)
    except Exception as exc:
        st.error(f"Couldn't reach Supabase for runs: {exc}")
        return pd.DataFrame()


def _run_selector(run_type: str, key: str) -> str | None:
    """Returns the selected run_id, or None for cumulative. Runs differ in
    simulator model and in how much API quota was left when they ran, so a
    blended view across all of them isn't a meaningful number."""
    runs = _load_runs(run_type)
    if runs.empty:
        return None
    labels = {"All runs (cumulative)": None}
    for _, r in runs.iterrows():
        labels[f"{r['started_at'][:16].replace('T', ' ')} — {r['label']}"] = r["run_id"]
    choice = st.selectbox("Run", list(labels), key=key)
    return labels[choice]


@st.cache_data(ttl=30)
def _load_session_turns(session_id: str):
    try:
        return fetch_session_turns(_client(), session_id)
    except Exception as exc:
        st.error(f"Couldn't reach Supabase for session_turns: {exc}")
        return pd.DataFrame()


OUTCOME_COLORS = {"bypassed": "red", "defended": "green", "errored": "orange"}
SEVERITY_COLORS = {"critical": "red", "moderate": "orange"}


def _untrusted(label: str, value) -> None:
    """Render attacker-influenced text WITHOUT markdown interpretation.

    Attack prompts, agent responses, judge reasons and session turns are all
    written by an adversarial generator or by a model responding to one, and
    a prompt-injection payload is routinely shaped to look like markup or
    instructions (DataModel.md's no-unsafe-HTML rule names exactly these
    fields). st.write would interpret them as markdown and let that payload
    style the page it appears on. st.code renders them verbatim - and is
    easier to read and copy for an audit view besides.
    """
    st.caption(label)
    text = "" if value is None else str(value)
    st.code(text if text.strip() else "(empty)", language=None, wrap_lines=True)


def _outcome_badge(outcome: str) -> None:
    st.badge(outcome, color=OUTCOME_COLORS.get(outcome, "gray"))


def _render_conversation(session_id: str) -> None:
    turns = _load_session_turns(session_id)
    if turns.empty:
        st.caption("No conversation turns logged for this session.")
        return
    st.markdown("**Conversation transcript**")
    for _, t in turns.sort_values("turn_index").iterrows():
        # Role is a DB enum (safe); content is untrusted free text.
        _untrusted(f"turn {t['turn_index']} · {t['role']}", t["content"])


def _render_attack_report() -> None:
    events = _load_attack_events()
    if events.empty:
        st.info("No attack events logged yet - run redteam/run_full.py.")
        return

    selected_run = _run_selector("redteam", key="attack_run")
    if selected_run:
        events = events[events["run_id"] == selected_run]
        if events.empty:
            st.info("No attack events logged for that run.")
            return

    asr = compute_asr_by_category(events)
    bypassed = int(asr["bypassed"].sum())
    errored = int(asr["errored"].sum())
    total_scored = int(bypassed + asr["defended"].sum())
    overall_asr = (bypassed / total_scored * 100) if total_scored else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Attempts", int(asr["attempts"].sum()), border=True)
    col2.metric("Scored", total_scored, help="Errored attempts are excluded from the ASR denominator - they never got a real answer.", border=True)
    col3.metric("Bypassed", bypassed, border=True)
    col4.metric("Attack Success Rate", f"{overall_asr:.2f}%", border=True)

    if errored:
        st.caption(f"{errored} attempt(s) errored and are excluded from the rate above - most are attack-generation refusals, where the simulator model declined to write the prompt at all.")
    if bypassed:
        st.warning(
            "Every bypass shown here is worth reading before it is believed. DeepTeam's framework "
            "criteria carry no knowledge of this agent's scope, so a correct refusal can score as a "
            "failure - the logged examples include the agent declining an off-topic question and being "
            "marked down for it. The commerce vulnerabilities do not have this problem: their criteria "
            "are written against this repo's own catalog, policies and mandate rules. See BUGS.md.",
            icon=":material/rule:",
        )

    st.subheader("Attack Success Rate by category")
    st.caption("One row per vulnerability type, each labelled with its OWASP ASI code.")
    st.dataframe(
        asr, width="stretch", hide_index=True,
        column_config={
            "asi_category": st.column_config.TextColumn("ASI"),
            "asi_display_name": st.column_config.TextColumn("Category"),
            "vulnerability": st.column_config.TextColumn("Vulnerability"),
            "vulnerability_type": st.column_config.TextColumn("Type"),
            "attempts": st.column_config.NumberColumn("Attempts", width="small"),
            "bypassed": st.column_config.NumberColumn("Bypassed", width="small"),
            "defended": st.column_config.NumberColumn("Defended", width="small"),
            "errored": st.column_config.NumberColumn("Errored", width="small"),
            "asr_pct": st.column_config.ProgressColumn("ASR", format="%.1f%%", min_value=0, max_value=100),
        },
    )

    st.subheader("Audit trail")
    st.caption("Full prompt, response and judge reasoning behind any single attempt.")
    # Label by what the row IS. A raw attack_id dropdown is unusable at this
    # volume - nobody can pick a meaningful UUID out of ~200.
    events = events.copy()
    events["_label"] = (
        events["outcome"].str.upper() + " · " + events["vulnerability"].fillna("?")
        + " / " + events["vulnerability_type"].fillna("?")
        + " · " + events["prompt"].fillna("").str.slice(0, 60).str.replace(r"\s+", " ", regex=True)
    )
    # Surface bypasses first - they are the rows anyone actually came to read.
    order = {"bypassed": 0, "errored": 1, "defended": 2}
    events = events.assign(_rank=events["outcome"].map(order).fillna(3)).sort_values(["_rank", "_label"])
    choice = st.selectbox("Attempt", events["_label"].tolist(), key="attack_pick")
    if choice:
        row = events[events["_label"] == choice].iloc[0]
        with st.container(border=True):
            head, badge = st.columns([5, 1])
            head.markdown(f"**{row['vulnerability']} / {row['vulnerability_type']}**")
            head.caption(f"{row['asi_category'] or 'no ASI mapping'} · attack method: {row['attack_method'] or 'n/a'}")
            with badge:
                _outcome_badge(row["outcome"])
            _untrusted("Attack prompt", row["prompt"])
            _untrusted("Agent response", row["response"])
            _untrusted("Judge reasoning", row["reason"])
            _render_conversation(row["session_id"])


def _render_drift_feed() -> None:
    incidents = _load_drift_incidents()
    if incidents.empty:
        st.info("No drift incidents logged yet - run drift/sampler.py.")
        return

    selected_run = _run_selector("drift_sample", key="drift_run")
    if selected_run:
        incidents = incidents[incidents["run_id"] == selected_run]
        if incidents.empty:
            st.info("No drift incidents logged for that run.")
            return

    flagged_count = int(incidents["flagged"].sum())
    errored_count = int((incidents["check_status"] == "errored").sum())
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Checks run", len(incidents), border=True)
    col2.metric("Flagged", flagged_count, border=True)
    col3.metric("Flag rate", f"{flagged_count / len(incidents) * 100:.1f}%", border=True)
    col4.metric("Errored", errored_count, help="A check that never completed - flagged is null, not false.", border=True)

    st.subheader("Incidents over time")
    st.caption("Total checks vs. flagged, per day. Meant to be read across build days, not within one batch.")
    st.line_chart(drift_incidents_over_time(incidents))

    breakdown = drift_cause_breakdown(incidents)
    if not breakdown.empty:
        st.subheader("Drift cause")
        st.caption("Flagged incidents only. Classified rule-based, not by an LLM: stale_ground_truth is a git-history lookup against the ground-truth file's real past values, fabrication is a value that never existed.")
        st.bar_chart(breakdown)

    st.subheader("False-positive cost")
    cost = compute_false_positive_cost(incidents.to_dict("records"))
    fp_rate = cost["false_positive_rate"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Flagged", cost["total_flagged"], border=True)
    c2.metric("Reviewed", cost["reviewed"], border=True)
    c3.metric("Confirmed drift", cost["true_positives"], border=True)
    c4.metric("False-positive rate", f"{fp_rate * 100:.0f}%" if fp_rate is not None else "n/a",
              help="Of reviewed incidents, how many turned out to be false alarms.", border=True)
    if cost["pending_review"]:
        st.caption(f"{cost['pending_review']} flagged incident(s) still awaiting review, so the rate above is computed over the reviewed subset only.")
    st.caption(
        "Review cost is modelled at 1 unit per flagged incident. The assumption that a missed drift "
        "costs several times more is stated explicitly and is NOT measured - there is no ground truth "
        "on what should have been flagged but wasn't. It is the stated reason both thresholds lean "
        "toward over-flagging. See README."
    )

    st.subheader("Audit trail")
    flagged = incidents[incidents["flagged"] == True].copy()  # noqa: E712
    if flagged.empty:
        st.caption("No flagged incidents to inspect in this run.")
        return
    flagged["_label"] = (
        flagged["check_type"] + " · " + flagged["ground_truth_ref"].fillna("(uncovered)")
        + " · " + flagged["question"].fillna("").str.slice(0, 60)
    )
    choice = st.selectbox("Flagged incident", flagged["_label"].tolist(), key="drift_pick")
    if choice:
        row = flagged[flagged["_label"] == choice].iloc[0]
        with st.container(border=True):
            left, right = st.columns([5, 1])
            left.markdown(f"**{row['check_type']}** · `{row['ground_truth_ref'] or 'no ground-truth ref'}`")
            severity = row.get("severity")
            if severity:
                with right:
                    st.badge(severity, color=SEVERITY_COLORS.get(severity, "gray"))
            meta = [f"cause: {row.get('drift_cause') or 'unclassified'}"]
            if row.get("score") is not None:
                meta.append(f"score: {row['score']:.2f}")
            review = "confirmed drift" if row.get("is_false_positive") is False else (
                "false positive" if row.get("is_false_positive") else "unreviewed")
            meta.append(f"review: {review}")
            left.caption(" · ".join(meta))

            _untrusted("Question", row["question"])
            exp, act = st.columns(2)
            with exp:
                _untrusted("Expected (ground truth at check time)", row["expected"])
            with act:
                _untrusted("Actual (agent answer)", row["actual"])
            _render_conversation(row["session_id"])


def _render_mandates() -> None:
    mandates = _load_mandates()
    if mandates.empty:
        st.info("No mandates logged yet - a checkout has to run against the tools-enabled agent (agent/reference_agent.py::ask_with_tools).")
        return

    authorized = int((mandates["status"] == "authorized").sum())
    denied = int((mandates["status"] == "denied").sum())
    live_calls = int(mandates["real_call_fired"].sum())
    bypassed = int(mandates["bypass_confirmed_at"].notna().sum())
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Authorized", authorized, border=True)
    col2.metric("Denied", denied, border=True)
    col3.metric("Real Razorpay calls", live_calls, help="Test-mode payment links are capped at 30 per business, so bulk runs are stubbed and only genuine demos fire.", border=True)
    col4.metric("Later found bypassable", bypassed, help="An attack got past this mandate's check. Recorded separately from status, which is immutable.", border=True)

    st.caption(
        "Every mandate creation attempt is logged, authorized or denied, live or stubbed - Track 01's "
        "\"every money action explainable, bounded and gated\" bar. The amount is computed server-side "
        "from the cart against real catalog prices; the model never states a number that reaches Razorpay."
    )
    if bypassed:
        st.error(f"{bypassed} mandate(s) were later confirmed bypassable by an attack. `status` is deliberately left untouched - the original decision stays an immutable record.", icon=":material/gpp_bad:")

    st.dataframe(
        mandates, width="stretch", hide_index=True,
        column_order=["authorized_at", "status", "scope", "amount", "coupon_code", "user_confirmed", "is_live_demo", "real_call_fired", "bypass_confirmed_at"],
        column_config={
            "authorized_at": st.column_config.DatetimeColumn("Authorized at", format="YYYY-MM-DD HH:mm"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "scope": st.column_config.TextColumn("Scope", width="small"),
            "amount": st.column_config.NumberColumn("Amount", help="Stored in paise - Razorpay's native unit", format="%d p"),
            "coupon_code": st.column_config.TextColumn("Coupon"),
            "user_confirmed": st.column_config.CheckboxColumn("Confirmed"),
            "is_live_demo": st.column_config.CheckboxColumn("Live intent"),
            "real_call_fired": st.column_config.CheckboxColumn("Call fired"),
            "bypass_confirmed_at": st.column_config.DatetimeColumn("Bypassed at", format="YYYY-MM-DD HH:mm"),
        },
    )

    st.subheader("Audit trail")
    mandates = mandates.copy()
    mandates["_label"] = (
        mandates["status"].str.upper() + " · Rs." + (mandates["amount"] / 100).round(2).astype(str)
        + " · " + mandates["authorized_at"].str.slice(0, 16).str.replace("T", " ")
    )
    choice = st.selectbox("Mandate", mandates["_label"].tolist(), key="mandate_pick")
    if choice:
        row = mandates[mandates["_label"] == choice].iloc[0]
        with st.container(border=True):
            left, right = st.columns([5, 1])
            left.markdown(f"**Rs.{row['amount'] / 100:.2f}** · scope: {row['scope']}")
            left.caption(f"authorized_at {row['authorized_at'][:19].replace('T', ' ')} · expires {str(row['expires_at'])[:19].replace('T', ' ')}")
            with right:
                st.badge(row["status"], color="green" if row["status"] == "authorized" else "orange")
            st.caption("Line items (server-computed from the cart, not model-supplied)")
            st.json(row["line_items"] if row["line_items"] else [], expanded=False)
            st.caption(
                f"Coupon: {row['coupon_code'] or '(none)'} · "
                f"user_confirmed: {row['user_confirmed']} · "
                f"bypass_confirmed_at: {row['bypass_confirmed_at'] or '(never - not bypassed)'}"
            )
            _render_conversation(row["session_id"])


def main():
    st.title("\U0001F441 Argus")
    st.markdown("##### Agent QA & Monitoring for Agentic Commerce")
    st.caption(
        "A pre-deployment red-team harness and a post-deployment drift sentinel, both run against one "
        "reference commerce agent. Read-only view over the full audit trail: every attack attempt, every "
        "ground-truth check, and every money-moving authorization."
    )

    if not (SUPABASE_URL and SUPABASE_ANON_KEY):
        st.warning("SUPABASE_URL / SUPABASE_ANON_KEY not configured.", icon=":material/key_off:")
        return

    tab1, tab2, tab3 = st.tabs(["Pre-Deployment · Red Team", "Post-Deployment · Drift", "Mandates"])
    with tab1:
        _render_attack_report()
    with tab2:
        _render_drift_feed()
    with tab3:
        _render_mandates()


if __name__ == "__main__":
    main()

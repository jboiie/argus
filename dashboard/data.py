"""Dashboard data layer - Supabase queries + pandas aggregation, split
from app.py so the aggregation math is unit-testable without a live
Supabase connection or Streamlit runtime. Only get_client/fetch_* touch
the network - build steps 21-24.
"""

import pandas as pd
from supabase import Client, create_client

from redteam.scoring import ASI_DISPLAY_NAMES


def get_client(url: str, key: str) -> Client:
    return create_client(url, key)


def fetch_attack_events(client: Client, limit: int = 1000) -> pd.DataFrame:
    resp = client.table("attack_events").select("*").order("timestamp", desc=True).limit(limit).execute()
    return pd.DataFrame(resp.data)


def fetch_drift_incidents(client: Client, limit: int = 1000) -> pd.DataFrame:
    resp = client.table("drift_incidents").select("*").order("timestamp", desc=True).limit(limit).execute()
    return pd.DataFrame(resp.data)


def fetch_session_turns(client: Client, session_id: str) -> pd.DataFrame:
    resp = client.table("session_turns").select("*").eq("session_id", session_id).order("turn_index").execute()
    return pd.DataFrame(resp.data)


def compute_asr_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (vulnerability, vulnerability_type) - same aggregation
    as redteam/scoring.py::compute_asr, but off already-logged DB rows
    instead of live DeepTeam test cases (the dashboard has no access to
    those, only what's in Supabase)."""
    columns = ["asi_category", "asi_display_name", "vulnerability", "vulnerability_type", "attempts", "bypassed", "defended", "errored", "asr_pct"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for (vuln, vtype), g in df.groupby(["vulnerability", "vulnerability_type"]):
        bypassed = int((g["outcome"] == "bypassed").sum())
        defended = int((g["outcome"] == "defended").sum())
        errored = int((g["outcome"] == "errored").sum())
        asi_code = next((c for c in g["asi_category"] if c), None)
        scored = bypassed + defended
        rows.append({
            "asi_category": asi_code,
            "asi_display_name": ASI_DISPLAY_NAMES.get(asi_code),
            "vulnerability": vuln,
            "vulnerability_type": vtype,
            "attempts": bypassed + defended + errored,
            "bypassed": bypassed,
            "defended": defended,
            "errored": errored,
            "asr_pct": (bypassed / scored * 100) if scored else 0.0,
        })
    return pd.DataFrame(rows, columns=columns).sort_values(["asi_category", "vulnerability", "vulnerability_type"], na_position="last")


def drift_incidents_over_time(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["total", "flagged"])
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    bucket = df.set_index("timestamp").sort_index()
    total = bucket["flagged"].resample(freq).count().rename("total")
    flagged = bucket["flagged"].resample(freq).sum().rename("flagged")
    return pd.concat([total, flagged], axis=1)


def drift_cause_breakdown(df: pd.DataFrame) -> pd.Series:
    if df.empty or "drift_cause" not in df:
        return pd.Series(dtype=int)
    flagged = df[df["flagged"] == True]  # noqa: E712 (pandas boolean mask, not identity check)
    if flagged.empty:
        return pd.Series(dtype=int)
    return flagged["drift_cause"].dropna().value_counts()

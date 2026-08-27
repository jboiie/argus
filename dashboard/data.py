"""Dashboard data layer - Supabase queries + pandas aggregation, split
from app.py so the aggregation math is unit-testable without a live
Supabase connection or Streamlit runtime. Only get_client/fetch_* touch
the network - build steps 21-24.
"""

import pandas as pd
from supabase import Client, create_client

from redteam.scoring import ASI_DISPLAY_NAMES


# Runs whose rows are fixtures or plumbing checks, not real results:
# telemetry/supabase_client.py's demo() inserts a hardcoded fake "RBAC"
# attack event, and the *_wiring_check / *_self_check runs exist only to
# prove a code path writes at all. They were being counted in the public
# dashboard's ASR alongside genuine findings - 10 fake rows in the headline
# number. Excluded by run label, since that's the only thing that
# distinguishes them at the row level.
EXCLUDED_RUN_LABELS = ("demo_self_check", "drift_diff_self_check")
EXCLUDED_LABEL_SUFFIXES = ("_wiring_check", "_wiring_test")


def get_client(url: str, key: str) -> Client:
    return create_client(url, key)


def _excluded_run_ids(client: Client) -> set[str]:
    resp = client.table("runs").select("run_id,label").limit(2000).execute()
    return {
        row["run_id"]
        for row in resp.data
        if row["label"] in EXCLUDED_RUN_LABELS
        or row["label"].endswith(EXCLUDED_LABEL_SUFFIXES)
    }


def _drop_excluded(df: pd.DataFrame, excluded: set[str]) -> pd.DataFrame:
    if df.empty or not excluded or "run_id" not in df:
        return df
    return df[~df["run_id"].isin(excluded)]


def fetch_runs(client: Client, run_type: str | None = None, limit: int = 500) -> pd.DataFrame:
    """Real runs only, newest first - fixtures/wiring checks filtered out on
    the same rule the row queries use. Backs the dashboard's run selector:
    without one, every view blends a dozen runs made under different
    simulator models and different quota conditions into one number, which
    isn't a result anyone can interpret."""
    query = client.table("runs").select("*").order("started_at", desc=True).limit(limit)
    if run_type:
        query = query.eq("run_type", run_type)
    df = pd.DataFrame(query.execute().data)
    if df.empty:
        return df
    keep = ~(
        df["label"].isin(EXCLUDED_RUN_LABELS)
        | df["label"].str.endswith(EXCLUDED_LABEL_SUFFIXES)
    )
    return df[keep]


def fetch_attack_events(client: Client, limit: int = 1000) -> pd.DataFrame:
    resp = client.table("attack_events").select("*").order("timestamp", desc=True).limit(limit).execute()
    return _drop_excluded(pd.DataFrame(resp.data), _excluded_run_ids(client))


def fetch_drift_incidents(client: Client, limit: int = 1000) -> pd.DataFrame:
    resp = client.table("drift_incidents").select("*").order("timestamp", desc=True).limit(limit).execute()
    return _drop_excluded(pd.DataFrame(resp.data), _excluded_run_ids(client))


def fetch_session_turns(client: Client, session_id: str) -> pd.DataFrame:
    resp = client.table("session_turns").select("*").eq("session_id", session_id).order("turn_index").execute()
    return pd.DataFrame(resp.data)


def fetch_mandates(client: Client, limit: int = 1000) -> pd.DataFrame:
    resp = client.table("mandates").select("*").order("authorized_at", desc=True).limit(limit).execute()
    return _drop_excluded(pd.DataFrame(resp.data), _excluded_run_ids(client))


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

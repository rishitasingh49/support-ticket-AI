import pandas as pd
from datetime import datetime
from app.db import get_connection


def load_tickets_df() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM tickets", conn, parse_dates=["created_at"])
    conn.close()
    return df


def find_long_resolution_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    resolved = df[df["resolution_time_hrs"].notna()]
    if resolved.empty:
        return pd.DataFrame()

    mean = resolved["resolution_time_hrs"].mean()
    std = resolved["resolution_time_hrs"].std()
    threshold = mean + 2 * std

    flagged = resolved[resolved["resolution_time_hrs"] > threshold].copy()
    flagged["anomaly_reason"] = f"Resolution time exceeds mean+2*std ({threshold:.1f}h)"
    return flagged[["ticket_id", "priority", "status", "resolution_time_hrs", "anomaly_reason"]]


def find_stale_critical_tickets(df: pd.DataFrame, hours_threshold: int = 24) -> pd.DataFrame:
    now = pd.Timestamp(datetime.now())
    open_tickets = df[df["status"].isin(["Open", "Escalated"])].copy()
    open_tickets["age_hrs"] = (now - open_tickets["created_at"]).dt.total_seconds() / 3600

    flagged = open_tickets[
        (open_tickets["priority"].isin(["Critical", "High"]))
        & (open_tickets["age_hrs"] > hours_threshold)
    ].copy()
    flagged["anomaly_reason"] = f"Unresolved {hours_threshold}+ hours despite high priority"
    return flagged[["ticket_id", "priority", "status", "age_hrs", "anomaly_reason"]]


def get_all_anomalies() -> dict:
    df = load_tickets_df()

    long_resolution = find_long_resolution_anomalies(df)
    stale_critical = find_stale_critical_tickets(df)

    return {
        "long_resolution_anomalies": long_resolution.to_dict(orient="records"),
        "stale_critical_anomalies": stale_critical.to_dict(orient="records"),
        "total_flagged": len(long_resolution) + len(stale_critical),
    }
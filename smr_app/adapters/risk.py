from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from ._legacy import import_domain_module
from .contracts import AdapterResult, table_columns


@dataclass(frozen=True)
class RiskContextRequest:
    ticker: str | None = None
    limit: int = 30


def load_risk_context(conn: sqlite3.Connection, request: RiskContextRequest) -> AdapterResult:
    ticker = request.ticker.strip().upper() if request.ticker else None
    alerts: list[dict] = []
    columns = table_columns(conn, "risk_alert")
    if columns:
        lifecycle = "COALESCE(lifecycle_status, 'opened')" if "lifecycle_status" in columns else "'opened'"
        occurrences = "COALESCE(occurrence_count, 1)" if "occurrence_count" in columns else "1"
        where = "acknowledged=0"
        params: list[object] = []
        if ticker:
            where += " AND (UPPER(COALESCE(ts_code, ''))=? OR ts_code IS NULL)"
            params.append(ticker)
        params.append(max(1, min(int(request.limit), 200)))
        rows = conn.execute(
            f"""
            SELECT alert_id, alert_time, alert_type, severity, ts_code, message, action,
                   {lifecycle} AS lifecycle_status, {occurrences} AS occurrence_count
            FROM risk_alert
            WHERE {where}
            ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END,
                     datetime(alert_time) DESC, alert_id DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
        alerts = [
            {
                "alert_id": row[0],
                "alert_time": row[1],
                "alert_type": row[2],
                "severity": row[3],
                "ticker": row[4],
                "message": row[5],
                "action": row[6],
                "lifecycle_status": row[7],
                "occurrence_count": row[8],
            }
            for row in rows
        ]
    try:
        health_module = import_domain_module("smr_data_health")
        health = health_module.build_health_snapshot(health_module.health_rows(conn))
    except Exception:
        health = {"items": [], "counts_by_status": {}}
    return AdapterResult("ok", {"ticker": ticker, "alerts": alerts, "data_health": health})

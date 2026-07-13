from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .contracts import AdapterResult, loads_json, relation_exists


@dataclass(frozen=True)
class DecisionContextRequest:
    ticker: str
    limit: int = 20


def load_decision_context(conn: sqlite3.Connection, request: DecisionContextRequest) -> AdapterResult:
    ticker = request.ticker.strip().upper()
    if not ticker:
        return AdapterResult("error", error="ticker is required")
    if not relation_exists(conn, "decision_ledger"):
        return AdapterResult("missing", {"ticker": ticker, "count": 0, "items": []})
    rows = conn.execute(
        """
        SELECT decision_id, ticker, market, theme, action, status, decision_time,
               thesis_summary, evidence_ids_json, bear_case_summary, kill_conditions_json,
               risk_notes, human_review_status, outcome_status, metadata_json, updated_at
        FROM decision_ledger
        WHERE UPPER(ticker)=?
        ORDER BY datetime(COALESCE(updated_at, decision_time)) DESC
        LIMIT ?
        """,
        (ticker, max(1, min(int(request.limit), 200))),
    ).fetchall()
    items = [
        {
            "decision_id": row[0],
            "ticker": row[1],
            "market": row[2],
            "theme": row[3],
            "action": row[4],
            "status": row[5],
            "decision_time": row[6],
            "thesis_summary": row[7],
            "evidence_ids": loads_json(row[8], []),
            "bear_case_summary": row[9],
            "kill_conditions": loads_json(row[10], []),
            "risk_notes": row[11],
            "human_review_status": row[12],
            "outcome_status": row[13],
            "metadata": loads_json(row[14], {}),
            "updated_at": row[15],
        }
        for row in rows
    ]
    return AdapterResult("ok" if items else "missing", {"ticker": ticker, "count": len(items), "items": items})

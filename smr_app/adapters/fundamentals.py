from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from ._legacy import import_domain_module
from .contracts import AdapterResult


@dataclass(frozen=True)
class FundamentalsRequest:
    ticker: str


def load_fundamentals(conn: sqlite3.Connection, request: FundamentalsRequest) -> AdapterResult:
    ticker = request.ticker.strip().upper()
    if not ticker:
        return AdapterResult("error", error="ticker is required")
    try:
        module = import_domain_module("smr_fundamentals")
        snapshot = module.latest_fundamentals_snapshot(conn, ticker)
    except Exception as exc:
        return AdapterResult("error", {"ticker": ticker}, error=f"fundamentals adapter failed: {exc}")
    if not snapshot:
        return AdapterResult("missing", {"ticker": ticker, "snapshot": {}})
    if str(snapshot.get("ticker") or "").upper() != ticker:
        return AdapterResult("error", {"ticker": ticker}, error="fundamentals snapshot ticker mismatch")
    return AdapterResult("ok", {"ticker": ticker, "snapshot": snapshot})

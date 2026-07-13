from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from ._legacy import import_domain_module
from .contracts import AdapterResult


@dataclass(frozen=True)
class ValuationRequest:
    ticker: str


def load_valuation(conn: sqlite3.Connection, request: ValuationRequest) -> AdapterResult:
    ticker = request.ticker.strip().upper()
    if not ticker:
        return AdapterResult("error", error="ticker is required")
    try:
        module = import_domain_module("smr_valuation")
        snapshot = module.latest_valuation_snapshot(conn, ticker)
    except Exception as exc:
        return AdapterResult("error", {"ticker": ticker}, error=f"valuation adapter failed: {exc}")
    if not snapshot:
        return AdapterResult("missing", {"ticker": ticker, "snapshot": {}})
    if str(snapshot.get("ticker") or "").upper() != ticker:
        return AdapterResult("error", {"ticker": ticker}, error="valuation snapshot ticker mismatch")
    return AdapterResult("ok", {"ticker": ticker, "snapshot": snapshot})

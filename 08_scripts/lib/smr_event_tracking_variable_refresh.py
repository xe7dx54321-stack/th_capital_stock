#!/usr/bin/env python3
"""Phase 48 event-driven tracking variable refresh."""

from __future__ import annotations

from typing import Any

from smr_paper_watchlist_tracking_variables import TRACKING_VARIABLE_ROWS
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


def build_event_tracking_variable_refresh(
    events: list[dict[str, Any]],
    ticker: str = TARGET_REVIEW_TICKER,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    touched_vars: set[str] = set()
    for event in events:
        for var in event.get("linked_tracking_variables", []):
            touched_vars.add(var)
    deltas: list[dict[str, Any]] = []
    for row in TRACKING_VARIABLE_ROWS:
        var = row["variable"]
        current = row["current_status"]
        if var in touched_vars:
            deltas.append({
                "variable": var,
                "previous_status": current,
                "current_status": current,
                "delta": "unchanged_positive",
                "event_impact": "supportive_but_not_new_confirmed_variable",
                "allowed_usage": row.get("allowed_usage", "research_tracking"),
            })
    summary = {
        "strengthened_variables": 0,
        "weakened_variables": 0,
        "unchanged_variables": len(TRACKING_VARIABLE_ROWS),
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "tracking_variable_refresh": {
            "variables_checked": len(TRACKING_VARIABLE_ROWS),
            "variables_touched_by_event": list(touched_vars),
            "variable_deltas": deltas,
            "strengthened_variables": 0,
            "weakened_variables": 0,
            "unchanged_variables": len(TRACKING_VARIABLE_ROWS),
        },
        "safety": {
            "refresh_is_not_trading_signal": True,
            "scenario_proxy_unconfirmed_preserved": True,
            "pending_created": 0,
            "paper_order_created": 0,
        },
    }

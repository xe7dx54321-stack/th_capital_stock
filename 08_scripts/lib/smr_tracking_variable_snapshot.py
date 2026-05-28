#!/usr/bin/env python3
"""Phase 47 tracking variable snapshot for periodic watchlist review."""

from __future__ import annotations

from typing import Any

from smr_paper_watchlist_tracking_variables import TRACKING_VARIABLE_ROWS
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


def build_tracking_variable_snapshot(ticker: str = TARGET_REVIEW_TICKER) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    snapshot_rows = []
    for row in TRACKING_VARIABLE_ROWS:
        var = row["variable"]
        current = row["current_status"]
        row_entry: dict[str, Any] = {
            "variable": var,
            "previous_status": current,
            "current_status": current,
            "delta": "unchanged_positive",
            "interpretation": "",
            "allowed_usage": row.get("allowed_usage", "research_tracking"),
        }
        if current in {"unconfirmed", "scenario_only", "proxy_only"}:
            row_entry["delta"] = "unchanged_gap"
            row_entry["interpretation"] = "still blocks investment pending"
        elif current == "partially_mitigated_not_cleared":
            row_entry["delta"] = "unchanged_gap"
            row_entry["interpretation"] = "partially mitigated, still requires tracking"
        elif current in {"supported", "partially_supported"}:
            row_entry["delta"] = "unchanged_positive"
            row_entry["interpretation"] = "continues to support thesis"
        elif current in {"scenario_analysis_only", "watchlist_positive_but_unconfirmed"}:
            row_entry["delta"] = "unchanged_gap"
            row_entry["interpretation"] = "scenario-level or unconfirmed, tracking continues"
        elif current == "watchlist_sufficient_not_pending_sufficient":
            row_entry["delta"] = "unchanged_gap"
            row_entry["interpretation"] = "sufficient for tracking, insufficient for pending"
        else:
            row_entry["delta"] = "needs_more_evidence"
            row_entry["interpretation"] = "status unclear, needs evidence update"
        snapshot_rows.append(row_entry)

    def count(delta_val: str) -> int:
        return sum(1 for r in snapshot_rows if r["delta"] == delta_val)

    summary = {
        "strengthened_variables": count("strengthened"),
        "weakened_variables": count("weakened"),
        "unchanged_positive": count("unchanged_positive"),
        "unchanged_gaps": count("unchanged_gap"),
        "needs_more_evidence": count("needs_more_evidence"),
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "tracking_variable_snapshot": {
            "variables_checked": len(snapshot_rows),
            "snapshot_rows": snapshot_rows,
            "summary": summary,
        },
        "safety": {
            "snapshot_is_trading_signal": False,
            "snapshot_triggers_pending": False,
            "snapshot_triggers_order": False,
            "snapshot_triggers_trade": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
        },
    }

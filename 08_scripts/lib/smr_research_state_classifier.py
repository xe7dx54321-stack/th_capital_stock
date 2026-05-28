#!/usr/bin/env python3
"""Phase 34 conservative ticker-level research state classifier."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_post_governance_evidence_state import build_post_governance_evidence_state, safe_next_evidence_plan_for_ticker
from smr_wiki import now_ts


RESEARCH_STATES = {
    "research_strengthened",
    "research_weakened",
    "unchanged_needs_more_data",
    "ready_for_research_packet",
    "deprioritize",
    "blocked_by_evidence_quality",
    "unknown",
}


def classify_ticker_research_state(ticker_row: dict[str, Any]) -> dict[str, Any]:
    state = ticker_row.get("evidence_state") or {}
    delta = ticker_row.get("evidence_delta") or {}
    reviewed = int(state.get("reviewed_evidence") or 0)
    approved = int(state.get("approved_evidence") or 0)
    rejected = int(state.get("rejected_evidence") or 0)
    downgraded = int(state.get("downgraded_evidence") or 0)
    noisy = int(state.get("marked_noise") or 0)
    needs_better = int(state.get("needs_better_source") or 0)
    weakening = rejected + downgraded + noisy + needs_better
    core_gaps = list(ticker_row.get("remaining_core_gaps") or [])

    if reviewed and noisy + rejected >= 3:
        research_state = "blocked_by_evidence_quality"
        confidence = "medium"
        main_reason = "too many reviewed evidence items were rejected or marked noise"
    elif reviewed and weakening > approved:
        research_state = "research_weakened"
        confidence = "medium"
        main_reason = "reviewed evidence weakened key variables and core missing variables remain unresolved"
    elif reviewed and approved > weakening and len(core_gaps) <= 2:
        research_state = "ready_for_research_packet"
        confidence = "medium"
        main_reason = "reviewed evidence improved key variables enough for a deeper research packet, not for promotion"
    elif reviewed and approved > weakening:
        research_state = "research_strengthened"
        confidence = "medium"
        main_reason = "reviewed evidence supports key variables, but still not enough for pending"
    else:
        research_state = "unchanged_needs_more_data"
        confidence = "medium" if core_gaps else "low_to_medium"
        main_reason = "evidence governance changed little or no reviewed evidence exists for this ticker; core variables remain missing"

    positive = []
    if delta.get("strengthened_variables"):
        positive.append("reviewed evidence supports " + ", ".join(delta.get("strengthened_variables") or []))
    negative = []
    if delta.get("weakened_variables"):
        negative.append("reviewed evidence weakened " + ", ".join(delta.get("weakened_variables") or []))
    negative.extend(f"{gap} missing" for gap in core_gaps[:4])
    return {
        "ticker": ticker_row.get("ticker"),
        "company_name": ticker_row.get("company_name"),
        "research_state": research_state,
        "state_confidence": confidence,
        "main_reason": main_reason,
        "positive_factors": positive or ["no reviewed evidence strengthened a core variable"],
        "negative_factors": list(dict.fromkeys(negative)) or ["core evidence gaps still require monitoring"],
        "recommended_next_step": "build targeted evidence plan for ASP, supplier share, customer allocation, and official consensus",
        "promotion_status": {
            "new_pending_created": False,
            "promotion_allowed": False,
            "reason": "research state classification only",
        },
    }


def build_research_state_classification(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    tickers: str | None = None,
) -> dict[str, Any]:
    evidence = build_post_governance_evidence_state(conn, ticker=ticker, tickers=tickers)
    rows = [classify_ticker_research_state(row) for row in evidence.get("ticker_results") or []]
    counts = {state: sum(1 for row in rows if row.get("research_state") == state) for state in RESEARCH_STATES}
    return {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(rows),
            "research_strengthened": counts.get("research_strengthened", 0),
            "research_weakened": counts.get("research_weakened", 0),
            "unchanged_needs_more_data": counts.get("unchanged_needs_more_data", 0),
            "ready_for_research_packet": counts.get("ready_for_research_packet", 0),
            "deprioritize": counts.get("deprioritize", 0),
            "blocked_by_evidence_quality": counts.get("blocked_by_evidence_quality", 0),
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "ticker_results": rows,
        "next_evidence_plan_preview": [
            {"ticker": row.get("ticker"), "plan_items": safe_next_evidence_plan_for_ticker(row)}
            for row in evidence.get("ticker_results") or []
        ],
        "safety": {
            "research_state_is_promotion_status": False,
            "ready_for_research_packet_is_pending": False,
            "research_strengthened_is_trade_signal": False,
            "promotion_rules_relaxed": False,
        },
    }

#!/usr/bin/env python3
"""Phase 48 watchlist event trigger detector."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_paper_watchlist_entry import get_paper_watchlist_entry
from smr_paper_watchlist_periodic_review import get_periodic_review_state
from smr_periodic_review_audit import list_periodic_review_audits
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_watchlist_event_trigger import SAMPLE_EVENTS, build_event_trigger
from smr_wiki import now_ts


def detect_events(
    conn: sqlite3.Connection,
    ticker: str = TARGET_REVIEW_TICKER,
    *,
    use_sample_events: bool = True,
) -> list[dict[str, Any]]:
    ticker = normalize_ticker(ticker)
    events: list[dict[str, Any]] = []
    if use_sample_events:
        for sample in SAMPLE_EVENTS:
            if sample["ticker"] == ticker:
                event = build_event_trigger(
                    ticker=ticker,
                    event_type=sample["event_type"],
                    event_source=sample["event_source"],
                    event_title=sample["event_title"],
                    linked_tracking_variables=list(sample["linked_tracking_variables"]),
                    event_strength=sample.get("event_strength", "medium"),
                )
                events.append(event)
    entry = get_paper_watchlist_entry(conn, ticker)
    if entry and entry.get("watchlist_status") in {
        "active_tracking", "tracking_strengthened", "tracking_weakened",
    }:
        review_state = get_periodic_review_state(conn, ticker)
        if review_state and review_state.get("review_status") == "review_due":
            events.append(build_event_trigger(
                ticker=ticker,
                event_type="periodic_review_due",
                event_source="phase47_periodic_review_state",
                event_title="Periodic review is due",
                linked_tracking_variables=["thesis_strength"],
                event_strength="low",
            ))
    return events


def build_event_detector_result(
    conn: sqlite3.Connection,
    ticker: str = TARGET_REVIEW_TICKER,
) -> dict[str, Any]:
    events = detect_events(conn, ticker)
    active_events = [e for e in events if e["requires_evidence_refresh"]]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "event_trigger_detector": {
            "events_checked": len(events),
            "events_detected": len(active_events) + sum(
                1 for e in events if not e["requires_evidence_refresh"]
            ),
            "refresh_required": len(active_events),
            "revalidation_required": len(active_events),
            "event_rows": events,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
        },
        "safety": {
            "detector_creates_pending": False,
            "detector_creates_order": False,
            "detector_creates_trade": False,
            "detector_does_not_fetch_raw": True,
        },
    }

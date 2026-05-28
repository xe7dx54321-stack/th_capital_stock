#!/usr/bin/env python3
"""Phase 49 metadata-to-watchlist event adapter."""

from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import generate_execution_id, now_ts

def adapt_to_watchlist_event(classifier_row: dict[str, Any], ticker=TARGET_REVIEW_TICKER):
    ticker = normalize_ticker(ticker)
    return {"event_id": generate_execution_id(f"watchlist_event_{ticker.split('.')[0]}_real"),
            "source_id": classifier_row.get("source_id"), "event_type": classifier_row.get("event_type"),
            "event_source": "cninfo_real", "event_title": classifier_row.get("source_title"),
            "event_date": now_ts(), "linked_tracking_variables": classifier_row.get("linked_tracking_variables",[]),
            "event_strength": classifier_row.get("event_strength","medium"),
            "requires_evidence_refresh": classifier_row.get("requires_evidence_refresh",True),
            "requires_revalidation": classifier_row.get("requires_revalidation",True),
            "allowed_action": "research_only_revalidation",
            "forbidden_actions": ["create_pending","create_paper_order","create_trade"],
            "pending_created": False, "paper_order_created": False, "real_trade_created": False}

def build_adapted_events(classifier_rows: list[dict[str, Any]], ticker=TARGET_REVIEW_TICKER):
    ticker = normalize_ticker(ticker)
    events = [adapt_to_watchlist_event(r, ticker) for r in classifier_rows if r.get("event_type") != "unknown"]
    return {"generated_at": now_ts(), "ticker": ticker,
            "metadata_watchlist_events": {
                "classified_events": len(classifier_rows), "watchlist_events_created": len(events),
                "events": events, "pending_created": 0, "paper_order_created": 0},
            "safety": {"adapter_does_not_execute_refresh": True, "adapter_creates_pending": False,
                       "adapter_preserves_source_linkage": True}}

#!/usr/bin/env python3
"""Phase 49 real source event deduplication."""

from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts
import re

def normalize_title(title: str) -> str:
    return re.sub(r"\s+", "", title)[:80] if title else ""

def dedupe_events(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: set[tuple] = set()
    unique: list[dict[str, Any]] = []
    skipped = 0
    for e in events:
        key = (e.get("event_type",""), normalize_title(e.get("event_title","")), e.get("event_source",""))
        if key in seen:
            skipped += 1
        else:
            seen.add(key)
            unique.append(e)
    return unique, skipped

def build_dedup_report(events: list[dict[str, Any]], ticker=TARGET_REVIEW_TICKER):
    unique, skipped = dedupe_events(events)
    return {"generated_at": now_ts(), "ticker": normalize_ticker(ticker),
            "event_dedup_report": {
                "events_checked": len(events), "unique_events": len(unique),
                "duplicates_skipped": skipped,
                "dedupe_keys_used": ["event_type","event_title_normalized","event_source"]},
            "safety": {"dedup_does_not_delete_metadata": True, "dedup_does_not_create_pending": True}}

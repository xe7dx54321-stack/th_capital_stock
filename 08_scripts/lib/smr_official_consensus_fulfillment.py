#!/usr/bin/env python3
"""Official consensus fulfillment path for Phase 42."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_official_consensus_availability import build_official_consensus_availability
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_specific_evidence_request import evidence_request_id_for, get_specific_evidence_request
from smr_wiki import now_ts


def build_official_consensus_fulfillment(
    conn: sqlite3.Connection,
    ticker: str = TARGET_REVIEW_TICKER,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    request = get_specific_evidence_request(conn, evidence_request_id_for(ticker, "official_consensus"))
    availability = build_official_consensus_availability(conn, ticker).get("official_consensus_availability") or {}
    body = {
        "request_status": request.get("status") or "missing_request",
        "availability_status": availability.get("status") or "unknown",
        "manual_intake_supported": True,
        "authorized_source_required": True,
        "internal_proxy_allowed": False,
        "fulfilled": False,
        "fulfillment_status": "authorized_source_required",
        "required_fields": [
            "source_provider",
            "source_date",
            "permission_status",
            "quoted_span_or_authorized_reference",
        ],
        "do_not_do": availability.get("do_not_do") or [
            "do not treat internal proxy as official consensus",
            "do not infer consensus from management commentary",
            "do not scrape restricted consensus data",
        ],
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "official_consensus_fulfillment": body,
        "safety": {
            "evidence_written": False,
            "official_consensus_added": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }

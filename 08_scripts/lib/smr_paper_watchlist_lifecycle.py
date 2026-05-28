#!/usr/bin/env python3
"""Phase 46 paper watchlist lifecycle rules."""

from __future__ import annotations

from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker


WATCHLIST_STATUSES = {
    "paper_watchlist_candidate",
    "active_tracking",
    "tracking_paused",
    "tracking_strengthened",
    "tracking_weakened",
    "tracking_needs_more_evidence",
    "tracking_archived",
    "unknown",
}

ALLOWED_TRANSITIONS = {
    ("paper_watchlist_candidate", "active_tracking"),
    ("active_tracking", "tracking_strengthened"),
    ("active_tracking", "tracking_weakened"),
    ("active_tracking", "tracking_needs_more_evidence"),
    ("active_tracking", "tracking_paused"),
    ("tracking_paused", "active_tracking"),
    ("active_tracking", "tracking_archived"),
    ("tracking_strengthened", "tracking_needs_more_evidence"),
    ("tracking_strengthened", "tracking_paused"),
    ("tracking_strengthened", "tracking_archived"),
    ("tracking_weakened", "tracking_needs_more_evidence"),
    ("tracking_weakened", "tracking_paused"),
    ("tracking_weakened", "tracking_archived"),
    ("tracking_needs_more_evidence", "active_tracking"),
    ("tracking_needs_more_evidence", "tracking_paused"),
    ("tracking_needs_more_evidence", "tracking_archived"),
}

FORBIDDEN_STATUSES = {
    "pending_human_review",
    "approved_paper",
    "paper_order",
    "paper_position",
    "real_trade",
    "create_pending",
    "create_paper_order",
    "create_trade",
}


def validate_watchlist_transition(before_status: str | None, after_status: str) -> tuple[bool, str]:
    before = str(before_status or "paper_watchlist_candidate")
    after = str(after_status or "unknown")
    if after in FORBIDDEN_STATUSES:
        return False, "forbidden_watchlist_transition_to_investment_or_trade_state"
    if after not in WATCHLIST_STATUSES:
        return False, f"unsupported_watchlist_status:{after}"
    if before == after:
        return True, "idempotent_transition"
    if before not in WATCHLIST_STATUSES:
        return False, f"unsupported_before_status:{before}"
    if (before, after) not in ALLOWED_TRANSITIONS:
        return False, f"transition_not_allowed:{before}->{after}"
    return True, "allowed"


def build_watchlist_transition(
    *,
    ticker: str = TARGET_REVIEW_TICKER,
    before_status: str | None = "paper_watchlist_candidate",
    after_status: str = "active_tracking",
    transition_reason: str = "Phase45 final research conclusion allows research-only tracking",
) -> dict[str, Any]:
    ok, reason = validate_watchlist_transition(before_status, after_status)
    return {
        "ticker": normalize_ticker(ticker),
        "before_status": before_status or "paper_watchlist_candidate",
        "after_status": after_status,
        "transition_allowed": ok,
        "transition_validation_reason": reason,
        "transition_reason": transition_reason,
        "pending_created": False,
        "paper_order_created": False,
        "real_trade_created": False,
    }

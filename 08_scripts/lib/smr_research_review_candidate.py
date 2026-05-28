#!/usr/bin/env python3
"""Phase 39 research-review candidate classification."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_evidence_contribution_analyzer import TARGET_TICKER, build_evidence_contribution
from smr_research_evidence_chain import build_research_evidence_chain
from smr_research_quality_scoring import build_research_quality_score
from smr_wiki import now_ts


REVIEW_STATUSES = {
    "research_review_candidate",
    "not_ready_for_research_review",
    "continue_evidence_acquisition",
    "repair_required_before_review",
    "deprioritize",
}
WHY_NOT_PENDING = [
    "supplier share unconfirmed",
    "official consensus missing",
    "confirmed customer allocation missing",
]


def _human_questions(variables: list[str]) -> list[str]:
    questions = [
        "Do product mix disclosures materially support higher-value optical module exposure?",
        "Is order visibility evidence strong enough to reduce the bear case?",
        "What additional evidence would be needed for ASP support?",
    ]
    if "shipment" in variables:
        questions.append("Does shipment commentary add incremental support without implying confirmed shipment numbers?")
    return questions


def build_research_review_candidate_decision(conn: sqlite3.Connection, ticker: str = TARGET_TICKER) -> dict[str, Any]:
    ticker = str(ticker or TARGET_TICKER).strip().upper()
    contribution = build_evidence_contribution(conn, ticker).get("evidence_contribution") or {}
    variables = list(contribution.get("variables_strengthened") or [])
    chain = build_research_evidence_chain(conn, ticker).get("evidence_chain") or {}
    quality = build_research_quality_score(conn, ticker).get("research_quality") or {}
    total_evidence = int(chain.get("total_evidence") or 0)
    quality_after = str(quality.get("overall_quality") or "low")
    new_evidence = int(contribution.get("new_evidence_count") or 0)

    if total_evidence == 0:
        decision = "repair_required_before_review"
        confidence = "high"
        why_eligible: list[str] = []
        why_not_ready = ["evidence chain is empty", "repair is required before research deepening"]
    elif new_evidence >= 3 and len(variables) >= 2 and quality_after in {"medium_low", "medium"}:
        decision = "research_review_candidate"
        confidence = "medium"
        why_eligible = [
            f"evidence chain has {total_evidence} usable rows after Phase 38",
            f"new evidence supports {' / '.join(variables)}",
            "research quality delta is strengthened_with_new_supporting_evidence",
            "why-not-pending boundary is explicit",
        ]
        why_not_ready = []
    elif total_evidence > 0:
        decision = "continue_evidence_acquisition"
        confidence = "medium_low"
        why_eligible = []
        why_not_ready = ["new evidence has not strengthened enough variables for manual research review"]
    else:
        decision = "not_ready_for_research_review"
        confidence = "low"
        why_eligible = []
        why_not_ready = ["research packet is not strong enough for manual review"]

    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "research_review_decision": {
            "decision": decision,
            "confidence": confidence,
            "why_eligible": why_eligible,
            "why_not_ready": why_not_ready,
            "why_not_pending": WHY_NOT_PENDING,
            "human_review_questions": _human_questions(variables),
            "promotion_boundary": {
                "pending_allowed": False,
                "paper_order_allowed": False,
                "promotion_allowed": False,
                "real_trade_allowed": False,
            },
        },
        "safety": {
            "research_review_candidate_is_pending": False,
            "trade_recommendation_generated": False,
            "paper_order_created": 0,
            "new_pending_created": 0,
            "promotion_rules_relaxed": False,
        },
    }

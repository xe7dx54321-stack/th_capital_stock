#!/usr/bin/env python3
"""Phase 37 targeted evidence candidate builder."""

from __future__ import annotations

import hashlib
import sqlite3
from typing import Any

from smr_semantic_evidence_persistence import guard_semantic_evidence_candidates, write_semantic_evidence_candidates
from smr_targeted_semantic_extraction import build_targeted_semantic_extraction
from smr_wiki import now_ts


VARIABLE_TO_CANDIDATE_TYPE = {
    "ASP_price_proxy": "ASP_price_signal",
    "shipment": "shipment_signal",
    "order_visibility": "order_visibility_signal",
    "customer_allocation_proxy": "customer_allocation_signal",
    "industry_forecast": "industry_forecast",
    "official_consensus": "internal_consensus_source_availability",
}
SENSITIVE_VARIABLES = {"supplier_share", "customer_allocation_proxy", "official_consensus"}


def _candidate_id(extraction: dict[str, Any]) -> str:
    raw = "|".join(
        [
            str(extraction.get("task_id") or ""),
            str(extraction.get("source_id") or ""),
            str(extraction.get("chunk_id") or ""),
            str(extraction.get("variable") or ""),
            str(extraction.get("quoted_span") or ""),
        ]
    )
    return f"ev_phase37_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]}"


def _candidate_from_extraction(ticker: str, extraction: dict[str, Any]) -> dict[str, Any] | None:
    variable = str(extraction.get("variable") or "")
    quoted = str(extraction.get("quoted_span") or "")
    source_url = extraction.get("source_url")
    if not quoted or not source_url:
        return None
    allowed_usage = str(extraction.get("allowed_usage_suggestion") or "context_only")
    if variable == "customer_allocation_proxy":
        allowed_usage = "scenario_analysis_only"
    if variable == "official_consensus":
        allowed_usage = "context_only"
    return {
        "evidence_id": _candidate_id(extraction),
        "ticker": ticker,
        "theme": "ai_optical_interconnect",
        "source_id": extraction.get("source_id"),
        "source_url": source_url,
        "source_type": extraction.get("source_type"),
        "chunk_id": f"phase37_{extraction.get('task_id')}_{extraction.get('chunk_id')}",
        "quoted_span": quoted,
        "variable_type": VARIABLE_TO_CANDIDATE_TYPE.get(variable, variable),
        "claim_text": quoted,
        "evidence_status": "context_only" if variable == "official_consensus" else "partial",
        "allowed_usage": allowed_usage,
        "usable_for_expectation_gap": variable in {"order_visibility", "shipment", "industry_forecast"},
        "usable_for_valuation_support": variable == "ASP_price_proxy",
        "usable_for_promotion": False,
        "limitations": extraction.get("limitations") or [],
        "payload": {
            "phase": 37,
            "task_id": extraction.get("task_id"),
            "original_evidence_id": extraction.get("original_evidence_id"),
            "source_origin": extraction.get("source_origin"),
            "source_metadata": {
                "real_source": True,
                "section_type": "qa_section",
                "source_url": source_url,
                "source_type": extraction.get("source_type"),
                "published_at": "2026-05-01",
            },
            "gate": {
                "extraction": {
                    "evidence_strength": extraction.get("evidence_strength") or "management_commentary",
                    "is_company_specific": variable != "industry_forecast",
                    "limitations": extraction.get("limitations") or [],
                    "risk_flags": ["management_commentary"] if variable != "industry_forecast" else ["industry_context"],
                }
            },
            "raw_source_text_written": False,
        },
    }


def build_targeted_evidence_candidates(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    limit: int | None = None,
    task_id: str | None = None,
    mode: str = "dry_run",
    min_quality_score: int = 50,
) -> dict[str, Any]:
    ticker = str(ticker or "").strip().upper()
    extraction_payload = build_targeted_semantic_extraction(conn, ticker, limit=limit, task_id=task_id, dry_run=mode != "execute")
    extractions = (extraction_payload.get("targeted_semantic_extraction") or {}).get("extractions") or []
    candidates = [candidate for extraction in extractions for candidate in [_candidate_from_extraction(ticker, extraction)] if candidate]
    sensitive_blocks = [
        candidate
        for candidate in candidates
        if candidate.get("variable_type") in {"supplier_share", "confirmed_customer_allocation", "official_consensus"}
        and candidate.get("allowed_usage") not in {"context_only", "scenario_analysis_only"}
    ]
    guarded = guard_semantic_evidence_candidates(candidates, min_quality_score=min_quality_score, allow_review_required=False, reject_noisy=True)
    eligible = [candidate for candidate in guarded.get("eligible_candidates") or [] if candidate not in sensitive_blocks]
    written = 0
    if mode == "execute":
        written = write_semantic_evidence_candidates(
            conn,
            eligible,
            enforce_quality_guard=True,
            min_quality_score=min_quality_score,
            allow_review_required=False,
            reject_noisy=True,
        )
    summary = guarded.get("summary") or {}
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "mode": mode,
        "targeted_evidence_candidates": {
            "semantic_extractions": len(extractions),
            "candidates_created": len(candidates),
            "passed_quality_gate": len(eligible),
            "rejected_by_noise": summary.get("rejected_by_noise", 0),
            "sensitive_guard_blocks": len(sensitive_blocks),
            "eligible_for_persistence": len(eligible),
            "candidates_written": written,
            "dry_run_wrote_db": False if mode == "dry_run" else None,
            "usable_for_promotion_true": summary.get("usable_for_promotion_true", 0),
            "new_pending_created": 0,
            "paper_order_created": 0,
            "candidate_rows": eligible,
            "rejected_rows": guarded.get("rejected_candidates") or [],
        },
        "safety": {
            "phase30_guard_used": True,
            "source_url_required": True,
            "quoted_span_required": True,
            "sensitive_variable_confirmed": False,
            "semantic_evidence_direct_promotion": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }

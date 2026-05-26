#!/usr/bin/env python3
"""Phase 20 valuation gate diagnostics."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_evidence_quality import evidence_quality_summary
from smr_promotion_block_reason import build_ticker_block_diagnostics
from smr_valuation import latest_valuation_snapshot


VALUATION_BLOCKER_CODES = {
    "VALUATION_STALE",
    "PRICE_STALE",
    "PEER_COMPARISON_MISSING",
    "PEER_COMPARISON_WEAK",
    "HISTORICAL_VALUATION_MISSING",
    "HISTORICAL_VALUATION_WEAK",
    "FORWARD_EPS_MISSING",
    "FORWARD_EPS_PROXY_ONLY",
    "VALUATION_CONFLICTS_WITH_THESIS",
    "VALUATION_CONFIDENCE_LOW",
    "VALUATION_EVIDENCE_QUALITY_LOW",
}


def normalize_ticker(ticker: str | None) -> str:
    return str(ticker or "").strip().upper()


def _forward_eps(snapshot: dict[str, Any]) -> dict[str, Any]:
    metadata = snapshot.get("metadata") or {}
    inputs = metadata.get("inputs_used") or {}
    return inputs.get("forward_eps") or metadata.get("forward_eps") or {}


def _quality_for_ids(conn: sqlite3.Connection, evidence_ids: list[str]) -> str:
    if not evidence_ids:
        return "missing"
    summary = evidence_quality_summary(conn, evidence_ids)
    avg = float(summary.get("avg_quality_score") or 0.0)
    if summary.get("usable_for_promotion_count") or avg >= 0.68:
        return "high"
    if summary.get("usable_for_core_claim_count") or avg >= 0.55:
        return "medium"
    if avg >= 0.35:
        return "low"
    return "blocked"


def _peer_status(snapshot: dict[str, Any]) -> str:
    peer = snapshot.get("peer_comparison") or {}
    status = str(peer.get("peer_comparison_status") or "").lower()
    if status in {"promotion_supporting", "supporting"}:
        return "supporting"
    if status in {"partial", "available"}:
        return "partial"
    if status in {"weak"}:
        return "weak"
    return "missing"


def _historical_status(snapshot: dict[str, Any]) -> str:
    historical = snapshot.get("historical_valuation") or {}
    status = str(historical.get("status") or snapshot.get("historical_percentile_status") or "").lower()
    if status in {"available", "supporting"}:
        return "supporting"
    if status in {"partial"}:
        return "partial"
    if status in {"not_meaningful", "weak"}:
        return "weak"
    return "missing"


def _price_freshness(snapshot: dict[str, Any]) -> str:
    usage = str(snapshot.get("allowed_usage") or "").lower()
    status = str(snapshot.get("valuation_status") or "").lower()
    if usage == "blocked_due_to_stale_price" or "price_stale" in status:
        return "stale"
    if snapshot.get("current_price") is not None:
        return "fresh"
    return "missing"


def _status_for_snapshot(snapshot: dict[str, Any], blockers: list[str]) -> str:
    usage = str(snapshot.get("allowed_usage") or "").lower()
    if not snapshot:
        return "blocked"
    if "PRICE_STALE" in blockers or "VALUATION_STALE" in blockers:
        return "blocked"
    if usage in {"promotion_eligible", "promotion_supporting"}:
        return "promotion_supporting"
    if usage == "supporting_evidence":
        return "supporting_evidence"
    if usage == "context_only":
        return "context_only"
    if not snapshot.get("valuation_available"):
        return "insufficient"
    return "supporting_evidence" if not blockers else "insufficient"


def diagnose_valuation_gate(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    phase19_diag: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    snapshot = latest_valuation_snapshot(conn, ticker) or {}
    forward = _forward_eps(snapshot)
    evidence_ids = [str(item) for item in forward.get("source_evidence_ids") or [] if item]
    quality = _quality_for_ids(conn, evidence_ids)
    blockers: list[str] = []
    price = _price_freshness(snapshot)
    peer = _peer_status(snapshot)
    historical = _historical_status(snapshot)
    if not snapshot:
        blockers.extend(["VALUATION_STALE", "PRICE_STALE"])
    if price == "stale":
        blockers.append("PRICE_STALE")
    elif price == "missing":
        blockers.append("VALUATION_STALE")
    if peer == "missing":
        blockers.append("PEER_COMPARISON_MISSING")
    elif peer == "weak":
        blockers.append("PEER_COMPARISON_WEAK")
    if historical == "missing":
        blockers.append("HISTORICAL_VALUATION_MISSING")
    elif historical == "weak":
        blockers.append("HISTORICAL_VALUATION_WEAK")
    if not forward or forward.get("status") == "missing":
        blockers.append("FORWARD_EPS_MISSING")
    elif not forward.get("is_official_consensus"):
        blockers.append("FORWARD_EPS_PROXY_ONLY")
    if float(snapshot.get("valuation_confidence") or 0.0) < 0.45:
        blockers.append("VALUATION_CONFIDENCE_LOW")
    if evidence_ids and quality in {"low", "blocked"}:
        blockers.append("VALUATION_EVIDENCE_QUALITY_LOW")
    blockers = list(dict.fromkeys(blockers))
    after_status = _status_for_snapshot(snapshot, blockers)
    if phase19_diag is None:
        try:
            phase19_diag = build_ticker_block_diagnostics(conn, ticker)
        except Exception:
            phase19_diag = {}
    had_phase19_gate = "VALUATION_GATE" in [phase19_diag.get("primary_blocking_gate"), *(phase19_diag.get("secondary_blocking_gates") or [])]
    before_status = "context_only" if had_phase19_gate and after_status in {"supporting_evidence", "promotion_supporting"} else after_status
    next_fix = []
    if "PRICE_STALE" in blockers:
        next_fix.append("refresh valuation price input")
    if "PEER_COMPARISON_MISSING" in blockers:
        next_fix.append("add peer set and peer valuation evidence")
    if "HISTORICAL_VALUATION_MISSING" in blockers:
        next_fix.append("repair historical valuation sample")
    if "FORWARD_EPS_PROXY_ONLY" in blockers:
        next_fix.append("add official consensus or stronger independent proxy evidence")
    if "VALUATION_CONFIDENCE_LOW" in blockers:
        next_fix.append("increase valuation confidence with primary evidence")
    return {
        "ticker": ticker,
        "valuation_gate": {
            "before_status": before_status,
            "after_status": after_status,
            "blocks_pending": after_status in {"blocked", "insufficient", "context_only"},
            "allows_reduced_size_pending": after_status == "supporting_evidence",
            "valuation_components": {
                "price_freshness": price,
                "peer_comparison": peer,
                "historical_valuation": historical,
                "forward_eps": "official" if forward.get("is_official_consensus") else ("proxy" if forward.get("status") == "proxy" else "missing"),
                "evidence_quality": quality,
            },
            "remaining_valuation_blockers": blockers,
            "proxy_eps_not_official_consensus": not bool(forward.get("is_official_consensus")),
            "source_evidence_ids": evidence_ids,
            "next_fix": next_fix or ["keep valuation as supporting metadata"],
            "promotion_metadata": {
                "phase": 20,
                "diagnostic_only": True,
                "proxy_eps_is_official_consensus": False,
            },
        },
    }


def valuation_gate_improved(payload: dict[str, Any]) -> bool:
    gate = payload.get("valuation_gate") or {}
    before = gate.get("before_status")
    after = gate.get("after_status")
    rank = {"blocked": 0, "insufficient": 1, "context_only": 2, "supporting_evidence": 3, "promotion_supporting": 4}
    return rank.get(str(after), 0) > rank.get(str(before), 0)

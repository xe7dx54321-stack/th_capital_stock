#!/usr/bin/env python3
"""Phase 22 valuation gate v2 diagnostics."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_demand_valuation_linkage import LINKAGE_RANK, build_demand_valuation_linkage
from smr_promotion_block_reason import build_ticker_block_diagnostics
from smr_valuation import latest_valuation_snapshot
from smr_valuation_gate import (
    _forward_eps,
    _historical_status,
    _peer_status,
    _price_freshness,
    diagnose_valuation_gate,
    normalize_ticker,
)


VALUATION_GATE_V2_STATUSES = {
    "promotion_supporting",
    "reduced_size_supporting",
    "supporting_evidence",
    "context_only",
    "insufficient",
    "blocked",
}

VALUATION_GATE_V2_BLOCKER_CODES = {
    "PRICE_STALE",
    "VALUATION_STALE",
    "PEER_COMPARISON_MISSING",
    "PEER_COMPARISON_WEAK",
    "HISTORICAL_VALUATION_MISSING",
    "HISTORICAL_VALUATION_WEAK",
    "FORWARD_EPS_MISSING",
    "FORWARD_EPS_PROXY_ONLY",
    "DEMAND_ASSUMPTION_UNSUPPORTED",
    "REVENUE_GROWTH_ASSUMPTION_UNSUPPORTED",
    "MARGIN_ASSUMPTION_UNSUPPORTED",
    "VALUATION_CONFLICTS_WITH_THESIS",
    "VALUATION_EVIDENCE_QUALITY_LOW",
    "VALUATION_CONFIDENCE_LOW",
    "VALUATION_SUPPORTING_ONLY",
}

STATUS_RANK = {
    "blocked": 0,
    "insufficient": 1,
    "context_only": 2,
    "supporting_evidence": 3,
    "reduced_size_supporting": 4,
    "promotion_supporting": 5,
}


def _forward_eps_status(forward: dict[str, Any]) -> str:
    if not forward or forward.get("status") == "missing":
        return "missing"
    if forward.get("is_official_consensus"):
        return "official"
    return "proxy_only"


def _demand_support_status(linkage: dict[str, Any]) -> str:
    status = str((linkage.get("demand_valuation_linkage") or {}).get("status") or "missing")
    if status == "strong_support":
        return "strong"
    if status == "medium_support":
        return "medium"
    if status == "weak_support":
        return "weak"
    return status


def _margin_support(snapshot: dict[str, Any]) -> str:
    fundamentals = snapshot.get("fundamentals_snapshot") or {}
    if fundamentals.get("gross_margin") is not None or fundamentals.get("operating_margin") is not None or fundamentals.get("net_margin") is not None:
        return "supporting"
    if fundamentals.get("revenue") is not None and (fundamentals.get("net_profit") is not None or fundamentals.get("operating_profit") is not None):
        return "partial"
    return "missing"


def _next_fix_for_blocker(code: str) -> str:
    return {
        "PRICE_STALE": "refresh latest daily price before valuation use",
        "VALUATION_STALE": "rebuild valuation snapshot",
        "PEER_COMPARISON_MISSING": "add auditable peer comparison evidence",
        "PEER_COMPARISON_WEAK": "repair weak peer comparison inputs",
        "HISTORICAL_VALUATION_MISSING": "add historical valuation sample",
        "HISTORICAL_VALUATION_WEAK": "repair weak historical valuation sample",
        "FORWARD_EPS_MISSING": "add forward EPS proxy evidence",
        "FORWARD_EPS_PROXY_ONLY": "add official consensus or stronger independent proxy evidence",
        "DEMAND_ASSUMPTION_UNSUPPORTED": "add confirmed demand/order/customer evidence",
        "REVENUE_GROWTH_ASSUMPTION_UNSUPPORTED": "link demand evidence to revenue growth assumption",
        "MARGIN_ASSUMPTION_UNSUPPORTED": "add margin assumption evidence",
        "VALUATION_CONFLICTS_WITH_THESIS": "resolve demand/valuation thesis conflict",
        "VALUATION_EVIDENCE_QUALITY_LOW": "replace low quality valuation evidence",
        "VALUATION_CONFIDENCE_LOW": "increase valuation confidence with primary evidence",
        "VALUATION_SUPPORTING_ONLY": "add stronger valuation evidence before full-size promotion",
    }.get(code, "inspect valuation blocker")


def _status_for_components(
    *,
    base_status: str,
    price: str,
    peer: str,
    historical: str,
    forward_status: str,
    linkage_status: str,
    evidence_quality: str,
    valuation_confidence: float,
    blockers: list[str],
) -> str:
    if price == "stale" or "PRICE_STALE" in blockers or "VALUATION_STALE" in blockers:
        return "blocked"
    if base_status == "blocked":
        return "blocked"
    if base_status == "context_only" and LINKAGE_RANK.get(linkage_status, 0) < LINKAGE_RANK["medium_support"]:
        return "context_only"
    if base_status == "insufficient" and not any(item in blockers for item in ("PEER_COMPARISON_MISSING", "HISTORICAL_VALUATION_MISSING")):
        return "supporting_evidence" if LINKAGE_RANK.get(linkage_status, 0) >= LINKAGE_RANK["medium_support"] else "insufficient"
    ready_for_reduced = (
        base_status in {"supporting_evidence", "promotion_supporting"}
        and price == "fresh"
        and peer in {"supporting", "partial"}
        and historical in {"supporting", "partial"}
        and forward_status in {"proxy_only", "official"}
        and LINKAGE_RANK.get(linkage_status, 0) >= LINKAGE_RANK["medium_support"]
        and evidence_quality in {"medium", "high", "missing"}
        and valuation_confidence >= 0.45
    )
    if ready_for_reduced:
        if forward_status == "official" and LINKAGE_RANK.get(linkage_status, 0) >= LINKAGE_RANK["strong_support"]:
            return "promotion_supporting"
        return "reduced_size_supporting"
    if base_status in {"supporting_evidence", "promotion_supporting"}:
        return "supporting_evidence"
    return base_status if base_status in VALUATION_GATE_V2_STATUSES else "insufficient"


def diagnose_valuation_gate_v2(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    watchlist_id: str = "ai_core",
    phase19_diag: dict[str, Any] | None = None,
    demand_linkage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    phase19_diag = phase19_diag if phase19_diag is not None else build_ticker_block_diagnostics(conn, ticker, watchlist_id=watchlist_id)
    base_payload = diagnose_valuation_gate(conn, ticker, phase19_diag=phase19_diag)
    base_gate = base_payload.get("valuation_gate") or {}
    snapshot = latest_valuation_snapshot(conn, ticker) or {}
    demand_linkage = demand_linkage or build_demand_valuation_linkage(
        conn,
        ticker,
        thesis_type=phase19_diag.get("primary_thesis_type") or "ai_infrastructure_demand",
        persist=True,
    )
    linkage = demand_linkage.get("demand_valuation_linkage") or {}
    linkage_status = str(linkage.get("status") or "missing")
    forward = _forward_eps(snapshot)
    forward_status = _forward_eps_status(forward)
    price = _price_freshness(snapshot)
    peer = _peer_status(snapshot)
    historical = _historical_status(snapshot)
    margin_support = _margin_support(snapshot)
    valuation_confidence = float(snapshot.get("valuation_confidence") or 0.0)
    evidence_quality = str((base_gate.get("valuation_components") or {}).get("evidence_quality") or "missing")
    blockers = list(base_gate.get("remaining_valuation_blockers") or [])
    if linkage_status in {"missing", "context_only", "weak_support"}:
        blockers.append("DEMAND_ASSUMPTION_UNSUPPORTED")
        blockers.append("REVENUE_GROWTH_ASSUMPTION_UNSUPPORTED")
    if linkage_status == "conflicted":
        blockers.append("VALUATION_CONFLICTS_WITH_THESIS")
    if margin_support == "missing":
        blockers.append("MARGIN_ASSUMPTION_UNSUPPORTED")
    if forward_status == "proxy_only" and "FORWARD_EPS_PROXY_ONLY" not in blockers:
        blockers.append("FORWARD_EPS_PROXY_ONLY")
    before_status = str(base_gate.get("after_status") or "insufficient")
    after_status = _status_for_components(
        base_status=before_status,
        price=price,
        peer=peer,
        historical=historical,
        forward_status=forward_status,
        linkage_status=linkage_status,
        evidence_quality=evidence_quality,
        valuation_confidence=valuation_confidence,
        blockers=blockers,
    )
    if after_status in {"supporting_evidence", "reduced_size_supporting"}:
        blockers.append("VALUATION_SUPPORTING_ONLY")
    blockers = [code for code in dict.fromkeys(blockers) if code in VALUATION_GATE_V2_BLOCKER_CODES]
    components = {
        "price_freshness": price,
        "peer_comparison": peer,
        "historical_valuation": historical,
        "forward_eps": forward_status,
        "demand_assumption_support": _demand_support_status(demand_linkage),
        "revenue_growth_support": _demand_support_status(demand_linkage),
        "margin_assumption_support": margin_support,
        "demand_to_valuation_linkage": linkage_status,
        "evidence_quality": evidence_quality,
        "valuation_confidence": round(valuation_confidence, 3),
    }
    return {
        "ticker": ticker,
        "valuation_gate_v2": {
            "before_status": before_status,
            "after_status": after_status,
            "blocks_pending": after_status in {"blocked", "insufficient", "context_only"},
            "allows_reduced_size_pending": after_status in {"supporting_evidence", "reduced_size_supporting"},
            "valuation_components": components,
            "remaining_blockers": blockers,
            "next_fix": list(dict.fromkeys(_next_fix_for_blocker(code) for code in blockers)) or ["keep monitoring valuation support"],
            "proxy_eps_not_official_consensus": forward_status == "proxy_only",
            "demand_valuation_linkage": linkage,
            "promotion_metadata": {
                "phase": 22,
                "valuation_gate_status": after_status,
                "allows_reduced_size_pending": after_status in {"supporting_evidence", "reduced_size_supporting"},
                "proxy_eps_is_official_consensus": bool(forward.get("is_official_consensus")),
                "demand_replaces_valuation_model": False,
                "promotion_rules_relaxed": False,
            },
        },
    }


def valuation_gate_v2_improved(payload: dict[str, Any]) -> bool:
    gate = payload.get("valuation_gate_v2") or {}
    return STATUS_RANK.get(str(gate.get("after_status") or "blocked"), 0) > STATUS_RANK.get(str(gate.get("before_status") or "blocked"), 0)

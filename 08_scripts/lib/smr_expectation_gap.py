#!/usr/bin/env python3
"""Phase 25 expectation-gap scoring."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_end_demand_proxy import build_end_demand_proxy
from smr_revenue_sensitivity_model import build_revenue_sensitivity
from smr_supplier_exposure_model import get_supplier_exposure_profile, normalize_ticker
from smr_supply_chain_variable_evidence import build_variable_evidence_packs


def _end_demand_points(proxy: dict[str, Any]) -> int:
    data = proxy.get("end_demand_proxy") or {}
    if data.get("overall_direction") == "conflicted":
        return 4
    if data.get("overall_direction") == "negative":
        return 0
    confidence = str(data.get("overall_confidence") or "low")
    return {"low": 10, "low_to_medium": 14, "medium": 18, "high": 22}.get(confidence, 10)


def _supplier_points(profile: dict[str, Any]) -> int:
    if profile.get("status") == "missing":
        return 0
    role_text = " ".join(profile.get("supply_chain_role") or []) + " " + " ".join(profile.get("product_exposure") or [])
    role_text = role_text.lower()
    if any(token in role_text for token in ("optical", "transceiver", "packaging", "optical component", "optical module")):
        return 15
    if profile.get("theme") == "ai_optical_interconnect":
        return 12
    return 5


def _sensitivity_points(sensitivity: dict[str, Any]) -> int:
    data = sensitivity.get("revenue_sensitivity") or {}
    missing = data.get("missing_variables") or []
    if len(missing) >= 4:
        return 5
    if len(missing) >= 2:
        return 8
    return 12


def _valuation_points(sensitivity: dict[str, Any]) -> int:
    return 7 if (sensitivity.get("revenue_sensitivity") or {}).get("valuation_support") == "supporting" else 3


def _evidence_quality_points(proxy: dict[str, Any]) -> int:
    count = int((proxy.get("end_demand_proxy") or {}).get("active_evidence_count") or 0)
    if count >= 6:
        return 14
    if count >= 2:
        return 10
    if count >= 1:
        return 8
    return 4


def _variable_status(variable_evidence: dict[str, Any], key: str) -> str:
    return str((variable_evidence.get(key) or {}).get("evidence_status") or "missing")


def _variable_evidence_uncertainty_offset(variable_evidence: dict[str, Any]) -> int:
    if not variable_evidence:
        return 0
    offset = 0
    for key in ("supplier_share", "capacity"):
        if _variable_status(variable_evidence, key) in {"partial", "proxy_supported", "confirmed"}:
            offset += 1
    return max(-4, min(3, offset))


def _uncertainty_penalty(
    profile: dict[str, Any],
    sensitivity: dict[str, Any],
    official_consensus_available: bool,
    variable_evidence: dict[str, Any] | None = None,
) -> int:
    missing = len((sensitivity.get("revenue_sensitivity") or {}).get("missing_variables") or [])
    penalty = -min(14, missing * 2)
    if profile.get("customer_exposure_status") != "confirmed":
        penalty -= 2
    if not official_consensus_available:
        penalty -= 2
    penalty += _variable_evidence_uncertainty_offset(variable_evidence or {})
    return penalty


def _confidence(score: int, sensitivity: dict[str, Any], official_consensus_available: bool) -> str:
    missing = len((sensitivity.get("revenue_sensitivity") or {}).get("missing_variables") or [])
    if not official_consensus_available or missing >= 3:
        return "low_to_medium" if score >= 55 else "low"
    if score >= 70:
        return "medium"
    return "low_to_medium"


def _status(score: int, confidence: str, profile: dict[str, Any], sensitivity: dict[str, Any]) -> str:
    missing = (sensitivity.get("revenue_sensitivity") or {}).get("missing_variables") or []
    if profile.get("status") == "missing":
        return "insufficient_data"
    if score < 35:
        return "insufficient_data" if missing else "neutral"
    if score >= 75 and confidence in {"medium", "high"} and not missing:
        return "strong_positive_gap"
    if score >= 45:
        return "potential_positive_gap"
    return "neutral"


def build_expectation_gap(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    theme: str | None = None,
    end_demand_proxy: dict[str, Any] | None = None,
    revenue_sensitivity: dict[str, Any] | None = None,
    variable_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    profile = get_supplier_exposure_profile(ticker)
    theme = theme or profile.get("theme") or "ai_optical_interconnect"
    end_proxy = end_demand_proxy or build_end_demand_proxy(conn, "ai_optical_interconnect")
    sensitivity = revenue_sensitivity or build_revenue_sensitivity(conn, ticker, theme=theme, end_demand_proxy=end_proxy)
    variable_evidence = variable_evidence if variable_evidence is not None else build_variable_evidence_packs(conn, ticker)
    official_consensus_available = bool((variable_evidence.get("consensus") or {}).get("official_consensus_available"))
    drivers = {
        "end_demand_strength": _end_demand_points(end_proxy),
        "supplier_exposure_strength": _supplier_points(profile),
        "revenue_sensitivity_confidence": _sensitivity_points(sensitivity),
        "valuation_expectation_support": _valuation_points(sensitivity),
        "proxy_consensus_gap": 4 if not official_consensus_available else 10,
        "evidence_quality": _evidence_quality_points(end_proxy),
        "uncertainty_penalty": _uncertainty_penalty(profile, sensitivity, official_consensus_available, variable_evidence),
    }
    score = max(0, min(100, sum(drivers.values())))
    confidence = _confidence(score, sensitivity, official_consensus_available)
    status = _status(score, confidence, profile, sensitivity)
    key_positive = []
    if drivers["end_demand_strength"] >= 14:
        key_positive.append("AI optical demand proxy positive")
    if drivers["supplier_exposure_strength"] >= 12:
        key_positive.append("company has relevant optical supply-chain exposure")
    uncertainties = list((profile.get("key_unknowns") or []) + (sensitivity.get("revenue_sensitivity") or {}).get("missing_variables", []))
    if not official_consensus_available:
        uncertainties.append("official consensus unavailable")
    variable_summary = {
        key: (pack.get("evidence_status") if isinstance(pack, dict) else "missing")
        for key, pack in (variable_evidence or {}).items()
    }
    return {
        "ticker": ticker,
        "company_name": profile.get("company_name"),
        "theme": theme,
        "expectation_gap": {
            "status": status,
            "score": score,
            "confidence": confidence,
            "direction": "positive" if status in {"strong_positive_gap", "potential_positive_gap"} else "neutral",
            "drivers": drivers,
            "key_positive_factors": list(dict.fromkeys(key_positive)),
            "key_uncertainties": list(dict.fromkeys(str(item) for item in uncertainties if item))[:10],
            "variable_evidence_summary": variable_summary,
            "allowed_usage": "research_candidate_only",
            "promotion_allowed": False,
            "safety": {
                "official_consensus_available": official_consensus_available,
                "expectation_gap_auto_pending": False,
                "proxy_estimate_treated_as_confirmed": False,
            },
        },
    }

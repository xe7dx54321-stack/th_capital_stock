#!/usr/bin/env python3
"""Phase 20 bear-case mitigation evidence mapping.

This module is intentionally diagnostic. It maps existing, linked evidence to
bear-case risk categories without deleting bear cases or weakening promotion
rules.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_bear_case_response import decompose_bear_case_residual_risk
from smr_evidence_quality import evidence_quality_summary
from smr_fundamentals import latest_fundamentals_snapshot
from smr_promotion_block_reason import build_ticker_block_diagnostics

try:
    from smr_direct_demand_evidence import extract_direct_demand_evidence
except ImportError:  # pragma: no cover - keeps older phase modules importable
    extract_direct_demand_evidence = None


RISK_CATEGORIES = {
    "valuation_risk",
    "growth_risk",
    "margin_risk",
    "cash_flow_risk",
    "data_quality_risk",
    "competitive_risk",
    "policy_risk",
    "supply_chain_risk",
    "customer_concentration_risk",
    "portfolio_concentration_risk",
    "thesis_confidence_risk",
    "unknown_risk",
}

MITIGATION_STATUSES = {
    "mitigated",
    "partially_mitigated",
    "unresolved_but_non_core",
    "unresolved_core",
    "requires_more_evidence",
    "not_applicable",
}

FINANCIAL_RISK_FIELDS = {
    "growth_risk": ("revenue", "revenue_growth"),
    "margin_risk": ("gross_profit", "gross_margin", "operating_margin"),
    "cash_flow_risk": ("operating_cash_flow", "free_cash_flow", "capex"),
    "data_quality_risk": (
        "revenue",
        "gross_profit",
        "shareholders_equity",
        "net_income",
        "eps_basic",
        "gross_margin",
    ),
    "valuation_risk": ("eps_basic", "net_income", "shareholders_equity", "revenue"),
}

DIRECT_THESIS_EVIDENCE_REQUIRED = {
    "growth_risk": ["AI order evidence", "customer demand evidence"],
    "competitive_risk": ["AI order evidence", "customer demand evidence", "competitive position evidence"],
    "policy_risk": ["policy impact evidence"],
    "supply_chain_risk": ["supplier or capacity evidence"],
    "customer_concentration_risk": ["customer concentration evidence"],
    "thesis_confidence_risk": ["claim graph support", "filing or news support"],
}

DIRECT_DEMAND_RISK_CATEGORIES = {
    "growth_risk",
    "competitive_risk",
    "customer_concentration_risk",
    "supply_chain_risk",
    "thesis_confidence_risk",
}

DEMAND_STRENGTH_RANK = {
    "blocked": 0,
    "context_only": 1,
    "weak_indication": 2,
    "medium_indication": 3,
    "strong_indication": 4,
    "confirmed_order": 5,
}


def normalize_ticker(ticker: str | None) -> str:
    return str(ticker or "").strip().upper()


def _quality_rank(level: str | None) -> int:
    return {"blocked": 0, "missing": 0, "low": 1, "medium": 2, "high": 3}.get(str(level or "missing"), 0)


def _risk_category(text: str | None, fallback: str | None = None) -> str:
    raw = f"{fallback or ''} {text or ''}".lower()
    explicit = str(fallback or "").lower()
    if explicit in RISK_CATEGORIES and explicit != "unknown_risk":
        return explicit
    if any(token in raw for token in ("valuation", "multiple", "price", "rerating", "eps")):
        return "valuation_risk"
    if any(token in raw for token in ("growth", "revenue", "demand", "order", "guidance")):
        return "growth_risk"
    if any(token in raw for token in ("margin", "gross profit", "cost")):
        return "margin_risk"
    if any(token in raw for token in ("cash flow", "free cash flow", "fcf", "capex")):
        return "cash_flow_risk"
    if any(token in raw for token in ("data", "evidence", "fundamental", "field")):
        return "data_quality_risk"
    if any(token in raw for token in ("competition", "competitive", "share")):
        return "competitive_risk"
    if "policy" in raw or "regulat" in raw:
        return "policy_risk"
    if "supply" in raw or "supplier" in raw:
        return "supply_chain_risk"
    if "customer concentration" in raw or "customer" in raw:
        return "customer_concentration_risk"
    if "portfolio" in raw or "position" in raw:
        return "portfolio_concentration_risk"
    if "thesis" in raw or "unknown" in raw:
        return "thesis_confidence_risk"
    return "unknown_risk"


def _field_evidence(snapshot: dict[str, Any], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    details = snapshot.get("field_details") or {}
    for field in fields:
        detail = details.get(field) or {}
        evidence_ids = []
        if detail.get("source_evidence_id"):
            evidence_ids.append(str(detail["source_evidence_id"]))
        evidence_ids.extend(str(item) for item in detail.get("source_evidence_ids") or [] if item)
        evidence_ids = list(dict.fromkeys(evidence_ids))
        if not evidence_ids:
            continue
        usage = str(detail.get("allowed_usage") or "")
        if usage not in {"supporting_evidence", "promotion_evidence"}:
            continue
        results.append(
            {
                "field": field,
                "evidence_ids": evidence_ids,
                "allowed_usage": usage,
                "confidence": detail.get("confidence"),
                "chunk_section_type": detail.get("chunk_section_type") or detail.get("source_section_type"),
            }
        )
    return results


def _evidence_quality_for_ids(conn: sqlite3.Connection, evidence_ids: list[str]) -> str:
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


def _default_claims(diag: dict[str, Any]) -> list[dict[str, Any]]:
    ticker = diag.get("ticker")
    thesis = str(diag.get("primary_thesis_type") or "unknown")
    claims: list[dict[str, Any]] = []
    if thesis == "valuation_rerating":
        claims.append(
            {
                "bear_case_claim_id": f"bear_{ticker}_valuation_risk",
                "bear_case_text": "Valuation rerating may not be supported by enough peer, historical, or EPS evidence.",
                "risk_category": "valuation_risk",
                "core_to_thesis": True,
            }
        )
    elif thesis == "ai_infrastructure_demand":
        claims.append(
            {
                "bear_case_claim_id": f"bear_{ticker}_growth_translation",
                "bear_case_text": "AI demand may not translate into company revenue growth or margin improvement.",
                "risk_category": "growth_risk",
                "core_to_thesis": True,
            }
        )
        claims.append(
            {
                "bear_case_claim_id": f"bear_{ticker}_direct_demand_missing",
                "bear_case_text": "Direct AI order or customer demand evidence is still missing.",
                "risk_category": "competitive_risk",
                "core_to_thesis": True,
            }
        )
    else:
        claims.append(
            {
                "bear_case_claim_id": f"bear_{ticker}_thesis_confidence",
                "bear_case_text": "Thesis evidence is not strong enough to support promotion.",
                "risk_category": "thesis_confidence_risk",
                "core_to_thesis": True,
            }
        )
    if diag.get("recovered_fields"):
        claims.append(
            {
                "bear_case_claim_id": f"bear_{ticker}_data_quality",
                "bear_case_text": "Recovered fundamentals reduce data-quality risk but do not answer the full thesis.",
                "risk_category": "data_quality_risk",
                "core_to_thesis": False,
            }
        )
    return claims


def _input_claims(diag: dict[str, Any]) -> list[dict[str, Any]]:
    gate = diag.get("bear_case_gate") or {}
    if str(gate.get("overall_status") or "").lower() == "mitigated":
        return [
            {
                "bear_case_claim_id": f"bear_{diag.get('ticker')}_already_mitigated",
                "bear_case_text": "existing bear-case gate is already mitigated",
                "risk_category": "unknown_risk",
                "core_to_thesis": False,
                "before_status": "mitigated",
            }
        ]
    residual = decompose_bear_case_residual_risk(normalize_ticker(diag.get("ticker")), gate)
    responses = (residual.get("bear_case_residual_risk") or {}).get("responses") or []
    if responses and not (
        len(responses) == 1
        and str(responses[0].get("bear_case_claim_id") or "").endswith("_latest")
        and responses[0].get("risk_category") == "unknown_risk"
    ):
        return responses
    return _default_claims(diag)


def _missing_for_category(category: str) -> list[str]:
    return list(DIRECT_THESIS_EVIDENCE_REQUIRED.get(category) or ["direct bear-case mitigation evidence"])


def _direct_demand_candidates(category: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if category not in DIRECT_DEMAND_RISK_CATEGORIES:
        return []
    candidates = [
        item
        for item in items or []
        if item.get("usable_for_bear_case_mitigation")
        and item.get("evidence_id")
        and item.get("claim_relevance") in {"core", "supporting"}
        and item.get("demand_strength") in {"medium_indication", "strong_indication", "confirmed_order"}
    ]
    candidates.sort(
        key=lambda item: (
            DEMAND_STRENGTH_RANK.get(str(item.get("demand_strength")), 0),
            _quality_rank(str(item.get("source_quality") or "missing")),
            bool(item.get("claim_relevance") == "core"),
        ),
        reverse=True,
    )
    return candidates


def _demand_quality(items: list[dict[str, Any]]) -> str:
    if not items:
        return "missing"
    ranks = [_quality_rank(str(item.get("source_quality") or "missing")) for item in items]
    best = max(ranks) if ranks else 0
    if best >= 3:
        return "high"
    if best >= 2:
        return "medium"
    if best >= 1:
        return "low"
    return "blocked"


def _remaining_demand_evidence(category: str, items: list[dict[str, Any]]) -> list[str]:
    missing = []
    if not any(item.get("demand_strength") == "confirmed_order" for item in items):
        missing.append("confirmed signed order or tender/procurement award")
    if len({item.get("independent_source_key") for item in items if item.get("independent_source_key")}) < 2:
        missing.append("second independent demand evidence source")
    for item in _missing_for_category(category):
        if "AI order" in item or "customer demand" in item:
            continue
        missing.append(item)
    return list(dict.fromkeys(missing))


def map_bear_case_to_evidence(
    conn: sqlite3.Connection,
    *,
    ticker: str,
    primary_thesis_type: str,
    claims: list[dict[str, Any]],
    fundamentals_snapshot: dict[str, Any],
    direct_demand_evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Map bear-case claims to existing evidence without weakening blockers."""

    rows = []
    for index, claim in enumerate(claims, start=1):
        category = _risk_category(claim.get("bear_case_text"), claim.get("risk_category"))
        fields = FINANCIAL_RISK_FIELDS.get(category, ())
        evidence_rows = _field_evidence(fundamentals_snapshot, fields)
        evidence_ids = list(dict.fromkeys(eid for item in evidence_rows for eid in item.get("evidence_ids") or []))
        quality = _evidence_quality_for_ids(conn, evidence_ids)
        demand_candidates = _direct_demand_candidates(category, direct_demand_evidence or [])
        core_to_thesis = bool(claim.get("core_to_thesis"))
        before_status = str(claim.get("response_status") or claim.get("before_status") or ("unresolved_core" if core_to_thesis else "unresolved_but_non_core"))
        if before_status == "mitigated":
            after_status = "mitigated"
            residual = "low"
            summary = "existing bear-case gate is already mitigated; Phase 20 does not add a stricter synthetic blocker"
            missing = []
            action = "keep_status"
            evidence_ids = []
            quality = "missing"
            evidence_rows = []
        elif demand_candidates:
            evidence_ids = list(dict.fromkeys(str(item.get("evidence_id")) for item in demand_candidates if item.get("evidence_id")))
            quality = _demand_quality(demand_candidates)
            evidence_rows = []
            best_strength = str(demand_candidates[0].get("demand_strength") or "")
            confirmed = best_strength == "confirmed_order"
            after_status = "mitigated" if confirmed and not any(item.get("is_management_commentary") for item in demand_candidates[:1]) else "partially_mitigated"
            residual = "low" if after_status == "mitigated" and not core_to_thesis else "medium"
            summary = "direct demand evidence mitigates the order/customer demand bear case, but promotion remains subject to proxy, valuation, and review gates"
            missing = [] if after_status == "mitigated" else _remaining_demand_evidence(category, demand_candidates)
            action = "reduce_position_size" if core_to_thesis else "supporting_warning"
        elif category in {"competitive_risk", "policy_risk", "supply_chain_risk", "customer_concentration_risk", "thesis_confidence_risk"}:
            after_status = "requires_more_evidence" if core_to_thesis else "unresolved_but_non_core"
            residual = "high" if core_to_thesis else "medium"
            summary = "financial statement evidence does not directly mitigate this bear-case category"
            missing = _missing_for_category(category)
            action = "block_pending_review" if core_to_thesis else "supporting_warning"
        elif _quality_rank(quality) >= 2 and evidence_ids:
            if category in {"growth_risk", "margin_risk"}:
                after_status = "partially_mitigated"
                residual = "medium"
                summary = "linked financial statement evidence mitigates revenue or margin risk, but direct demand evidence remains missing"
                missing = _missing_for_category(category)
                action = "reduce_position_size"
            elif category == "data_quality_risk":
                after_status = "partially_mitigated" if core_to_thesis else "mitigated"
                residual = "medium" if core_to_thesis else "low"
                summary = "recovered, field-linked fundamentals evidence reduces data-quality risk"
                missing = [] if not core_to_thesis else ["promotion-grade field evidence for every core claim"]
                action = "reduce_position_size" if core_to_thesis else "supporting_warning"
            elif category == "valuation_risk":
                after_status = "partially_mitigated"
                residual = "medium"
                summary = "fundamental evidence supports valuation context, but valuation gate remains separate"
                missing = ["peer or historical valuation evidence", "official consensus or stronger proxy evidence"]
                action = "reduce_position_size"
            else:
                after_status = "partially_mitigated"
                residual = "medium"
                summary = "linked evidence partially mitigates this risk, but direct evidence remains incomplete"
                missing = _missing_for_category(category)
                action = "reduce_position_size"
        elif evidence_ids:
            after_status = "requires_more_evidence" if core_to_thesis else "unresolved_but_non_core"
            residual = "high" if core_to_thesis else "medium"
            summary = "only low-quality or blocked evidence is available, so mitigation is not credited"
            missing = ["higher-quality field-linked evidence"]
            action = "block_pending_review" if core_to_thesis else "supporting_warning"
        else:
            after_status = "unresolved_core" if core_to_thesis else "unresolved_but_non_core"
            residual = "high" if core_to_thesis else "medium"
            summary = "no relevant evidence is linked to this bear-case category"
            missing = _missing_for_category(category)
            action = "block_pending_review" if core_to_thesis else "supporting_warning"

        rows.append(
            {
                "bear_case_claim_id": claim.get("bear_case_claim_id") or claim.get("claim_id") or f"bear_{normalize_ticker(ticker)}_{index}",
                "bear_case_text": claim.get("bear_case_text") or claim.get("claim_text") or "bear case claim",
                "risk_category": category,
                "core_to_thesis": core_to_thesis,
                "before_status": before_status,
                "after_status": after_status,
                "mitigating_evidence_ids": evidence_ids[:8],
                "mitigating_evidence_quality": quality,
                "mitigated_fields": [item["field"] for item in evidence_rows],
                "direct_demand_evidence_ids": [item.get("evidence_id") for item in demand_candidates[:8]],
                "direct_demand_strength": demand_candidates[0].get("demand_strength") if demand_candidates else None,
                "evidence_summary": summary,
                "missing_evidence": missing,
                "residual_risk_level": residual,
                "action_effect": action,
            }
        )

    blocking = any(
        item["core_to_thesis"] and item["after_status"] in {"unresolved_core", "requires_more_evidence"}
        for item in rows
    )
    residual_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    residual = max((item["residual_risk_level"] for item in rows), key=lambda item: residual_rank.get(item, 0), default="low")
    if not rows:
        overall = "not_applicable"
    elif blocking:
        overall = "requires_more_evidence"
    elif any(item["after_status"] == "partially_mitigated" for item in rows):
        overall = "partially_mitigated"
    elif all(item["after_status"] in {"mitigated", "not_applicable", "unresolved_but_non_core"} for item in rows):
        overall = "mitigated" if any(item["after_status"] == "mitigated" for item in rows) else "unresolved_but_non_core"
    else:
        overall = "requires_more_evidence"
    return {
        "ticker": normalize_ticker(ticker),
        "primary_thesis_type": primary_thesis_type,
        "bear_case_mitigation": {
            "overall_status": overall,
            "overall_residual_risk_level": residual,
            "blocks_pending": bool(blocking or residual in {"high", "critical"}),
            "allows_reduced_size_pending": bool((not blocking) and residual in {"low", "medium"} and any(item["after_status"] == "partially_mitigated" for item in rows)),
            "responses": rows,
            "promotion_metadata": {
                "phase": 20,
                "diagnostic_only": True,
                "promotion_rules_relaxed": False,
            },
        },
    }


def build_ticker_bear_case_mitigation(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    watchlist_id: str = "ai_core",
    include_direct_demand: bool = True,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    diag = build_ticker_block_diagnostics(conn, ticker, watchlist_id=watchlist_id)
    fundamentals = latest_fundamentals_snapshot(conn, ticker) or {}
    direct_demand = []
    if include_direct_demand and extract_direct_demand_evidence is not None:
        direct_demand = extract_direct_demand_evidence(
            conn,
            ticker,
            thesis_type=str(diag.get("primary_thesis_type") or "unknown"),
            limit=24,
            persist=True,
        )
    return map_bear_case_to_evidence(
        conn,
        ticker=ticker,
        primary_thesis_type=str(diag.get("primary_thesis_type") or "unknown"),
        claims=_input_claims(diag),
        fundamentals_snapshot=fundamentals,
        direct_demand_evidence=direct_demand,
    )


def bear_case_mitigation_improved(payload: dict[str, Any]) -> bool:
    for item in ((payload.get("bear_case_mitigation") or {}).get("responses") or []):
        before = str(item.get("before_status") or "")
        after = str(item.get("after_status") or "")
        if before in {"unresolved", "unresolved_core", "requires_more_evidence"} and after in {"partially_mitigated", "mitigated"}:
            return True
    return False

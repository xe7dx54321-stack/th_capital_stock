#!/usr/bin/env python3
"""Phase 22 demand-to-valuation assumption linkage.

Demand evidence can support revenue-growth assumptions, but it does not replace
valuation inputs and does not create promotion eligibility by itself.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_direct_demand_evidence import (
    STRENGTH_RANK,
    extract_direct_demand_evidence,
    normalize_ticker,
    summarize_demand_evidence,
)


LINKAGE_LEVELS = {
    "strong_support",
    "medium_support",
    "weak_support",
    "context_only",
    "conflicted",
    "missing",
}

QUALITY_RANK = {"blocked": 0, "low": 1, "medium": 2, "high": 3}
LINKAGE_RANK = {
    "missing": 0,
    "conflicted": 0,
    "context_only": 1,
    "weak_support": 2,
    "medium_support": 3,
    "strong_support": 4,
}

STRONG_LINKAGE_CATEGORIES = {
    "signed_contract",
    "tender_award",
    "procurement_award",
}

MEDIUM_LINKAGE_CATEGORIES = {
    "customer_order",
    "framework_contract",
    "customer_capex",
    "downstream_capex",
    "shipment",
    "backlog",
    "capacity_utilization",
    "management_guidance",
    "product_launch_demand",
    "industry_data",
    "policy_demand",
}


def _quality_usable(item: dict[str, Any]) -> bool:
    return QUALITY_RANK.get(str(item.get("source_quality") or "blocked"), 0) >= QUALITY_RANK["medium"]


def _item_linkage_level(item: dict[str, Any]) -> str:
    category = str(item.get("evidence_category") or "")
    strength = str(item.get("demand_strength") or "")
    if category == "rumor_or_unconfirmed" or strength == "blocked":
        return "missing"
    if not item.get("evidence_id"):
        return "missing"
    if category == "news_mention":
        return "weak_support"
    if strength == "confirmed_order" and category in STRONG_LINKAGE_CATEGORIES and _quality_usable(item):
        return "strong_support"
    if category in STRONG_LINKAGE_CATEGORIES and _quality_usable(item):
        return "strong_support"
    if category in MEDIUM_LINKAGE_CATEGORIES and strength in {"strong_indication", "medium_indication", "confirmed_order"}:
        return "medium_support" if _quality_usable(item) else "weak_support"
    if strength == "weak_indication":
        return "weak_support"
    return "context_only"


def _best_status(items: list[dict[str, Any]]) -> str:
    usable = [item for item in items if item.get("evidence_id") and item.get("demand_direction") in {"positive", "negative"}]
    directions = {item.get("demand_direction") for item in usable}
    if "positive" in directions and "negative" in directions:
        return "conflicted"
    if not usable:
        return "missing"
    best = "missing"
    for item in usable:
        level = _item_linkage_level(item)
        if item.get("is_management_commentary") and LINKAGE_RANK.get(level, 0) > LINKAGE_RANK["medium_support"]:
            level = "medium_support"
        if LINKAGE_RANK.get(level, 0) > LINKAGE_RANK.get(best, 0):
            best = level
    return best


def _supported_assumptions(status: str) -> list[str]:
    if status == "strong_support":
        return ["revenue_growth_assumption", "AI_demand_tailwind", "customer_specific_demand"]
    if status == "medium_support":
        return ["revenue_growth_assumption", "AI_demand_tailwind"]
    if status == "weak_support":
        return ["AI_demand_tailwind"]
    if status == "context_only":
        return ["valuation_context"]
    return []


def _unsupported_assumptions(status: str, items: list[dict[str, Any]]) -> list[str]:
    unsupported: list[str] = []
    if status != "strong_support":
        unsupported.append("confirmed_order_growth")
    if not any(str(item.get("evidence_category") or "") in {"customer_order", "signed_contract", "tender_award", "procurement_award"} for item in items):
        unsupported.append("customer_specific_demand")
    if not any(str(item.get("demand_strength") or "") == "confirmed_order" for item in items):
        unsupported.append("official_confirmed_order")
    return list(dict.fromkeys(unsupported))


def _valuation_effect(status: str) -> str:
    if status == "strong_support":
        return "support_reduced_size_valuation"
    if status == "medium_support":
        return "upgrade_context_to_supporting"
    if status == "weak_support":
        return "contextual_support_only"
    if status == "conflicted":
        return "blocker_conflicted"
    return "no_valuation_upgrade"


def build_demand_valuation_linkage(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    thesis_type: str | None = "ai_infrastructure_demand",
    demand_items: list[dict[str, Any]] | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    items = demand_items
    if items is None:
        items = extract_direct_demand_evidence(conn, ticker, thesis_type=thesis_type, limit=30, persist=persist)
    summary = summarize_demand_evidence(ticker, items)
    usable_items = [
        item
        for item in items
        if item.get("evidence_id")
        and item.get("demand_strength") not in {"blocked"}
        and item.get("demand_direction") in {"positive", "negative"}
    ]
    status = _best_status(usable_items)
    evidence_used = []
    for item in sorted(
        usable_items,
        key=lambda value: (
            LINKAGE_RANK.get(_item_linkage_level(value), 0),
            STRENGTH_RANK.get(str(value.get("demand_strength")), 0),
            QUALITY_RANK.get(str(value.get("source_quality") or "blocked"), 0),
        ),
        reverse=True,
    )[:10]:
        limitation = "; ".join(item.get("limitations") or []) or (
            "not confirmed order" if item.get("demand_strength") != "confirmed_order" else "confirmed or near-confirmed demand evidence"
        )
        evidence_used.append(
            {
                "evidence_id": item.get("evidence_id"),
                "evidence_category": item.get("evidence_category"),
                "demand_strength": item.get("demand_strength"),
                "source_quality": item.get("source_quality"),
                "limitation": limitation,
            }
        )
    limitations: list[str] = []
    if status in {"missing", "context_only"}:
        limitations.append("no usable direct demand evidence for valuation assumptions")
    if status == "conflicted":
        limitations.append("positive and negative demand evidence conflict")
    if not any(item.get("demand_strength") == "confirmed_order" for item in usable_items):
        limitations.append("no confirmed order")
    if not any(str(item.get("evidence_category") or "") in {"customer_order", "signed_contract", "tender_award", "procurement_award"} for item in usable_items):
        limitations.append("no customer-specific order evidence")
    if any(item.get("is_management_commentary") for item in usable_items):
        limitations.append("management commentary is supporting only")
    payload = {
        "ticker": ticker,
        "demand_valuation_linkage": {
            "status": status,
            "supported_assumptions": _supported_assumptions(status),
            "evidence_used": evidence_used,
            "unsupported_assumptions": _unsupported_assumptions(status, usable_items),
            "valuation_effect": _valuation_effect(status),
            "limitations": list(dict.fromkeys(limitations)),
            "demand_evidence_summary": summary,
            "evidence_ids": [item.get("evidence_id") for item in evidence_used if item.get("evidence_id")],
            "safety": {
                "demand_replaces_valuation_model": False,
                "promotion_rules_relaxed": False,
                "indication_treated_as_confirmed_order": False,
            },
        },
    }
    return payload


def demand_valuation_linkage_improved(payload: dict[str, Any]) -> bool:
    linkage = payload.get("demand_valuation_linkage") or {}
    return LINKAGE_RANK.get(str(linkage.get("status") or "missing"), 0) >= LINKAGE_RANK["medium_support"]

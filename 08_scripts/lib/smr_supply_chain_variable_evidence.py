#!/usr/bin/env python3
"""Phase 26 supply-chain variable evidence packs.

This module keeps Phase 26 conservative: it can surface proxy evidence and source
routes, but it never fabricates supplier share, ASP, customer allocation, or
official consensus.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_phase25_utils import unique_list
from smr_proxy_extraction import build_live_consensus_proxy
from smr_source_connector_registry import get_routes_for_information_type, infer_market_from_ticker
from smr_supplier_exposure_model import get_supplier_exposure_profile, normalize_ticker


VARIABLE_TYPES = {
    "supplier_share",
    "ASP_price_proxy",
    "capacity",
    "shipment",
    "customer_allocation_proxy",
    "customer_capex",
    "end_demand_forecast",
    "industry_forecast",
    "official_consensus",
    "internal_consensus_proxy",
    "company_IR",
    "margin_sensitivity",
    "revenue_growth_assumption",
    "unknown",
}
EVIDENCE_STATUSES = {"confirmed", "proxy_supported", "partial", "context_only", "planned_only", "missing", "conflicted", "blocked"}
CONFIDENCES = {"high", "medium", "low_to_medium", "low", "unknown"}
ALLOWED_USAGES = {"research_evidence", "valuation_support", "scenario_analysis_only", "context_only", "planned_only", "blocked"}

STATUS_CONFIDENCE_CAP = {
    "confirmed": "high",
    "proxy_supported": "medium",
    "partial": "low_to_medium",
    "context_only": "low",
    "planned_only": "unknown",
    "missing": "unknown",
    "conflicted": "low",
    "blocked": "unknown",
}
CONFIDENCE_RANK = {"unknown": 0, "low": 1, "low_to_medium": 2, "medium": 3, "high": 4}
VARIABLE_INFORMATION_TYPES = {
    "supplier_share": "supplier_share",
    "ASP_price_proxy": "component_price_forecast",
    "capacity": "capacity_utilization",
    "shipment": "shipment_forecast",
    "customer_allocation_proxy": "customer_allocation_proxy",
    "customer_capex": "customer_capex",
    "industry_forecast": "industry_forecast",
    "official_consensus": "official_consensus",
    "internal_consensus_proxy": "internal_consensus_proxy",
    "company_IR": "company_ir",
}


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone())


def _columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not _table_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def _loads(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = str(text or "").lower()
    return any(term.lower() in lower for term in terms)


def _confidence_cap(status: str, confidence: str) -> str:
    cap = STATUS_CONFIDENCE_CAP.get(status, "unknown")
    return confidence if CONFIDENCE_RANK.get(confidence, 0) <= CONFIDENCE_RANK.get(cap, 0) else cap


def route_for_variable(ticker: str, variable_type: str) -> dict[str, Any]:
    info_type = VARIABLE_INFORMATION_TYPES.get(variable_type, variable_type)
    market = infer_market_from_ticker(ticker)
    route = get_routes_for_information_type(info_type, market)
    if route.get("route_status") == "UNKNOWN_INFORMATION_ROUTE":
        route["preferred_sources"] = []
        route["fallback_sources"] = [
            {
                "source_name": "company IR / public evidence review",
                "connector_id": "company_ir",
                "status": "partial",
                "allowed_usage": "context_only",
            },
            {
                "source_name": "authorized industry or consensus source",
                "connector_id": f"{info_type}_provider",
                "status": "planned",
                "allowed_usage": "planned_only",
            },
        ]
        route["route_status"] = "partial"
        route["next_action"] = f"add first-class source route for {info_type}; use partial/context sources only until implemented"
    return route


def compact_source_routes(route: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for source in (route.get("preferred_sources") or []) + (route.get("fallback_sources") or []):
        rows.append(
            {
                "information_type": route.get("information_type"),
                "connector_id": source.get("connector_id"),
                "status": source.get("status"),
                "allowed_usage": source.get("allowed_usage"),
            }
        )
    return rows


def search_variable_evidence(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    keywords: tuple[str, ...],
    company_name: str | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    ticker = normalize_ticker(ticker)
    aliases = {ticker, ticker.replace(".SZ", ""), ticker.replace(".SH", ""), ticker.replace(".HK", "")}
    if company_name:
        aliases.add(company_name)
    rows: list[dict[str, Any]] = []
    if _table_exists(conn, "evidence_items"):
        cols = _columns(conn, "evidence_items")
        required = {"evidence_id", "source_key", "source_type", "source_quality", "published_at", "text_excerpt", "metadata_json"}
        if required.issubset(cols):
            order = "id DESC" if "id" in cols else "rowid DESC"
            for row in conn.execute(
                f"""
                SELECT evidence_id, source_key, source_type, source_quality, published_at, text_excerpt, metadata_json
                FROM evidence_items
                ORDER BY {order}
                LIMIT ?
                """,
                (max(limit * 80, 500),),
            ).fetchall():
                metadata = _loads(row[6])
                text = str(row[5] or "")
                haystack = f"{text} {json.dumps(metadata, ensure_ascii=False)}"
                if not _contains_any(haystack, tuple(alias for alias in aliases if alias)):
                    continue
                if not _contains_any(haystack, keywords):
                    continue
                rows.append(
                    {
                        "evidence_id": row[0],
                        "source_key": row[1],
                        "source_type": row[2],
                        "source_quality": row[3],
                        "published_at": row[4],
                        "text_excerpt": text[:500],
                        "metadata": metadata,
                    }
                )
                if len(rows) >= limit:
                    break
    if _table_exists(conn, "direct_demand_evidence_items") and len(rows) < limit:
        cols = _columns(conn, "direct_demand_evidence_items")
        required = {"evidence_id", "source_type", "source_quality", "evidence_excerpt", "metadata_json", "independent_source_key"}
        if required.issubset(cols):
            order = "updated_at DESC" if "updated_at" in cols else "rowid DESC"
            for row in conn.execute(
                f"""
                SELECT evidence_id, source_type, source_quality, evidence_excerpt, metadata_json, independent_source_key
                FROM direct_demand_evidence_items
                ORDER BY {order}
                LIMIT ?
                """,
                (max(limit * 50, 300),),
            ).fetchall():
                metadata = _loads(row[4])
                text = str(row[3] or "")
                haystack = f"{text} {json.dumps(metadata, ensure_ascii=False)}"
                if not _contains_any(haystack, tuple(alias for alias in aliases if alias)):
                    continue
                if not _contains_any(haystack, keywords):
                    continue
                rows.append(
                    {
                        "evidence_id": row[0],
                        "source_key": row[5],
                        "source_type": row[1],
                        "source_quality": row[2],
                        "published_at": metadata.get("published_at"),
                        "text_excerpt": text[:500],
                        "metadata": metadata,
                    }
                )
                if len(rows) >= limit:
                    break
    return rows[:limit]


def make_variable_evidence(
    *,
    ticker: str,
    theme: str,
    variable_type: str,
    evidence_status: str,
    confidence: str,
    allowed_usage: str,
    evidence_ids: list[str] | None = None,
    source_routes: list[dict[str, Any]] | None = None,
    assumption_range: dict[str, Any] | None = None,
    missing_reason: str | None = None,
    limitations: list[str] | None = None,
    next_connector_need: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if variable_type not in VARIABLE_TYPES:
        variable_type = "unknown"
    if evidence_status not in EVIDENCE_STATUSES:
        evidence_status = "blocked"
    if confidence not in CONFIDENCES:
        confidence = "unknown"
    confidence = _confidence_cap(evidence_status, confidence)
    if allowed_usage not in ALLOWED_USAGES:
        allowed_usage = "blocked"
    if evidence_status == "planned_only":
        allowed_usage = "planned_only"
    if evidence_status in {"missing", "blocked"} and allowed_usage not in {"scenario_analysis_only", "context_only", "blocked"}:
        allowed_usage = "context_only"
    payload = {
        "ticker": normalize_ticker(ticker),
        "theme": theme,
        "variable_type": variable_type,
        "evidence_status": evidence_status,
        "confidence": confidence,
        "allowed_usage": allowed_usage,
        "evidence_ids": list(dict.fromkeys(evidence_ids or [])),
        "source_routes": source_routes or [],
        "assumption_range": assumption_range or {"low": None, "base": None, "high": None},
        "missing_reason": missing_reason,
        "limitations": limitations or [],
        "next_connector_need": unique_list(next_connector_need or []),
        "active_for_scoring": evidence_status not in {"planned_only", "missing", "blocked"} and allowed_usage != "planned_only",
        "safety": {
            "supplier_share_fabricated": False,
            "ASP_fabricated": False,
            "customer_allocation_fabricated": False,
            "planned_source_used_as_active_evidence": False,
        },
    }
    if extra:
        payload.update(extra)
    return payload


def validate_variable_evidence(item: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    status = item.get("evidence_status")
    confidence = item.get("confidence")
    allowed_usage = item.get("allowed_usage")
    if item.get("variable_type") not in VARIABLE_TYPES:
        issues.append({"severity": "error", "path": "variable_type", "message": "invalid variable_type"})
    if status not in EVIDENCE_STATUSES:
        issues.append({"severity": "error", "path": "evidence_status", "message": "invalid evidence_status"})
    if confidence not in CONFIDENCES:
        issues.append({"severity": "error", "path": "confidence", "message": "invalid confidence"})
    if allowed_usage not in ALLOWED_USAGES:
        issues.append({"severity": "error", "path": "allowed_usage", "message": "invalid allowed_usage"})
    if status == "confirmed" and not item.get("evidence_ids"):
        issues.append({"severity": "error", "path": "evidence_ids", "message": "confirmed requires direct evidence"})
    if status == "proxy_supported" and not item.get("evidence_ids"):
        issues.append({"severity": "error", "path": "evidence_ids", "message": "proxy_supported requires evidence_id"})
    if status == "planned_only" and item.get("active_for_scoring"):
        issues.append({"severity": "error", "path": "active_for_scoring", "message": "planned_only cannot be active"})
    if status == "missing" and not item.get("missing_reason"):
        issues.append({"severity": "error", "path": "missing_reason", "message": "missing evidence needs missing_reason"})
    if CONFIDENCE_RANK.get(confidence, 0) > CONFIDENCE_RANK.get(STATUS_CONFIDENCE_CAP.get(status, "unknown"), 0):
        issues.append({"severity": "error", "path": "confidence", "message": "confidence exceeds evidence_status cap"})
    return issues


def build_supplier_share_pack(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    profile = get_supplier_exposure_profile(ticker)
    theme = profile.get("theme") or "ai_optical_interconnect"
    route = route_for_variable(ticker, "supplier_share")
    rows = search_variable_evidence(
        conn,
        ticker,
        company_name=profile.get("company_name"),
        keywords=("supplier share", "market share", "share", "allocation", "\u4efd\u989d", "\u4f9b\u5e94\u4efd\u989d", "\u5e02\u5360\u7387"),
    )
    evidence_ids = [row["evidence_id"] for row in rows]
    status = "partial" if profile.get("status") == "available" else "missing"
    confidence = "low"
    return make_variable_evidence(
        ticker=ticker,
        theme=theme,
        variable_type="supplier_share",
        evidence_status=status,
        confidence=confidence,
        allowed_usage="scenario_analysis_only",
        evidence_ids=evidence_ids,
        source_routes=compact_source_routes(route),
        assumption_range=profile.get("supplier_share_assumption_range") or {"low": None, "base": None, "high": None},
        missing_reason="exact supplier share not disclosed",
        limitations=["customer allocation not officially disclosed", "evidence supports exposure but not exact share"],
        next_connector_need=["company IR evidence", "industry forecast connector", "authorized industry/sell-side source"],
        extra={
            "company_name": profile.get("company_name"),
            "direct_share_disclosed": False,
            "customer_allocation_disclosed": False,
            "proxy_indicators": [
                {"indicator": "product_exposure", "status": "available" if profile.get("product_exposure") else "missing", "source": "supplier_exposure_profile"},
                {
                    "indicator": "AI optical interconnect exposure",
                    "status": "proxy_supported" if profile.get("theme") == "ai_optical_interconnect" or evidence_ids else "context_only",
                    "evidence_ids": evidence_ids,
                },
            ],
            "assumption_policy": {
                "allowed": True,
                "must_use_range": True,
                "default_range": None,
                "reason": "exact supplier share not disclosed",
            },
            "missing_variables": ["customer allocation", "supplier share", "product-level shipment share"],
        },
    )


def build_asp_price_proxy_pack(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    profile = get_supplier_exposure_profile(ticker)
    theme = profile.get("theme") or "ai_optical_interconnect"
    route = route_for_variable(ticker, "ASP_price_proxy")
    rows = search_variable_evidence(
        conn,
        ticker,
        company_name=profile.get("company_name"),
        keywords=("asp", "average selling price", "price", "pricing", "product mix", "800g", "1.6t", "\u4ef7\u683c", "\u5355\u4ef7", "\u4ea7\u54c1\u7ed3\u6784"),
    )
    evidence_ids = [row["evidence_id"] for row in rows]
    product_mix_proxy = bool(profile.get("product_exposure"))
    status = "context_only" if evidence_ids else "missing"
    confidence = "low" if evidence_ids else "unknown"
    return make_variable_evidence(
        ticker=ticker,
        theme=theme,
        variable_type="ASP_price_proxy",
        evidence_status=status,
        confidence=confidence,
        allowed_usage="scenario_analysis_only",
        evidence_ids=evidence_ids,
        source_routes=compact_source_routes(route),
        assumption_range=profile.get("ASP_assumption_range") or {"low": None, "base": None, "high": None},
        missing_reason="product ASP and product mix split not disclosed" if not evidence_ids else "direct ASP not disclosed; only context proxy available",
        limitations=["product upgrade trend is context, not ASP", "industry ASP proxy is inactive without source"],
        next_connector_need=["industry forecast/price connector", "company IR product mix evidence", "authorized sell-side source"],
        extra={
            "direct_ASP_disclosed": False,
            "industry_price_proxy_available": False,
            "product_mix_proxy_available": product_mix_proxy,
            "price_direction": "unknown",
            "missing_variables": ["product ASP", "800G/1.6T component price", "product mix split"],
        },
    )


def build_capacity_shipment_pack(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    profile = get_supplier_exposure_profile(ticker)
    theme = profile.get("theme") or "ai_optical_interconnect"
    route = route_for_variable(ticker, "capacity")
    capacity_rows = search_variable_evidence(
        conn,
        ticker,
        company_name=profile.get("company_name"),
        keywords=("capacity", "capex", "expansion", "production", "ramp", "\u4ea7\u80fd", "\u6269\u4ea7", "\u6295\u4ea7", "\u8d44\u672c\u5f00\u652f"),
    )
    shipment_rows = search_variable_evidence(
        conn,
        ticker,
        company_name=profile.get("company_name"),
        keywords=("shipment", "delivery", "units shipped", "\u51fa\u8d27", "\u4ea4\u4ed8", "\u53d1\u8d27"),
    )
    evidence_ids = unique_list([row["evidence_id"] for row in capacity_rows + shipment_rows])
    status = "partial" if capacity_rows else "missing"
    confidence = "low_to_medium" if capacity_rows else "unknown"
    return make_variable_evidence(
        ticker=ticker,
        theme=theme,
        variable_type="capacity",
        evidence_status=status,
        confidence=confidence,
        allowed_usage="scenario_analysis_only",
        evidence_ids=evidence_ids,
        source_routes=compact_source_routes(route),
        missing_reason=None if capacity_rows else "no capacity expansion evidence found in active local sources",
        limitations=["capex or capacity expansion is not shipment", "shipment is not customer allocation"],
        next_connector_need=["company IR evidence", "filing note parser", "industry shipment forecast connector"],
        extra={
            "capacity_expansion_evidence": [
                {"evidence_id": row["evidence_id"], "type": "capex_or_capacity_expansion", "confidence": "medium"} for row in capacity_rows[:6]
            ],
            "shipment_evidence": [
                {"evidence_id": row["evidence_id"], "type": "shipment", "confidence": "low_to_medium"} for row in shipment_rows[:6]
            ],
            "constraints": ["no product-level shipment disclosure", "no customer-specific allocation"],
        },
    )


def build_customer_allocation_proxy_pack(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    profile = get_supplier_exposure_profile(ticker)
    theme = profile.get("theme") or "ai_optical_interconnect"
    route = route_for_variable(ticker, "customer_allocation_proxy")
    rows = search_variable_evidence(
        conn,
        ticker,
        company_name=profile.get("company_name"),
        keywords=("nvidia", "hyperscaler", "customer allocation", "customer share", "\u82f1\u4f1f\u8fbe", "\u5ba2\u6237\u5206\u914d", "\u4e91\u5382\u5546"),
    )
    evidence_ids = [row["evidence_id"] for row in rows]
    confirmed = False
    return make_variable_evidence(
        ticker=ticker,
        theme=theme,
        variable_type="customer_allocation_proxy",
        evidence_status="missing" if not confirmed else "confirmed",
        confidence="unknown",
        allowed_usage="scenario_analysis_only",
        evidence_ids=[] if not confirmed else evidence_ids,
        source_routes=compact_source_routes(route),
        missing_reason="no official customer allocation disclosure",
        limitations=["no official customer allocation disclosure", "no direct NVIDIA/hyperscaler supply evidence"],
        next_connector_need=["company IR evidence", "authorized industry/sell-side source", "customer-side supply chain evidence"],
        extra={
            "confirmed_customer_allocation": confirmed,
            "proxy_customer_exposure": profile.get("customer_exposure_status") or "unknown",
            "candidate_proxy_evidence_ids": evidence_ids,
        },
    )


def build_consensus_expectation_proxy_pack(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    profile = get_supplier_exposure_profile(ticker)
    theme = profile.get("theme") or "ai_optical_interconnect"
    route = route_for_variable(ticker, "official_consensus")
    try:
        proxy = build_live_consensus_proxy(conn, ticker)
    except sqlite3.OperationalError:
        proxy = {
            "ticker": normalize_ticker(ticker),
            "is_official_consensus": False,
            "official_consensus_active": False,
            "proxy_quality": "invalid",
            "usable_for_promotion": False,
            "evidence_ids": [],
            "note": "internal consensus proxy unavailable for current local schema; not official sell-side consensus",
        }
    evidence_ids = list(proxy.get("evidence_ids") or [])
    quality = str(proxy.get("proxy_quality") or "invalid")
    internal_available = quality not in {"invalid", "missing"} or bool(evidence_ids)
    status = "proxy_supported" if evidence_ids else ("partial" if internal_available else "missing")
    confidence = {"strong": "medium", "medium": "low_to_medium", "weak": "low"}.get(quality, "unknown")
    return make_variable_evidence(
        ticker=ticker,
        theme=theme,
        variable_type="internal_consensus_proxy",
        evidence_status=status,
        confidence=confidence,
        allowed_usage="valuation_support" if evidence_ids else "scenario_analysis_only",
        evidence_ids=evidence_ids,
        source_routes=compact_source_routes(route),
        missing_reason=None if internal_available else "no internal expectation proxy evidence found",
        limitations=["not official sell-side consensus", "cannot be used as official EPS/revenue estimate"],
        next_connector_need=["commercial consensus provider", "authorized sell-side estimate source"],
        extra={
            "official_consensus_available": False,
            "official_consensus_status": "planned_only",
            "internal_proxy_available": internal_available,
            "internal_proxy_status": "supporting_evidence" if internal_available else "missing",
            "proxy_quality": quality,
            "proxy": proxy,
            "official_consensus_treated_as_internal": False,
        },
    )


def build_industry_forecast_routing(theme: str = "ai_optical_interconnect") -> dict[str, Any]:
    route_names = ["industry_forecast", "optical_module_forecast", "AI_capex_forecast", "component_price_forecast", "shipment_forecast"]
    planned_sources = []
    partial_sources = []
    active_sources = []
    for info_type in route_names:
        route = get_routes_for_information_type(info_type, "GLOBAL")
        for source in (route.get("preferred_sources") or []) + (route.get("fallback_sources") or []):
            row = {
                "information_type": info_type,
                "source_name": source.get("source_name"),
                "connector_id": source.get("connector_id"),
                "status": source.get("status"),
                "allowed_usage": source.get("allowed_usage"),
            }
            if source.get("status") == "planned" or source.get("allowed_usage") == "planned_only":
                planned_sources.append(row)
            elif source.get("status") == "partial":
                partial_sources.append(row)
            elif source.get("status") == "implemented":
                active_sources.append(row)
    return {
        "theme": theme,
        "industry_forecast_source_routing": {
            "active_sources": [],
            "planned_sources": unique_list(planned_sources),
            "partial_sources": unique_list(partial_sources + [
                {
                    "source_name": "news / public industry commentary",
                    "connector_id": "news_ingestion",
                    "status": "partial",
                    "allowed_usage": "context_only",
                }
            ]),
            "next_connector_need": [
                "authorized industry forecast source",
                "public company IR evidence",
                "industry news source with explicit forecast",
            ],
            "safety": {
                "planned_source_used_as_active_evidence": False,
                "commercial_source_marked_implemented": False,
            },
        },
    }


def build_variable_evidence_packs(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    return {
        "supplier_share": build_supplier_share_pack(conn, ticker),
        "ASP_price_proxy": build_asp_price_proxy_pack(conn, ticker),
        "capacity": build_capacity_shipment_pack(conn, ticker),
        "customer_allocation_proxy": build_customer_allocation_proxy_pack(conn, ticker),
        "consensus": build_consensus_expectation_proxy_pack(conn, ticker),
    }

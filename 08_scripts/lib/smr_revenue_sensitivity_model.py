#!/usr/bin/env python3
"""Phase 25 scenario-only revenue sensitivity model."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_end_demand_proxy import build_end_demand_proxy
from smr_supplier_exposure_model import get_supplier_exposure_profile, normalize_ticker


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone())


def _columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not _table_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def _latest_baseline_revenue(conn: sqlite3.Connection, ticker: str) -> tuple[Any, str]:
    if not _table_exists(conn, "fundamentals_snapshot"):
        return None, "fundamentals_snapshot_missing"
    cols = _columns(conn, "fundamentals_snapshot")
    revenue_col = next((col for col in ("revenue", "total_revenue", "operating_revenue") if col in cols), None)
    if not revenue_col:
        return None, "fundamentals_snapshot_or_missing"
    order_col = "period_end" if "period_end" in cols else ("as_of_date" if "as_of_date" in cols else "rowid")
    row = conn.execute(
        f"SELECT {revenue_col} FROM fundamentals_snapshot WHERE upper(ticker)=? ORDER BY {order_col} DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    return (row[0] if row else None), "fundamentals_snapshot"


def _missing_variables(profile: dict[str, Any], baseline_revenue: Any) -> list[str]:
    missing = []
    share = profile.get("supplier_share_assumption_range") or {}
    asp = profile.get("ASP_assumption_range") or {}
    if not all(share.get(key) is not None for key in ("low", "base", "high")):
        missing.append("supplier_share")
    if not all(asp.get(key) is not None for key in ("low", "base", "high")):
        missing.append("ASP")
    if profile.get("capacity_constraint") in {None, "", "unknown"}:
        missing.append("capacity_constraint")
    if baseline_revenue is None:
        missing.append("baseline_revenue")
    if profile.get("customer_exposure_status") != "confirmed":
        missing.append("customer_allocation")
    return list(dict.fromkeys(missing))


def build_revenue_sensitivity(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    theme: str | None = None,
    end_demand_proxy: dict[str, Any] | None = None,
    variable_evidence_packs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    profile = get_supplier_exposure_profile(ticker)
    theme = theme or profile.get("theme") or "ai_optical_interconnect"
    end_demand_proxy = end_demand_proxy or build_end_demand_proxy(conn, "ai_optical_interconnect")
    baseline_revenue, baseline_source = _latest_baseline_revenue(conn, ticker)
    missing = _missing_variables(profile, baseline_revenue)
    share = profile.get("supplier_share_assumption_range") or {}
    asp = profile.get("ASP_assumption_range") or {}
    scenarios = {}
    for scenario, confidence in (("low", "low"), ("base", "low_to_medium"), ("high", "low")):
        can_calculate = baseline_revenue is not None and share.get(scenario) is not None and asp.get(scenario) is not None
        scenarios[scenario] = {
            "supplier_share_assumption": scenario,
            "supplier_share_value": share.get(scenario),
            "ASP_assumption": scenario,
            "ASP_value": asp.get(scenario),
            "incremental_revenue_proxy": None if not can_calculate else None,
            "confidence": confidence if not can_calculate else "medium",
            "calculation_status": "not_calculated_missing_variables" if not can_calculate else "not_calculated_policy_guardrail",
        }
    allowed_for_valuation = bool(len(missing) <= 2 and (end_demand_proxy.get("end_demand_proxy") or {}).get("overall_direction") == "positive")
    return {
        "ticker": ticker,
        "company_name": profile.get("company_name"),
        "theme": theme,
        "revenue_sensitivity": {
            "status": "scenario_analysis",
            "baseline_revenue_source": baseline_source,
            "baseline_revenue": baseline_revenue,
            "scenario_cases": scenarios,
            "key_swing_factors": ["supplier share", "ASP", "capacity", "customer allocation"],
            "missing_variables": missing,
            "proxy_variables": {
                "product_exposure": profile.get("product_exposure") or [],
                "customer_exposure_status": profile.get("customer_exposure_status"),
                "end_demand_direction": (end_demand_proxy.get("end_demand_proxy") or {}).get("overall_direction"),
                "end_demand_confidence": (end_demand_proxy.get("end_demand_proxy") or {}).get("overall_confidence"),
            },
            "variable_evidence_status": {
                key: (pack.get("evidence_status") if isinstance(pack, dict) else "missing")
                for key, pack in (variable_evidence_packs or {}).items()
            },
            "next_connector_needs": next_connector_needs(missing),
            "valuation_support": "supporting" if allowed_for_valuation else "context_only",
            "limitations": [
                "exact customer allocation not disclosed",
                "ASP not disclosed",
                "supplier share not disclosed",
                "scenario-only estimate",
            ],
            "allowed_usage": "scenario_analysis_only",
            "safety": {
                "supplier_share_fabricated": False,
                "ASP_fabricated": False,
                "customer_allocation_fabricated": False,
            },
        },
    }


def next_connector_needs(missing_variables: list[str]) -> list[str]:
    needs = []
    if "supplier_share" in missing_variables or "ASP" in missing_variables:
        needs.append("industry forecast connector")
    if "customer_allocation" in missing_variables:
        needs.append("official/company IR evidence")
    if "baseline_revenue" in missing_variables:
        needs.append("fundamentals connector")
    needs.append("consensus source")
    return list(dict.fromkeys(needs))

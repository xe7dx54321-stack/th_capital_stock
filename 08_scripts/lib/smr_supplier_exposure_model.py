#!/usr/bin/env python3
"""Phase 25 supplier exposure profile helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smr_paths import project_path


PROFILE_PATH = project_path("00_control", "supplier_exposure_profiles.json")
PILOT_WATCHLIST_PATH = project_path("00_control", "watchlists", "supply_chain_pilot.json")
CUSTOMER_EXPOSURE_STATUSES = {"confirmed", "proxy_only", "not_directly_confirmed", "unknown"}


def normalize_ticker(ticker: str | None) -> str:
    return str(ticker or "").strip().upper()


def load_supplier_exposure_profiles(path: str | None = None) -> dict[str, Any]:
    profile_path = Path(path) if path else PROFILE_PATH
    return json.loads(profile_path.read_text(encoding="utf-8"))


def get_supplier_exposure_profile(ticker: str, *, profiles: dict[str, Any] | None = None) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    payload = profiles if profiles is not None else load_supplier_exposure_profiles()
    profile = (payload.get("profiles") or {}).get(ticker)
    if not profile:
        return {
            "ticker": ticker,
            "status": "missing",
            "missing_reason": "supplier exposure profile not configured",
            "allowed_usage": "blocked",
        }
    return {"ticker": ticker, "status": "available", **profile}


def validate_supplier_exposure_profile(profile: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if profile.get("status") == "missing":
        return [{"severity": "error", "path": "ticker", "message": profile.get("missing_reason")}]
    for field in ("company_name", "theme", "market", "supply_chain_role", "product_exposure", "customer_exposure_status", "allowed_usage"):
        if not profile.get(field):
            issues.append({"severity": "error", "path": field, "message": f"missing {field}"})
    if profile.get("customer_exposure_status") not in CUSTOMER_EXPOSURE_STATUSES:
        issues.append({"severity": "error", "path": "customer_exposure_status", "message": "invalid customer exposure status"})
    if profile.get("customer_exposure_status") == "confirmed":
        issues.append({"severity": "warning", "path": "customer_exposure_status", "message": "confirmed exposure requires explicit evidence ids"})
    if profile.get("allowed_usage") != "scenario_analysis_only":
        issues.append({"severity": "error", "path": "allowed_usage", "message": "supplier profile must be scenario_analysis_only"})
    for assumption_field in ("supplier_share_assumption_range", "ASP_assumption_range"):
        value = profile.get(assumption_field)
        if not isinstance(value, dict):
            issues.append({"severity": "error", "path": assumption_field, "message": "assumption must be an interval object"})
        elif not all(key in value for key in ("low", "base", "high")):
            issues.append({"severity": "error", "path": assumption_field, "message": "assumption interval needs low/base/high"})
    if not profile.get("assumption_required"):
        issues.append({"severity": "warning", "path": "assumption_required", "message": "Phase 25 profiles should explicitly require assumptions"})
    return issues


def load_supply_chain_pilot_watchlist(path: str | None = None) -> dict[str, Any]:
    watchlist_path = Path(path) if path else PILOT_WATCHLIST_PATH
    payload = json.loads(watchlist_path.read_text(encoding="utf-8"))
    payload["tickers"] = [normalize_ticker(ticker) for ticker in payload.get("tickers") or [] if normalize_ticker(ticker)]
    return payload

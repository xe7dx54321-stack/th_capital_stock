#!/usr/bin/env python3
"""Disclosure source fallback router for Phase 64."""

from __future__ import annotations

import json
from typing import Any

from smr_a_share_disclosure_endpoint_registry import get_fallback_order
from smr_cninfo_endpoint_diagnostics import run_cninfo_diagnostics


def _check_cninfo(ticker: str, skip_network: bool = False) -> dict[str, Any]:
    """Check CNINFO availability."""
    diag = run_cninfo_diagnostics(ticker, skip_network=skip_network)
    d = diag.get("cninfo_endpoint_diagnostics", {})
    ann_ok = d.get("https_connect_ok", False)
    ann_tests = d.get("his_announcement_query", {}).get("tests", [])
    has_results = any(
        t.get("status") == "ok"
        and t.get("response_json", {}).get("totalAnnouncement", 0) > 0
        for t in ann_tests
    )
    return {
        "reachable": ann_ok,
        "metadata_available": ann_ok,
        "text_available": False,  # CNINFO currently returns 0 results
        "has_results": has_results,
        "diagnostics": d,
    }


def _check_szse(ticker: str, skip_network: bool = False) -> dict[str, Any]:
    """Check SZSE availability."""
    if skip_network:
        return {"reachable": False, "metadata_available": False, "text_available": False, "reason": "skip_network"}

    from smr_szse_disclosure_connector import _check_szse_reachable, _try_disclosure_api

    reach = _check_szse_reachable()
    if not reach.get("szse_reachable", False):
        return {
            "reachable": False,
            "metadata_available": False,
            "text_available": False,
            "reason": reach.get("failure_reason", "szse_not_reachable"),
        }

    code = ticker.split(".")[0] if "." in ticker else ticker
    params = {"stock": [code], "pageNum": 1, "pageSize": 5}
    api_result = _try_disclosure_api("GET", params)
    api_ok = api_result.get("status") == "ok"

    return {
        "reachable": True,
        "metadata_available": api_ok,
        "text_available": False,
        "pdf_url_available": api_ok,
        "api_result": api_result,
        "reason": None if api_ok else api_result.get("failure_reason", "api_failed"),
    }


def _check_irm(ticker: str, skip_network: bool = False) -> dict[str, Any]:
    """Check IRM availability."""
    if skip_network:
        return {"reachable": False, "qa_available": False, "api_json_available": False, "html_parse_available": False, "reason": "skip_network"}

    from smr_irm_interactive_qa_connector import fetch_irm_qa

    result = fetch_irm_qa(ticker, max_sources=5, mode="execute", skip_network=False)
    inv = result.get("irm_qa_inventory", {})
    return {
        "reachable": inv.get("irm_reachable", False),
        "qa_available": inv.get("qa_items_usable", 0) > 0,
        "api_json_available": inv.get("api_json_available", False),
        "html_parse_available": inv.get("html_parse_available", False),
        "qa_count": inv.get("qa_items_usable", 0),
        "reason": inv.get("failure_reason"),
    }


def route_disclosure_source(
    ticker: str = "300308.SZ",
    skip_network: bool = False,
) -> dict[str, Any]:
    """Determine the best available disclosure source path."""
    result: dict[str, Any] = {
        "ticker": ticker,
        "disclosure_source_fallback_router": {
            "selected_primary_source": "none",
            "cninfo_status": "not_checked",
            "szse_status": "not_checked",
            "irm_status": "not_checked",
            "company_site_status": "not_configured",
            "real_metadata_available": False,
            "real_text_available": False,
            "fallback_used": False,
            "mock_used": False,
            "fixture_used": False,
            "routing_reason": [],
        },
    }

    r = result["disclosure_source_fallback_router"]

    # Check CNINFO
    cninfo = _check_cninfo(ticker, skip_network)
    if cninfo["reachable"] and cninfo["has_results"]:
        r["cninfo_status"] = "metadata_available_with_results"
        r["selected_primary_source"] = "cninfo"
        r["real_metadata_available"] = True
        r["routing_reason"].append("CNINFO reachable and returning results")
    elif cninfo["reachable"]:
        r["cninfo_status"] = "reachable_but_zero_results"
        r["routing_reason"].append("CNINFO reachable but returned 0 results - checking fallbacks")
    else:
        r["cninfo_status"] = "unreachable"
        r["routing_reason"].append("CNINFO unreachable in current network")

    # Check SZSE
    szse = _check_szse(ticker, skip_network)
    if szse["reachable"]:
        if szse["metadata_available"]:
            r["szse_status"] = "metadata_available"
            if r["selected_primary_source"] == "none":
                r["selected_primary_source"] = "szse_disclosure"
                r["fallback_used"] = True
            r["real_metadata_available"] = True
            r["routing_reason"].append("SZSE reachable and disclosure metadata available")
        else:
            r["szse_status"] = "reachable_but_api_failed"
            r["routing_reason"].append(f"SZSE reachable but API failed: {szse.get('reason', 'unknown')}")
    else:
        r["szse_status"] = "unreachable"
        r["routing_reason"].append(f"SZSE unreachable: {szse.get('reason', 'unknown')}")

    # Check IRM
    irm = _check_irm(ticker, skip_network)
    if irm["reachable"]:
        if irm["qa_available"]:
            r["irm_status"] = "qa_available"
            r["real_text_available"] = True
            r["routing_reason"].append(f"IRM reachable with {irm.get('qa_count', 0)} QA items")
            if irm["api_json_available"]:
                r["routing_reason"].append("IRM using JSON API")
            elif irm["html_parse_available"]:
                r["routing_reason"].append("IRM using HTML parsing fallback")
        else:
            r["irm_status"] = "reachable_but_no_qa"
            r["routing_reason"].append(f"IRM reachable but QA not extractable: {irm.get('reason', 'unknown')}")
    else:
        r["irm_status"] = "unreachable"
        r["routing_reason"].append(f"IRM unreachable: {irm.get('reason', 'unknown')}")

    # Determine final path
    if r["selected_primary_source"] == "none" and not r["real_text_available"]:
        r["selected_primary_source"] = "degraded_no_real_disclosure_source"
        r["status"] = "degraded"
        r["routing_reason"].append("No real disclosure source available")

    # If CNINFO/SZSE gave metadata but no text, IRM has text
    if r["real_metadata_available"] and r["real_text_available"] and r["selected_primary_source"] != "none":
        r["routing_reason"].append("Using SZSE/CNINFO for metadata, IRM for Q&A text supplement")
        if not r["selected_primary_source"]:
            r["selected_primary_source"] = "szse_metadata_plus_irm_qa"

    r["fallback_order"] = [s["source_id"] for s in get_fallback_order()]

    return result

#!/usr/bin/env python3
"""Small controlled source fetch for Phase 64."""

from __future__ import annotations

import json
import hashlib
from typing import Any

from smr_disclosure_source_fallback_router import route_disclosure_source, _check_cninfo, _check_szse, _check_irm


def run_small_controlled_source_fetch(
    ticker: str = "300308.SZ",
    max_sources: int = 10,
    mode: str = "execute",
    skip_network: bool = False,
) -> dict[str, Any]:
    """Run a small controlled fetch using the fallback router."""
    result: dict[str, Any] = {
        "ticker": ticker,
        "small_controlled_source_fetch": {
            "network_attempted": not skip_network,
            "mode": mode,
            "selected_sources": [],
            "sources_checked": 0,
            "metadata_ok": 0,
            "text_ok": 0,
            "pdf_url_ok": 0,
            "pdf_text_ok": 0,
            "metadata_only": 0,
            "failed": 0,
            "mock_used": False,
            "fixture_used": False,
            "raw_saved": False,
            "ocr_used": False,
            "rows": [],
            "status": "pending",
        },
    }

    r = result["small_controlled_source_fetch"]

    if skip_network:
        r["status"] = "skipped_network_disabled"
        r["failure_reason"] = "skip_network_enabled"
        return result

    if mode == "dry-run":
        router = route_disclosure_source(ticker, skip_network=True)
        r["status"] = "dry_run"
        r["expected_path"] = router.get("disclosure_source_fallback_router", {}).get("selected_primary_source", "unknown")
        r["max_sources"] = max_sources
        return result

    # Route to best available source
    router = route_disclosure_source(ticker, skip_network=False)
    route_info = router.get("disclosure_source_fallback_router", {})

    # Try CNINFO
    cninfo = _check_cninfo(ticker)
    r["selected_sources"].append("cninfo")
    r["sources_checked"] += 1
    if cninfo.get("has_results"):
        r["metadata_ok"] += 1
        r["rows"].append({
            "source_id": f"cninfo_{ticker}_metadata",
            "source_type": "cninfo_disclosure",
            "fetch_status": "metadata_ok",
            "text_available": False,
            "failure_reason": None,
        })
    elif cninfo.get("reachable"):
        r["metadata_only"] += 1
        r["rows"].append({
            "source_id": f"cninfo_{ticker}_metadata",
            "source_type": "cninfo_disclosure",
            "fetch_status": "metadata_only",
            "text_available": False,
            "failure_reason": "zero_results_from_api",
        })
    else:
        r["failed"] += 1
        r["rows"].append({
            "source_id": f"cninfo_{ticker}_metadata",
            "source_type": "cninfo_disclosure",
            "fetch_status": "failed",
            "failure_reason": "cninfo_unreachable",
        })

    # Try SZSE
    szse = _check_szse(ticker)
    r["selected_sources"].append("szse")
    r["sources_checked"] += 1
    if szse.get("metadata_available"):
        r["metadata_ok"] += 1
        r["pdf_url_ok"] += 1
        r["rows"].append({
            "source_id": f"szse_{ticker}_disclosure",
            "source_type": "szse_disclosure",
            "fetch_status": "metadata_ok",
            "pdf_url_available": True,
            "text_available": False,
            "failure_reason": None,
        })
    elif szse.get("reachable"):
        r["metadata_only"] += 1
        r["rows"].append({
            "source_id": f"szse_{ticker}_disclosure",
            "source_type": "szse_disclosure",
            "fetch_status": "metadata_only",
            "pdf_url_available": False,
            "failure_reason": szse.get("reason", "api_failed"),
        })
    else:
        r["failed"] += 1
        r["rows"].append({
            "source_id": f"szse_{ticker}_disclosure",
            "source_type": "szse_disclosure",
            "fetch_status": "failed",
            "failure_reason": szse.get("reason", "szse_not_reachable"),
        })

    # Try IRM
    irm = _check_irm(ticker)
    r["selected_sources"].append("irm")
    r["sources_checked"] += 1
    if irm.get("qa_available"):
        r["text_ok"] += irm.get("qa_count", 0)
        r["rows"].append({
            "source_id": f"irm_{ticker}_qa",
            "source_type": "irm_interactive_qa",
            "fetch_status": "text_ok",
            "text_available": True,
            "qa_count": irm.get("qa_count", 0),
            "failure_reason": None,
        })
    elif irm.get("reachable"):
        r["metadata_only"] += 1
        r["rows"].append({
            "source_id": f"irm_{ticker}_qa",
            "source_type": "irm_interactive_qa",
            "fetch_status": "metadata_only",
            "text_available": False,
            "failure_reason": irm.get("reason", "qa_not_extractable"),
        })
    else:
        r["failed"] += 1
        r["rows"].append({
            "source_id": f"irm_{ticker}_qa",
            "source_type": "irm_interactive_qa",
            "fetch_status": "failed",
            "failure_reason": irm.get("reason", "irm_not_reachable"),
        })

    r["status"] = "complete"
    r["best_path"] = route_info.get("selected_primary_source", "degraded")

    return result

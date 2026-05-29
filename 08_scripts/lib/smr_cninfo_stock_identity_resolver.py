#!/usr/bin/env python3
"""CNINFO stock identity resolver - Phase 65."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Any

from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES

CNINFO_API = "https://www.cninfo.com.cn/new/hisAnnouncement/query"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.cninfo.com.cn/",
    "Content-Type": "application/x-www-form-urlencoded",
}

STOCK_FORMATS = [
    "300308",
    "0300308",
    "000300308",
    "300308,gfbj0832926",
    "300308,9900022016",
]

PLATE_OPTIONS = ["sz", "szse", "szcy", "cyb", "all"]
COLUMN_OPTIONS = ["szse", "sz", "cyb", "all"]


def _try_query(params: dict, timeout: int = 20) -> dict[str, Any]:
    result = {"params": dict(params), "http_status": None, "total_announcement": 0, "status": "unknown", "failure_reason": None}
    try:
        data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(CNINFO_API, data=data, headers=dict(HEADERS))
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["http_status"] = resp.status
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
            result["total_announcement"] = body.get("totalAnnouncement", 0)
            result["status"] = "ok" if result["total_announcement"] > 0 else "zero_result"
            result["response_keys"] = list(body.keys())[:10]
    except urllib.error.HTTPError as e:
        result["http_status"] = e.code
        result["status"] = "failed"
        result["failure_reason"] = "http_" + str(e.code)
    except Exception as e:
        result["status"] = "failed"
        result["failure_reason"] = str(e)[:120]
    return result


def resolve_cninfo_identity(ticker: str = "300308.SZ", skip_network: bool = False) -> dict[str, Any]:
    code = ticker.split(".")[0] if "." in ticker else ticker
    curated = CURATED_CNINFO_IDENTITIES.get(ticker, {})
    org_id = curated.get("org_id", "")

    result: dict[str, Any] = {
        "ticker": ticker,
        "cninfo_stock_identity_resolver": {
            "network_attempted": not skip_network,
            "curated_identity": {"org_id": org_id, "plate": curated.get("plate"), "column": curated.get("column")} if curated else None,
            "parameter_sets_tested": 0,
            "working_parameter_sets": [],
            "failed_parameter_sets": [],
            "best_parameter_set": None,
            "mock_used": False,
            "fixture_used": False,
        },
    }
    r = result["cninfo_stock_identity_resolver"]

    if skip_network:
        r["status"] = "skipped_network_disabled"
        r["likely_root_cause"] = "skip_network"
        return result

    # Priority 1: org_id from curated identity
    if org_id:
        for stock_fmt in [code, code + "," + org_id]:
            for plate in PLATE_OPTIONS[:3]:
                for col in COLUMN_OPTIONS[:3]:
                    params = {
                        "pageNum": 1, "pageSize": 10, "stock": stock_fmt,
                        "plate": plate, "column": col, "tabName": "fulltext",
                        "searchkey": "", "secid": "", "category": "", "trade": "", "seDate": "",
                    }
                    r["parameter_sets_tested"] += 1
                    trial = _try_query(params)
                    if trial["status"] == "ok":
                        r["working_parameter_sets"].append(trial)
                    else:
                        trial["test_label"] = "orgId_" + stock_fmt + "_" + plate + "_" + col
                        r["failed_parameter_sets"].append(trial)

    # Priority 2: stock-only formats
    for stock_fmt in STOCK_FORMATS:
        for plate in PLATE_OPTIONS[:3]:
            for col in COLUMN_OPTIONS[:3]:
                params = {
                    "pageNum": 1, "pageSize": 10, "stock": stock_fmt,
                    "plate": plate, "column": col, "tabName": "fulltext",
                    "searchkey": "", "secid": "", "category": "", "trade": "", "seDate": "",
                }
                r["parameter_sets_tested"] += 1
                trial = _try_query(params)
                if trial["status"] == "ok":
                    r["working_parameter_sets"].append(trial)
                else:
                    trial["test_label"] = "stock_" + stock_fmt + "_" + plate + "_" + col
                    r["failed_parameter_sets"].append(trial)

    if r["working_parameter_sets"]:
        best = max(r["working_parameter_sets"], key=lambda x: x["total_announcement"])
        r["best_parameter_set"] = best["params"]
        r["best_result_count"] = best["total_announcement"]
    else:
        r["best_parameter_set"] = None
        r["likely_root_cause"] = "stock_orgid_or_column_parameter_unknown"
        r["recommended_next_action"] = "derive_orgid_from_cninfo_search_or_szse_fallback"

    return result

#!/usr/bin/env python3
"""CNINFO announcement query parameter matrix - Phase 65."""

from __future__ import annotations

import json, time, urllib.request, urllib.error, urllib.parse
from typing import Any

from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES

CNINFO_API = "https://www.cninfo.com.cn/new/hisAnnouncement/query"

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
}

HEADERS_PROFILES = {
    "basic": {"User-Agent": BASE_HEADERS["User-Agent"]},
    "ua_referer": {**BASE_HEADERS, "Referer": "https://www.cninfo.com.cn/"},
    "ua_referer_origin": {**BASE_HEADERS, "Referer": "https://www.cninfo.com.cn/", "Origin": "https://www.cninfo.com.cn"},
}

CATEGORIES = {"all": "", "annual": "category_ndbg_szsh", "semi": "category_bndbg_szsh", "quarterly": "category_qtrpt_szsh"}
TIME_RANGES = {"1y": "2024-05-29", "2y": "2023-05-29"}


def run_announcement_query_matrix(ticker: str = "300308.SZ", skip_network: bool = False, max_tests: int = 72) -> dict[str, Any]:
    code = ticker.split(".")[0] if "." in ticker else ticker
    curated = CURATED_CNINFO_IDENTITIES.get(ticker, {})
    org_id = curated.get("org_id", "")
    stock_candidates = [code, code + "," + org_id] if org_id else [code]

    result: dict[str, Any] = {
        "ticker": ticker,
        "cninfo_announcement_query_matrix": {
            "network_attempted": not skip_network,
            "parameter_sets_tested": 0,
            "successful_sets": 0,
            "zero_result_sets": 0,
            "error_sets": 0,
            "best_set": None,
            "trials": [],
            "mock_used": False,
            "fixture_used": False,
        },
    }
    m = result["cninfo_announcement_query_matrix"]

    if skip_network:
        m["status"] = "skipped_network_disabled"
        m["likely_root_cause"] = "skip_network"
        return result

    plates = ["sz", "szse", "all"]
    columns = ["szse", "sz", "all"]
    count = 0

    for stock in stock_candidates:
        for plate in plates:
            for col in columns:
                for cat_name, cat_val in CATEGORIES.items():
                    for header_name, headers in HEADERS_PROFILES.items():
                        if count >= max_tests:
                            break
                        params = {
                            "pageNum": 1, "pageSize": 10, "stock": stock,
                            "plate": plate, "column": col, "tabName": "fulltext",
                            "searchkey": "", "secid": "", "category": cat_val, "trade": "", "seDate": "",
                        }
                        trial = {"params_summary": stock + "|" + plate + "|" + col + "|" + cat_name + "|" + header_name,
                                 "http_status": None, "total_announcement": 0, "status": "unknown", "failure_reason": None}
                        m["parameter_sets_tested"] += 1
                        count += 1
                        try:
                            data = urllib.parse.urlencode(params).encode("utf-8")
                            req = urllib.request.Request(CNINFO_API, data=data, headers=dict(headers))
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                trial["http_status"] = resp.status
                                body = json.loads(resp.read().decode("utf-8", errors="replace"))
                                trial["total_announcement"] = body.get("totalAnnouncement", 0)
                                if trial["total_announcement"] > 0:
                                    trial["status"] = "ok"
                                    m["successful_sets"] += 1
                                    if not m["best_set"] or trial["total_announcement"] > m["best_set"]["total_announcement"]:
                                        m["best_set"] = {"params_summary": trial["params_summary"],
                                                         "total_announcement": trial["total_announcement"],
                                                         "stock": stock, "plate": plate, "column": col}
                                else:
                                    trial["status"] = "zero_result"
                                    m["zero_result_sets"] += 1
                        except urllib.error.HTTPError as e:
                            trial["http_status"] = e.code
                            trial["status"] = "error"
                            trial["failure_reason"] = "http_" + str(e.code)
                            m["error_sets"] += 1
                        except Exception as e:
                            trial["status"] = "error"
                            trial["failure_reason"] = str(e)[:100]
                            m["error_sets"] += 1
                        m["trials"].append(trial)
                        time.sleep(0.05)
                if count >= max_tests:
                    break
            if count >= max_tests:
                break
        if count >= max_tests:
            break

    if m["successful_sets"] == 0:
        failures = {}
        for t in m["trials"]:
            rsn = t.get("failure_reason") or t.get("status", "unknown")
            failures[rsn] = failures.get(rsn, 0) + 1
        m["top_failure_reasons"] = sorted(failures.items(), key=lambda x: -x[1])[:5]
        m["recommended_next_action"] = "use_szse_disclosure_fallback"
    return result
